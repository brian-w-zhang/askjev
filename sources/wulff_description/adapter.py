"""Description-based risky choice problems from the Wulff, Mergenthaler-Canseco & Hertwig (2018) meta-analysis of
the description-experience gap, as transcribed in Psych-101 (Binz et al. 2025, Apache-2.0). Each participant chose
between two fully described lotteries (points added to a bonus); choices are pooled per problem across
participants and studies into a two-way Choice with the choice shares as the human distribution."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "wulff_description"
URL = "https://huggingface.co/datasets/marcelbinz/Psych-101/resolve/main/prompts_training.jsonl"
EXPERIMENT = "wulff2018description/exp1.csv"
LICENSE = ("Psych-101 (marcelbinz/Psych-101, Apache-2.0), transcribing Wulff, Mergenthaler-Canseco & Hertwig 2018, "
           "Psychological Bulletin 144:140-176 (description condition)")
TARGET = env_int("TARGET_WULFF_DESCRIPTION", 5000)
MIN_N = 15
SALT = "wulff_description-v1"
TEXT = ("Imagine you pick one of these two lotteries, and one random draw from it is added to a real bonus (negative "
        "points are taken off). Which do you pick: `lottery_a` or `lottery_b`?")
NODE = "self.personality.risk_decision_style"
PAT = re.compile(r"Lottery (\w) offers (.+?)\.\nLottery (\w) offers (.+?)\.\nYou press <<(\w)>>")
OUTCOME = re.compile(r"(-?[\d.]+) points with ([\d.]+)% probability")


def fetch(raw_dir: Path) -> None:
    """Streams the 860 MB Psych-101 file once and keeps only this experiment's transcripts."""
    out = raw_dir / "wulff2018description.jsonl"
    if out.exists():
        return
    tmp = out.with_suffix(".part")
    with httpx.stream("GET", URL, follow_redirects=True, timeout=None) as r, open(tmp, "w", encoding="utf-8") as fh:
        r.raise_for_status()
        for line in r.iter_lines():
            if EXPERIMENT in line and json.loads(line).get("experiment") == EXPERIMENT:
                fh.write(line + "\n")
    tmp.rename(out)


def _parse(s: str) -> tuple[tuple[float, float], ...] | None:
    outs = [(float(x), float(p)) for x, p in OUTCOME.findall(s)]
    if not outs or abs(sum(p for _, p in outs) - 100) > 0.6:
        return None
    merged = defaultdict(float)
    for x, p in outs:
        if p > 0:
            merged[x] += p
    return tuple(sorted(merged.items(), key=lambda kv: (-kv[1], kv[0])))


def _num(x: float) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def _describe(outs: tuple[tuple[float, float], ...]) -> str:
    def pts(x: float) -> str:
        return f"{_num(x)} point" + ("" if abs(x) == 1 else "s")

    if len(outs) == 1:
        return f"{pts(outs[0][0])} for sure"
    parts = []
    for x, p in outs:
        pct = _num(p)
        art = "an" if pct.startswith("8") or re.match(r"1[18](\.|$)", pct) else "a"
        parts.append(f"{pts(x)} with {art} {pct}% chance")
    return ", ".join(parts[:-1]) + ", or " + parts[-1]


def normalize(raw_dir: Path) -> Iterator[Question]:
    tally: dict[tuple, dict] = {}
    for line in open(raw_dir / "wulff2018description.jsonl", encoding="utf-8"):
        d = json.loads(line)
        for k1, s1, k2, s2, pressed in PAT.findall(d["text"]):
            g1, g2 = _parse(s1), _parse(s2)
            if not g1 or not g2 or g1 == g2:
                continue
            a, b = sorted([g1, g2])  # canonical order, independent of screen position
            chose = g1 if pressed == k1 else g2 if pressed == k2 else None
            if chose is None:
                continue
            t = tally.setdefault((a, b), {"a": 0, "b": 0, "participants": set()})
            t["a" if chose == a else "b"] += 1
            t["participants"].add(d.get("participant"))
    pool = [(k, v) for k, v in tally.items() if v["a"] + v["b"] >= MIN_N]
    for (a, b), v in hash_order(pool, key=lambda kv: repr(kv[0]), salt=SALT)[:TARGET]:
        n = v["a"] + v["b"]
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="personality",
            origin="template",
            source=NAME,
            options={"lottery_a": None, "lottery_b": None},
            state={"lottery_a": _describe(a), "lottery_b": _describe(b)},
            node_hint=NODE,
            source_item_id=f"{_describe(a)} | {_describe(b)}",
            license=LICENSE,
            human=[HumanDist(population="Participants in description-based risky choice studies (Wulff et al. 2018 "
                                        "meta-analysis)", distribution={"lottery_a": round(v["a"] / n, 4),
                                                                        "lottery_b": round(v["b"] / n, 4)},
                             n=n, source="Psych-101 wulff2018description/exp1.csv, pooled choices")],
            template_id=f"{NAME}.lottery",
            meta={"choices": n, "participants": len(v["participants"])},
        )
