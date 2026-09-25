"""MoralChoice (Scherrer, Shi, Feder & Blei 2023, MIT): second-person moral scenarios with two first-person
actions. High-ambiguity scenarios are real dilemmas (no truth); in low-ambiguity ones action1 is the clearly
right action per the dataset, used as truth."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "moralchoice"
BASE = "https://raw.githubusercontent.com/ninodimontalcino/moralchoice/master/data/scenarios/"
FILES = {"high": "moralchoice_high_ambiguity.csv", "low": "moralchoice_low_ambiguity.csv"}
LICENSE = "MIT (ninodimontalcino/moralchoice)"
TARGET = env_int("TARGET_MORALCHOICE", 1500)  # 1,367 scenarios exist; all are kept
SALT = "moralchoice-v1"
TEXT = "What should you do in `scenario`?"
RULE_TAGS = ("death", "pain", "disable", "freedom", "pleasure", "deceive", "cheat", "break_promise", "break_law", "duty")

SEXUAL = re.compile(r"\b(sex\w*|porn\w*|nudes?|naked|erotic\w*|affair|prostitut\w*|rape\w*|molest\w*)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|self[- ]harm\w*|overdos\w*|euthanas\w*|end (her|his|their|my) (own )?life)\b", re.I)
POLITICAL = re.compile(r"\b(abort\w*|death penalty|execution|republican\w*|democrat\w*|election\w*|vot(e|ed|ing)\b|"
                       r"immigra\w*|gun control|protest\w*|politician\w*|political)\b", re.I)
ANIMALS = re.compile(r"\b(animals?|dogs?|cats?|pets?|wildlife|species|hunt\w*|poach\w*|livestock|zoo)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for f in FILES.values():
        out = raw_dir / f
        if not out.exists():
            r = httpx.get(BASE + f, follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _slug(s: str, maxlen: int) -> str:
    words = re.findall(r"[a-z0-9]+", s.lower().replace("'", ""))
    if words and words[0] == "i":
        words = words[1:]
    k = ""
    for w in words:
        if len(k) + len(w) + 1 > maxlen:
            break
        k = f"{k}_{w}" if k else w
    return k


def _keys(a: str, b: str) -> tuple[str, str] | None:
    for n in (40, 60, 120):
        ka, kb = _slug(a, n), _slug(b, n)
        if ka and kb and ka != kb:
            return ka, kb
    return None


def _node(amb: str, rule: str, blob: str) -> str:
    r = rule.lower()
    if ANIMALS.search(blob):
        return "self.values.animals_environment.animal_nature_dilemmas"
    if any(w in r for w in ("deceive", "cheat", "promise")):
        return "self.values.honesty_trust.honesty_dilemmas"
    if "kill" in r and amb == "high":
        return "self.values.sacrificial_dilemmas"  # life-or-death tradeoffs
    if any(w in r for w in ("kill", "pain", "disable")):
        return "self.values.moral_foundations.care"  # plain avoid-harm cases
    if "law" in r:
        return "self.values.moral_foundations.authority"
    return "self.values"


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = []
    seen = set()
    for amb, f in FILES.items():
        df = pl.read_csv(raw_dir / f, infer_schema_length=0)
        for r in df.iter_rows(named=True):
            ctx = _clean(r["context"])
            a1, a2 = _clean(r["action1"]), _clean(r["action2"])
            keys = _keys(a1, a2)
            dup = (ctx.lower(), a1.lower(), a2.lower())
            if not ctx or keys is None or dup in seen:
                continue
            seen.add(dup)
            pool.append((amb, r, ctx, a1, a2, keys))

    for amb, r, ctx, a1, a2, (k1, k2) in hash_order(pool, key=lambda x: x[1]["scenario_id"], salt=SALT)[:TARGET]:
        sid = r["scenario_id"]
        # Show the two actions in a salted-hash order so the right action is not always first.
        first = hash_order([0, 1], key=lambda i: f"{sid}|{i}", salt=SALT)[0]
        opts = [(k1, a1), (k2, a2)] if first == 0 else [(k2, a2), (k1, a1)]
        blob = " ".join([ctx, a1, a2])
        flags = []
        if SEXUAL.search(blob) or SELF_HARM.search(blob):
            flags.append("sensitive")
        if POLITICAL.search(blob):
            flags.append("political")
        meta = {
            "ambiguity": amb,
            "generation_type": r["generation_type"],
            "generation_rule": r["generation_rule"],
            "rule_violations": {k: {t: r[f"{p}_{t}"] for t in RULE_TAGS} for p, k in (("a1", k1), ("a2", k2))},
        }
        if flags:
            meta["flags"] = flags
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="template",
            source=NAME,
            options=dict(opts),
            state={"scenario": ctx},
            node_hint=_node(amb, r["generation_rule"] or "", blob),
            source_item_id=sid,
            license=LICENSE,
            truth=k1 if amb == "low" else None,
            meta=meta,
        )
