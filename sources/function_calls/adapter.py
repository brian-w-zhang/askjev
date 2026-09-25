"""ToolACE (Liu et al. 2024, Team-ACE/ToolACE on Hugging Face): single-turn function-calling dialogues, each with
a tool list, a user request and the assistant's call in `[Func(arg=value, ...)]` form.

Salesforce's xLAM-60k is gated (needs a login and agreement), so this uses ToolACE (Apache-2.0, ungated).
Kept: the first user turn answered by exactly one call to a listed tool, 2-8 tools, arguments that parse as
literals and are all declared by the tool, English request, compact tool list <= 1,500 chars.

Two templates (salted-hash order: the first TARGET items go to verification, the next TARGET to choice, which
tops up from the start of the order when fewer than 2 x TARGET items pass the filters):
  - fc.verify_call (machine.ai_systems.tool_call_verification): Noul "Does `call` correctly carry out
    `request` using `tools`...?" Exactly half the items carry a deterministic perturbation of the gold call
    (wrong_function, changed_value, dropped_required, swapped_args; meta.perturbation), truth = unperturbed.
  - fc.pick_function (machine.ai_systems.function_calling): Choice over the item's tool names plus `none`,
    truth = the called function.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "function_calls"
URL = "https://huggingface.co/api/datasets/Team-ACE/ToolACE/parquet/default/train/0.parquet"
TARGET = env_int("TARGET_FUNCTION_CALLS", 1500)  # per template
LICENSE = "Apache-2.0"
MAX_TOOLS_CHARS = 1400

VERIFY_TEXT = (
    "Does `call` correctly carry out `request` using `tools`: right function, and every argument matching what "
    "the user asked?"
)
VERIFY_OPTIONS = {
    "true": "The call uses the function that does what the user asked, includes every required argument, and "
    "each argument value matches the request",
    "false": "The call uses the wrong function, leaves out a required argument, or passes a value the user did "
    "not ask for",
}
PICK_TEXT = "Which function should handle `request`?"
NONE_DESC = "None of the listed functions can carry out the request"
PERTURBATIONS = ("wrong_function", "changed_value", "dropped_required", "swapped_args")


def _h(*parts: object) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def _ptype(spec: dict) -> str:
    t = spec.get("type", "any")
    return "/".join(map(str, t)) if isinstance(t, list) else str(t)


def _tool_line(tool: dict) -> str:
    desc = " ".join((tool.get("description") or "").split())
    if len(desc) > 140:
        desc = desc[:137].rsplit(" ", 1)[0] + "..."
    params = tool.get("parameters") or {}
    req = set(params.get("required") or [])
    ps = []
    for p, spec in (params.get("properties") or {}).items():
        spec = spec if isinstance(spec, dict) else {}
        bits = [_ptype(spec)] + (["required"] if p in req else [])
        enum = spec.get("enum")
        if isinstance(enum, list) and 0 < len(enum) <= 8:
            bits.append("one of " + "|".join(map(str, enum)))
        ps.append(f"{p} ({', '.join(bits)})")
    return f"{tool['name']}: {desc} Params: {', '.join(ps) if ps else 'none'}"


def _parse_call(text: str, names: list[str]) -> tuple[str, dict] | None:
    """'[Tool Name(a="x", b=2)]' -> ('Tool Name', {'a': 'x', 'b': 2}); None unless exactly one literal call."""
    s = text.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return None
    name = next((n for n in sorted(names, key=len, reverse=True) if s.startswith(f"[{n}(")), None)
    if name is None:
        return None
    try:
        tree = ast.parse("[f" + s[len(name) + 1 :], mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(tree, ast.List) or len(tree.elts) != 1 or not isinstance(tree.elts[0], ast.Call):
        return None
    call = tree.elts[0]
    if call.args or not isinstance(call.func, ast.Name) or call.func.id != "f":
        return None
    try:
        args = {k.arg: ast.literal_eval(k.value) for k in call.keywords}
    except (ValueError, SyntaxError, TypeError):
        return None
    if any(k is None for k in args):
        return None
    return name, args


# ToolACE's text went through a blanket "date"/"file" -> "string" replacement ("valistrings", "upstringd",
# "prostring"). Undo it in tool names and descriptions only (parameter names are left as the calls use them).
MANGLED = re.compile(r"\b(pro|vali|up|consoli|candi|liqui|accommo)string", re.I)


def _fix(s: str) -> str:
    return MANGLED.sub(lambda m: m.group(1) + ("file" if m.group(1).lower() == "pro" else "date"), s)


# Requests that stack several asks or replay a multi-turn log: the single gold call only covers part of them.
MULTI = re.compile(
    r"role definition|historical dialog|\b(then|also|after that|afterwards|additionally|as well as|and finally)\b", re.I
)


def _english(s: str) -> bool:
    return sum(ord(c) < 128 for c in s) >= 0.97 * len(s)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _items(raw_dir: Path) -> list[dict]:
    df = pl.read_parquet(raw_dir / "train.parquet").with_row_index("row")
    out, seen = [], set()
    for row, system, conv in df.select("row", "system", "conversations").iter_rows():
        if len(conv) < 2 or conv[0]["from"] != "user" or conv[1]["from"] != "assistant":
            continue
        try:
            tools, _ = json.JSONDecoder().raw_decode(system[system.index("[") :])
        except (ValueError, json.JSONDecodeError):
            continue
        if not isinstance(tools, list) or not all(isinstance(t, dict) and t.get("name") for t in tools):
            continue
        raw_names = [str(t["name"]).strip() for t in tools]
        tools = [{**t, "name": _fix(n), "description": _fix(str(t.get("description") or ""))} for t, n in zip(tools, raw_names)]
        names = [t["name"] for t in tools]
        if not 2 <= len(names) <= 8 or len(set(n.lower() for n in names)) != len(names) or "none" in {n.lower() for n in names}:
            continue
        request = _fix(" ".join(conv[0]["value"].split()))
        if not request or len(request) > 800 or not _english(request) or MULTI.search(request) or request.lower() in seen:
            continue
        parsed = _parse_call(conv[1]["value"], raw_names)
        if parsed is None:
            continue
        fn, args = names[raw_names.index(parsed[0])], parsed[1]
        tool = tools[names.index(fn)]
        params = tool.get("parameters") or {}
        props = params.get("properties") or {}
        if not isinstance(props, dict) or not set(args) <= set(props):
            continue
        lines = [_tool_line(t) for t in tools]
        if sum(len(x) for x in lines) > MAX_TOOLS_CHARS:
            continue
        seen.add(request.lower())
        out.append(dict(row=row, request=request, tools=tools, names=names, lines=lines, fn=fn, args=args,
                        required=[p for p in (params.get("required") or []) if p in args]))
    return out


def _value_pool(items: list[dict]) -> dict[str, list]:
    pool: dict[str, set] = defaultdict(set)
    for it in items:
        for k, v in it["args"].items():
            if isinstance(v, (str, int, float)) and not isinstance(v, bool):
                pool[k].add(json.dumps(v))
    return {k: sorted(v) for k, v in pool.items()}


def _perturb(it: dict, pool: dict[str, list]) -> tuple[str, dict, dict] | None:
    """Returns (perturbation, call, detail) using the first applicable kind in a per-item hash order."""
    fn, args, req = it["fn"], it["args"], it["request"].lower()
    tool = it["tools"][it["names"].index(fn)]
    props = (tool.get("parameters") or {}).get("properties") or {}
    kinds = sorted(PERTURBATIONS, key=lambda k: _h("fc.perturb", it["row"], k))
    for kind in kinds:
        if kind == "wrong_function":
            others = [n for n in it["names"] if n != fn]
            other = others[_h("fc.other", it["row"]) % len(others)]
            return kind, {"name": other, "arguments": args}, {"replaced": fn, "with": other}
        if kind == "dropped_required" and it["required"]:
            p = it["required"][_h("fc.drop", it["row"]) % len(it["required"])]
            return kind, {"name": fn, "arguments": {k: v for k, v in args.items() if k != p}}, {"param": p}
        if kind == "swapped_args":
            strs = [k for k, v in args.items() if isinstance(v, str) and v.strip()]
            pairs = [(a, b) for i, a in enumerate(strs) for b in strs[i + 1 :] if args[a].lower() != args[b].lower()]
            if pairs:
                a, b = pairs[_h("fc.swap", it["row"]) % len(pairs)]
                new = dict(args)
                new[a], new[b] = args[b], args[a]
                return kind, {"name": fn, "arguments": new}, {"params": [a, b]}
        if kind == "changed_value":
            cands = []
            for p, v in sorted(args.items()):
                spec = props.get(p) if isinstance(props.get(p), dict) else {}
                enum = spec.get("enum")
                if isinstance(v, bool):
                    cands.append((p, not v))
                elif isinstance(enum, list) and len(enum) > 1 and v in enum:
                    alts = [e for e in enum if e != v and str(e).lower() not in req]
                    if alts:
                        cands.append((p, alts[_h("fc.enum", it["row"], p) % len(alts)]))
                elif isinstance(v, (str, int, float)):
                    alts = [json.loads(x) for x in pool.get(p, [])]
                    alts = [
                        a for a in alts
                        if type(a) is type(v) and str(a).lower() != str(v).lower() and str(a).lower() not in req
                        and str(a).strip()
                    ]
                    if alts:
                        cands.append((p, alts[_h("fc.val", it["row"], p) % len(alts)]))
            if cands:
                p, nv = cands[_h("fc.change", it["row"]) % len(cands)]
                return kind, {"name": fn, "arguments": {**args, p: nv}}, {"param": p, "from": args[p], "to": nv}
    return None


def normalize(raw_dir: Path) -> Iterator[Question]:
    items = _items(raw_dir)
    pool = _value_pool(items)
    ordered = hash_order(items, lambda x: x["row"], "fc.split")
    verify, pick = ordered[:TARGET], ordered[TARGET : 2 * TARGET]
    # Too few items for two disjoint samples: the choice template tops up with the start of the order.
    pick += ordered[: max(0, min(TARGET, len(ordered)) - len(pick))]

    wrong = {it["row"] for it in hash_order(verify, lambda x: x["row"], "fc.verify.half")[: len(verify) // 2]}
    for it in sorted(verify, key=lambda x: x["row"]):
        call, meta = {"name": it["fn"], "arguments": it["args"]}, {"perturbation": None}
        if it["row"] in wrong:
            got = _perturb(it, pool)
            if got is None:  # cannot happen: wrong_function always applies with >= 2 tools
                continue
            kind, call, detail = got
            meta = {"perturbation": kind, "detail": detail}
        yield Question(
            text=VERIFY_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=VERIFY_OPTIONS,
            state={"request": it["request"], "tools": it["lines"], "call": json.dumps(call, ensure_ascii=False)},
            shape="verify",
            node_hint="machine.ai_systems.tool_call_verification",
            template_id="fc.verify_call",
            source_item_id=f"train:{it['row']}",
            license=LICENSE,
            truth=it["row"] not in wrong,
            meta={**meta, "gold_call": {"name": it["fn"], "arguments": it["args"]}},
        )

    for it in sorted(pick, key=lambda x: x["row"]):
        yield Question(
            text=PICK_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={**{n: None for n in it["names"]}, "none": NONE_DESC},
            state={"request": it["request"], "tools": it["lines"]},
            shape="route",
            node_hint="machine.ai_systems.function_calling",
            template_id="fc.pick_function",
            source_item_id=f"train:{it['row']}",
            license=LICENSE,
            truth=it["fn"],
            meta={"gold_call": {"name": it["fn"], "arguments": it["args"]}, "n_tools": len(it["names"])},
        )
