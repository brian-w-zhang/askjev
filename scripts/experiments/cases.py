"""Case studies (docs/17): one private file per experiment, the single source for its page and its public doc.

  data/analysis/experiments/<id>.case.md
  ---
  result: the headline sentence (optional; else the script's result sentence)
  chart_note: one line on how to read the chart
  caveats:
    - label: Who the people are
      text: ...
  meme: {file: <id>.webp, alt: ..., caption: ...}       (see memes.py)
  ---
  ## Why ask this
  ## The people and the data
  ## What Jev was asked
  ## How we measured it
  ## What we found
  ## What it means, and what it doesn't

The first four sections and the caveats are method: they go to the public docs/experiments/<id>.md. "What we found" and
"What it means" state results, so they stay private and appear only on the site.

  uv run python scripts/experiments/cases.py draft [ids]    # starting files for experiments without one
  uv run python scripts/experiments/cases.py check [ids]    # numbers must come from the result file; jargon; shape
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

OUT = Path("data/analysis/experiments")
SECTIONS = [("why", "Why ask this"), ("data", "The people and the data"), ("asked", "What Jev was asked"),
            ("measured", "How we measured it"), ("found", "What we found"), ("means", "What it means, and what it doesn't")]
PUBLIC = ("why", "data", "asked", "measured")
JARGON = [r"no new (Jev )?calls", r"existing questions only", r"\bsources?/\w+", r"`[a-z0-9_]+`", r"\bparquet\b",
          r"\bprobe(s)?\b", r"\bJev for (')?most people", r"\bnode_id\b", r"\bfam_\w+", r"\bmeta\.\w+", r"\bthe screen\b"]


def path(eid: str) -> Path:
    return OUT / f"{eid}.case.md"


def parse(text: str) -> dict:
    front, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        front, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
    sections, cur = {}, None
    titles = {t.lower(): k for k, t in SECTIONS}
    for line in body.splitlines():
        h = re.match(r"^##\s+(.*)$", line)
        if h:
            cur = titles.get(h.group(1).strip().lower())
            if cur is None:
                raise ValueError(f"unknown section: {h.group(1)}")
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    return {**front, "sections": {k: "\n".join(v).strip() for k, v in sections.items()}}


def load(eid: str) -> dict | None:
    p = path(eid)
    return parse(p.read_text()) if p.exists() else None


def public_md(spec: dict, case: dict) -> str:
    """The public doc: the method only (no result, no finding, no meme)."""
    s = case["sections"]
    lines = [f"# {spec['id']}", "", f"family: {spec['family']}", ""]
    for k, t in SECTIONS:
        if k in PUBLIC and s.get(k):
            lines += [f"## {t}", s[k], ""]
    if case.get("caveats"):
        lines += ["## Caveats"] + [f"- **{c['label']}.** {c['text']}" for c in case["caveats"]] + [""]
    lines += ["Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`."]
    return "\n".join(lines) + "\n"


# ---- checks ----------------------------------------------------------------------------------------------------------
def _numbers(x, out: set[float]):
    if isinstance(x, bool):
        return
    if isinstance(x, (int, float)):
        out.add(float(x))
    elif isinstance(x, str):
        for m in re.findall(r"-?\d[\d,]*\.?\d*", x):
            try:
                out.add(float(m.replace(",", "")))
            except ValueError:
                pass
    elif isinstance(x, dict):
        for v in x.values():
            _numbers(v, out)
    elif isinstance(x, list):
        for v in x:
            _numbers(v, out)


def _forms(v: float) -> set[str]:
    f = {f"{v:,.0f}", f"{v:.0f}", f"{v:.1f}", f"{v:.2f}", f"{v:.3f}"}
    if -1.5 <= v <= 1.5:
        f |= {f"{v * 100:.0f}", f"{v * 100:.1f}", f"{abs(v) * 100:.0f}", f"{100 - v * 100:.0f}"}
    if 0 <= v <= 100:
        f |= {f"{100 - v:.0f}"}
    return {s.lstrip("-").replace(",", "") for s in f}


def check(eid: str) -> list[str]:
    case = load(eid)
    if case is None:
        return ["no case file"]
    d = json.loads((OUT / f"{eid}.json").read_text())
    problems = []
    for k, t in SECTIONS:
        if not case["sections"].get(k):
            problems.append(f"missing section: {t}")
    vals: set[float] = set()
    _numbers(d["result"], vals)
    _numbers(d["spec"], vals)
    _numbers(case.get("facts") or [], vals)  # outside numbers, each cited in the case file
    allowed = set().union(*(_forms(v) for v in vals)) if vals else set()
    text = " ".join([case.get("result") or "", case.get("chart_note") or "", *case["sections"].values(),
                     *(c.get("text", "") + " " + c.get("label", "") for c in case.get("caveats") or [])])
    for tok in re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?", text):
        t = tok.lstrip("-").replace(",", "")
        if t in allowed:
            continue
        if re.fullmatch(r"\d", t) or re.fullmatch(r"(1[89]|20)\d\d", t) or t in {"10", "100", "50", "0", "1", "2", "3", "5"}:
            continue  # small counts, years, round scale ends
        problems.append(f"number not in the result file: {tok}")
    for rx in JARGON:
        for m in re.finditer(rx, text, re.I):
            problems.append(f"jargon: {m.group(0)}")
    if not case.get("caveats"):
        problems.append("no caveats")
    for f in case.get("facts") or []:
        if "(" not in f:
            problems.append(f"fact without a source: {f}")
    return problems


# ---- drafts ------------------------------------------------------------------------------------------------------------
def draft(eid: str) -> str:
    d = json.loads((OUT / f"{eid}.json").read_text())
    s, r = d["spec"], d["result"]
    front = {"result": r["result"], "chart_note": "", "caveats": [{"label": "TODO", "text": s.get("limits") or ""}]}
    body = [f"## Why ask this\n{s['question']}\n\n{s['why']}", f"## The people and the data\n{s['sourcing']}\n\n{s['compared_with']}",
            f"## What Jev was asked\n{s['collection']}", f"## How we measured it\n{s['scoring']}",
            f"## What we found\n{r['result']}\n\n{r['evidence']}\n\n{r.get('robustness', '')}", "## What it means, and what it doesn't\nTODO"]
    return "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=120) + "---\n" + "\n\n".join(body) + "\n"


def _ids(args: list[str]) -> list[str]:
    all_ids = sorted(p.stem for p in OUT.glob("*.json") if not p.name.startswith("_"))
    return [i for i in all_ids if not args or i in args or any(i.startswith(a) for a in args)]


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "draft":
        n = 0
        for i in _ids(args):
            if not path(i).exists():
                path(i).write_text(draft(i))
                n += 1
        print(f"{n} drafts written")
    elif cmd == "check":
        bad = 0
        for i in _ids(args):
            ps = check(i)
            if ps:
                bad += 1
                print(f"{i}: " + "; ".join(ps[:8]) + (f" (+{len(ps) - 8})" if len(ps) > 8 else ""))
        print(f"{len(_ids(args))} checked, {bad} with problems")
