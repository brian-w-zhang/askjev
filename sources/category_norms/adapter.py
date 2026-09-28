"""Which member of a category comes to mind first, and how typical is each member? (docs/15 E43; research pass 2.)

Human data: Banks, Wingfield & Connell 2023, "Category production norms for 117 concrete and abstract categories"
(Behavior Research Methods 55:1292-1313; OSF jgcu6, CC BY 4.0). Twenty Lancaster University students per category
named as many members as they could in 60 seconds; the first member each named gives the first-to-mind
distribution. A separate sample of UK adults (Prolific, at least 12 per item) rated "How good an example of this
category is X?" from 1 (very poor example) to 5 (very good example); only item means are published.

Two sets: first-to-mind for 114 categories (a Choice over the members people named first, plus "something else"),
and typicality for 350 members sampled evenly over the range of mean ratings. Religion, political systems and
religious buildings are left out.
"""

from __future__ import annotations

import csv
import random
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "category_norms"
NODE = "world.society.languages.word.category_members"
LICENSE = "CC BY 4.0 (Banks, Wingfield & Connell 2023, category production norms, OSF jgcu6)"
URL = "https://osf.io/download/nz38s/"  # Referential version_Item level data.csv
FILE = "item_level.csv"
SKIP = {"religion", "political system", "religious building"}
LEVELS = ["A very poor example: most people wouldn't think of it as one at all",
          "A poor example: it belongs, but only at the edge of the category",
          "A middling example: clearly in the category but not what people picture",
          "A good example: one of the first few people would think of",
          "A very good example: the textbook case people picture first"]
N_TYPICALITY = 350
MAX_FIRST = 7


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / FILE).exists():
        urllib.request.urlretrieve(URL, raw_dir / FILE)


def _f(x: str) -> float | None:
    return None if x in ("", "NA") else float(x)


def _key(s: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in s.lower()).strip("_")[:60]


def _an(cat: str) -> str:
    return ("an " if cat[0] in "aeiou" else "a ") + cat


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = list(csv.DictReader(open(raw_dir / FILE, encoding="utf-8-sig")))
    by = defaultdict(list)
    for r in rows:
        if r["category"] not in SKIP:
            by[r["category"]].append(r)
    for cat, ms in sorted(by.items()):
        firsts = sorted(((m["category.member"], _f(m["first.rank.freq"]) or 0) for m in ms), key=lambda x: (-x[1], x[0]))
        firsts = [(m, c) for m, c in firsts if c > 0]
        total = 20  # participants per category (Banks et al. 2023); a few skipped a category, the rest is "something else"
        shown = firsts[:MAX_FIRST]
        if len(shown) < 2:
            continue
        opts = {_key(m): m for m, _ in shown}
        opts["something_else"] = "Something else"
        dist = {_key(m): c / total for m, c in shown}
        dist["something_else"] = max(0.0, 1 - sum(dist.values()))
        yield Question(
            text=f"Asked to name {_an(cat)}, which one comes to mind first?", primitive="choice", hemisphere="world",
            kind="perception", origin="dataset", source=NAME, options=opts, node_hint=NODE, license=LICENSE,
            source_item_id=f"first:{cat}",
            human=[HumanDist(population="Lancaster University students (Banks et al. 2023)", distribution=dist, n=total,
                             source="first.rank.freq: members named first in a 60-second category production task")],
            meta={"experiment": "category_first", "set": "first", "category": cat, "domain": ms[0]["domain"].lower()})
    typ = sorted(((r["category"], r["category.member"], _f(r["typicality"])) for ms in by.values() for r in ms
                  if _f(r["typicality"]) is not None), key=lambda x: (x[2], x[0], x[1]))
    k = len(typ) / N_TYPICALITY
    rng = random.Random(2023)
    picks = {typ[min(len(typ) - 1, int(i * k + rng.random() * k))] for i in range(N_TYPICALITY)}
    for cat, member, mean in sorted(picks):
        yield Question(
            text=f"How good an example of {_an(cat)} is {member}?", primitive="score", hemisphere="world",
            kind="perception", origin="dataset", source=NAME, options=LEVELS, node_hint=NODE, license=LICENSE,
            source_item_id=f"typicality:{cat}:{member}",
            meta={"experiment": "category_typicality", "set": "typicality", "category": cat, "member": member,
                  "human_mean": mean, "scale": "1 very poor example - 5 very good example",
                  "domain": by[cat][0]["domain"].lower()})
