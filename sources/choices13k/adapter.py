"""choices13k (Peterson, Bourgin, Agrawal, Reichman & Griffiths 2021, Science): human choice rates on 13,006
two-gamble risky choice problems in the CPC15/CPC18 format, run on MTurk with a real bonus. Asked as a two-way
Choice between the gambles, with the problem's gamble-B choice rate as the human distribution. Only problems
answered without outcome feedback are used, since the question is a one-shot choice from description."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "choices13k"
BASE = "https://raw.githubusercontent.com/jcpeterson/choices13k/master/"
FILES = ("c13k_selections.csv", "c13k_problems.json")
LICENSE = ("choices13k (Peterson et al. 2021, Science 372:1209), public GitHub release with no license file; "
           "research use with citation")
TARGET = env_int("TARGET_CHOICES13K", 5000)
SALT = "choices13k-v1"
TEXT = ("Imagine you must play one of these two gambles once, for real money (wins are paid to you, losses come out "
        "of your pocket). Which do you choose: `gamble_a` or `gamble_b`?")
NODE = "self.personality.risk_decision_style"


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        p = raw_dir / f
        if not p.exists():
            r = httpx.get(BASE + f, follow_redirects=True, timeout=300)
            r.raise_for_status()
            p.write_bytes(r.content)


def _money(x: float) -> str:
    v = round(x, 2)
    s = f"{abs(v):,.2f}".rstrip("0").rstrip(".")
    return f"-${s}" if v < 0 else f"${s}"


def _pct(p: float) -> str:
    v = round(p * 100, 4)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return f"{s}%"


def _article(pct: str) -> str:
    return "an" if pct.startswith(("8", "11%", "11.", "18")) else "a"


def _describe(outcomes: list[list[float]], ambiguous: bool = False) -> str:
    merged = defaultdict(float)
    for p, x in outcomes:
        if p > 1e-9:
            merged[round(x, 2)] += p
    if len(merged) == 1:
        return f"{_money(next(iter(merged)))} for sure"
    items = sorted(merged.items(), key=lambda kv: -kv[1]) if not ambiguous else sorted(merged.items())
    if ambiguous:
        vals = [_money(x) for x, _ in items]
        return f"one of these amounts: {', '.join(vals[:-1])} or {vals[-1]}, with probabilities you are not told"
    parts = [f"{_money(x)} with {_article(_pct(p))} {_pct(p)} chance" for x, p in items]
    return ", ".join(parts[:-1]) + ", or " + parts[-1]


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = list(csv.DictReader(open(raw_dir / "c13k_selections.csv", encoding="utf-8")))
    probs = json.loads((raw_dir / "c13k_problems.json").read_text())
    merged: dict[tuple, dict] = {}
    for i, r in enumerate(rows):
        if r["Feedback"] != "False":
            continue
        pr = probs[str(i)]
        amb = r["Amb"] == "True"
        a = _describe(pr["A"])
        b = _describe(pr["B"], ambiguous=amb)
        if a == b:
            continue
        n = int(r["n"])
        key = (a, b)
        m = merged.setdefault(key, {"a": a, "b": b, "n": 0, "bsum": 0.0, "rows": [], "problems": [], "amb": amb,
                                    "corr": int(r["Corr"]), "lotnum": int(r["LotNumB"])})
        m["n"] += n
        m["bsum"] += float(r["bRate"]) * n
        m["rows"].append(i)
        m["problems"].append(int(r["Problem"]))
    pool = list(merged.values())
    for m in hash_order(pool, key=lambda m: m["rows"][0], salt=SALT)[:TARGET]:
        brate = m["bsum"] / m["n"]
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="personality",
            origin="template",
            source=NAME,
            options={"gamble_a": None, "gamble_b": None},
            state={"gamble_a": m["a"], "gamble_b": m["b"]},
            node_hint=NODE,
            source_item_id=f"row{m['rows'][0]}",
            license=LICENSE,
            human=[HumanDist(population="US MTurk workers (choices13k, no feedback)",
                             distribution={"gamble_a": round(1 - brate, 4), "gamble_b": round(brate, 4)},
                             n=m["n"], source="Peterson et al. 2021 c13k_selections.csv bRate")],
            template_id=f"{NAME}.gamble",
            meta={"rows": m["rows"], "problems": m["problems"], "ambiguous_b": m["amb"], "lot_outcomes_b": m["lotnum"],
                  "b_rate": round(brate, 4)},
        )
