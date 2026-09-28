"""Who has a mind? (docs/15 E20): Gray, Gray & Wegner's (2007, Science) character comparisons, re-run on Jev.

Human data: Weisman's direct replication of Gray et al. 2007 (github.com/kgweisman/ggw-rep, run of 2015-03-09; US
MTurk adults). The same 13 characters with the original descriptions (a frog, a dog, a chimpanzee, a fetus, a
5-month-old, a 5-year-old, two adults, a man in a persistent vegetative state, a woman who recently died, God, the
sociable robot Kismet, and "you"), compared in all 78 pairs on one capacity per participant: two for Experience
(feeling afraid, feeling hungry) and two for Agency (telling right from wrong, self-control), on the study's
5-point scale. "You" is the respondent, so for Jev it is Jev.
The repository states no license; the data were posted publicly by the author with the study. Used here for private,
non-commercial research and not redistributed.
"""

from __future__ import annotations

import re
import urllib.request
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import HumanDist, Question

NAME = "mind_perception"
NODE = "self.mind.consciousness_ai.mind_perception"
LICENSE = "No license stated (github.com/kgweisman/ggw-rep, data posted publicly with the replication); private research use"
BASE = "https://raw.githubusercontent.com/kgweisman/ggw-rep/master/"
FILES = {"ggw_rep_data.csv": "data/run-01_2015-03-09_data_anonymized.csv", "characters.js": "experiment/scripts/characters.js"}
CAPACITIES = {"Fear": ("feeling afraid or fearful", "experience"), "Hunger": ("feeling hungry", "experience"),
              "Morality": ("telling right from wrong and trying to do the right thing", "agency"),
              "SelfControl": ("exercising self-restraint over desires, emotions, or impulses", "agency")}
YOU = "You yourself: the one answering this question."


def fetch(raw_dir: Path) -> None:
    for f, p in FILES.items():
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(BASE + p, raw_dir / f)


def characters(raw_dir: Path) -> list[tuple[str, str, str]]:
    """(key, short title, description) in the study's order."""
    js = (raw_dir / "characters.js").read_text()
    out = re.findall(r'addCharacter\("([^"]+)", "([^"]+)", "([^"]+)"\);', js)
    return [(k, t, YOU if k == "you" else d) for k, t, d in out]


def _short(title: str) -> str:
    return "you" if title == "You" else title.split(",")[0]


def normalize(raw_dir: Path) -> Iterator[Question]:
    chars = characters(raw_dir)
    order = {k: i for i, (k, _, _) in enumerate(chars)}
    info = {k: (t, d) for k, t, d in chars}
    d = pl.read_csv(raw_dir / "ggw_rep_data.csv", infer_schema_length=0)
    counts: dict[tuple, Counter] = {}
    for r in d.iter_rows(named=True):
        l, rt, v = r["leftCharacter"], r["rightCharacter"], int(r["responseNum"])  # -2 = much more the left one
        a, b = (l, rt) if order[l] < order[rt] else (rt, l)
        lev = 2 + v if l == a else 2 - v  # 0 = much more a ... 4 = much more b
        counts.setdefault((r["condition"], a, b), Counter())[str(lev)] += 1
    for cond, (wording, dim) in CAPACITIES.items():
        for (a, _, _), (b, _, _) in combinations(chars, 2):
            c = counts.get((cond, a, b), Counter())
            n = sum(c.values())
            A, B = _short(info[a][0]), _short(info[b][0])
            cap = lambda s: s[0].upper() + s[1:]  # noqa: E731
            levels = [f"{cap(A)}: much more capable", f"{cap(A)}: slightly more capable", "Both equally capable",
                      f"{cap(B)}: slightly more capable", f"{cap(B)}: much more capable"]
            text = (f"Which character is more capable of {wording}?\n"
                    f"{cap(A)}: {info[a][1]}\n{cap(B)}: {info[b][1]}")
            yield Question(
                text=text, primitive="score", hemisphere="self", kind="perception", origin="dataset", source=NAME,
                options=levels, node_hint=NODE, license=LICENSE, source_item_id=f"{cond}:{a}:{b}",
                human=[HumanDist(population="US MTurk adults (Weisman's replication of Gray et al. 2007)",
                                 distribution={k: c.get(k, 0) / n for k in map(str, range(5))}, n=n,
                                 source="kgweisman/ggw-rep run-01 2015-03-09, pair responses on the study's 5-point scale")] if n else [],
                meta={"experiment": "mind_perception", "capacity": cond, "dimension": dim, "a": a, "b": b})
