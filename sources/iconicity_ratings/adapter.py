"""Iconicity ratings for 14,000+ English words (Winter, Lupyan, Perry, Dingemanse & Perlman 2023).

'How much does the word "X" sound like what it means?' as a 7-level Score. The authors publish the individual
ratings after their exclusions (iconicity_ratings_raw.csv, 161k ratings; their per-word means are exactly the means
of these rows), so each question carries the raters' real 1-7 answer distribution, not a fitted one. "I don't know
the word" (NA) answers are dropped, as in the published means.

Word pool: single lowercase words most raters knew (prop_known >= 0.9) that are common (SUBTLEX-US count from
Brysbaert et al. 2014). Iconic words are rare, so the sample is stratified by mean rating into four bands with equal
quotas (a band short of words passes its remainder on), each band in salted-hash order.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

_spec = importlib.util.spec_from_file_location(
    "sources.concreteness", Path(__file__).parents[1] / "concreteness" / "adapter.py")
_c = importlib.util.module_from_spec(_spec)
sys.modules["sources.concreteness"] = _c
_spec.loader.exec_module(_c)

NAME = "iconicity_ratings"
BASE = "https://raw.githubusercontent.com/bodowinter/iconicity_ratings/main/ratings/"  # mirrored on OSF qvw6u
FILES = ["iconicity_ratings_cleaned.csv", "iconicity_ratings_raw.csv"]
LICENSE = "Research use; public data (Winter, Lupyan, Perry, Dingemanse & Perlman 2023, Behavior Research Methods, CC BY 4.0 article; OSF qvw6u)"
SALT = "iconicity_ratings-20260926"
TARGET = env_int("TARGET_ICONICITY_RATINGS", 2500)
MIN_KNOWN = 0.9
MIN_SUBTLEX = 50
BANDS = [(1.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 7.01)]
ANCHORS = {"buzz", "hiss", "boom"}  # named in the top level, so never asked

TEXT = 'How much does the word "{w}" sound like what it means?'
HUMAN_TEXT = 'How much does the word "{w}" sound like what it means, to most people?'
LEVELS = [
    'Any other sound would do as well: nothing in how it sounds connects to what it means',
    'You can find a link between its sound and its meaning only by straining for one',
    'One sound in it hints at its meaning, but you would notice only if someone pointed it out',
    'Its sound suits its meaning, the way a short word suits something small, without imitating it',
    'Its sound clearly fits its meaning, like a rough-sounding word for something rough',
    'Part of it imitates what it means, such as a noise, a motion or a texture',
    'Saying it imitates what it means, like "buzz", "hiss" or "boom"',
]


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if not out.exists():
            r = httpx.get(BASE + f, follow_redirects=True, timeout=300)
            r.raise_for_status()
            out.write_bytes(r.content)
    _c.fetch_brysbaert(raw_dir)


def normalize(raw_dir: Path) -> Iterator[Question]:
    brys = _c.read_brysbaert(raw_dir / _c.FILE)
    with open(raw_dir / FILES[0], newline="", encoding="utf-8") as fh:
        words = {r["word"]: r for r in csv.DictReader(fh)}
    ratings: dict[str, list[int]] = defaultdict(list)
    with open(raw_dir / FILES[1], newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["key"] in {"1", "2", "3", "4", "5", "6", "7"}:
                ratings[r["word"]].append(int(r["key"]))
    pool = []
    for w, r in words.items():
        b = brys.get(w)
        if (b is None or b["bigram"] or not re.fullmatch(r"[a-z]{3,}", w) or w in ANCHORS or _c.SLURS.match(w)
                or b["subtlex"] < MIN_SUBTLEX or float(r["prop_known"]) < MIN_KNOWN):
            continue
        if len(ratings[w]) != int(r["n_ratings"]):  # raw rows must reproduce the published count
            continue
        pool.append(w)
    bands = [hash_order([w for w in pool if lo <= float(words[w]["rating"]) < hi], lambda w: w, SALT)
             for lo, hi in BANDS]
    picked: list[str] = []
    quota = TARGET // len(bands)
    for i, band in enumerate(sorted(range(len(bands)), key=lambda i: len(bands[i]))):  # smallest band first
        take = bands[band][:quota]
        picked += take
        left = len(bands) - i - 1
        if left:
            quota = (TARGET - len(picked)) // left
    print(f"{NAME}: {len(words)} words, {len(pool)} common known words, bands {[len(b) for b in bands]}, "
          f"{len(picked)} picked")
    for w in sorted(picked):
        r = words[w]
        ks = ratings[w]
        cnt = Counter(ks)
        yield Question(
            text=TEXT.format(w=w),
            primitive="score",
            hemisphere="world",
            kind="perception",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            node_hint="world.society.languages.word",
            human_text=HUMAN_TEXT.format(w=w),
            source_item_id=w,
            license=LICENSE,
            template_id=f"{NAME}.iconicity",
            human=[HumanDist(
                population="Winter et al. 2023 raters (US English speakers, Prolific/MTurk)",
                distribution={str(k - 1): cnt[k] / len(ks) for k in range(1, 8)},
                n=len(ks),
                source="Winter et al. 2023 iconicity ratings, individual ratings after exclusions",
            )],
            meta={
                **({"flags": fl} if (fl := _c.word_flags(w)) else {}),
                "word": w,
                "mean_1_7": round(float(r["rating"]), 3),
                "sd": round(float(r["rating_sd"]), 3),
                "prop_known": float(r["prop_known"]),
                "subtlex_count": brys[w]["subtlex"],
                "scale": "1 (not iconic at all) to 7 (very iconic); level i = rating i+1",
            },
        )
