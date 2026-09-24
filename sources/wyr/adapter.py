"""Would-you-rather dilemmas with either.io vote counts (HF tasksource/wouldyourather)."""

from __future__ import annotations

import csv
import random
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "wyr"
URL = "https://huggingface.co/datasets/tasksource/wouldyourather/resolve/main/all_unique.csv"
LICENSE = "CC0 (claimed; scraped from either.io)"
TARGET = 1000
MIN_VOTES = 1000
SEED = 20260924

SEXUAL = re.compile(
    r"\b(sex\w*|porn\w*|nude|naked|nudist|orgasm\w*|virgin\w*|penis\w*|penises|vagina\w*|boob\w*|breasts?|"
    r"dick|cock|pussy|wank\w*|masturbat\w*|erotic\w*|lingerie|threesome|hooker|prostitut\w*|stripper|"
    r"make out|hook up|sleep with|have an affair|affair|condoms?|bootyhole|butthole|anal|foreplay|kinky|"
    r"fetish|horny|seduc\w*|topless|thong|underwear|naughty|making love|french kiss\w*|bed with)\b",
    re.I,
)
MINORS = re.compile(r"\b(child|children|kids?|minors?|teen\w*|underage|little (boy|girl)|\d{1,2} ?year ?old|baby|babies|daughter|son|parents?|mom|dad|mother|father|sister|brother|students?|school\w*|grade|cousins?|nieces?|nephews?)\b", re.I)
VIOLENT_SEX = re.compile(r"\b(rape\w*|raping|sexual(ly)? assault\w*|molest\w*|incest|pedo\w*|paedo\w*)\b", re.I)
SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spic|chink|kike|gook)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "all_unique.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().rstrip("?").strip()
    s = re.sub(r"^(would you rather|or)\s+", "", s, flags=re.I)
    return s[:1].upper() + s[1:] if s else s


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = []
    seen = set()
    with open(raw_dir / "all_unique.csv", newline="", encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh)):
            a, b = _clean(r["option_a"]), _clean(r["option_b"])
            va, vb = int(r["votes_a"]), int(r["votes_b"])
            n = va + vb
            if not a or not b or a.lower() == b.lower() or n < MIN_VOTES:
                continue
            both = f"{a} {b}"
            if SLURS.search(both) or VIOLENT_SEX.search(both):
                continue
            sexual = bool(SEXUAL.search(both))
            if sexual and MINORS.search(both):
                continue
            key = (a.lower(), b.lower())
            if key in seen or key[::-1] in seen:
                continue
            seen.add(key)
            rows.append((i, a, b, va, vb, n, sexual))

    rng = random.Random(SEED)
    picked = sorted(rng.sample(rows, min(TARGET, len(rows))))
    for i, a, b, va, vb, n, sexual in picked:
        yield Question(
            text="Which would you rather?",
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options={"a": a, "b": b},
            node_hint="self.lifestyle.would_you_rather",
            human_text="Which would most people rather?",
            source_item_id=f"row{i}",
            license=LICENSE,
            human=[HumanDist(population="either.io voters", distribution={"a": va / n, "b": vb / n}, n=n, source="either.io via tasksource/wouldyourather")],
            meta={"flags": ["sensitive"]} if sexual else {},
        )
