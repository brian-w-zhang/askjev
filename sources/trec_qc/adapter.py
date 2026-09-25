"""TREC question classification (Li & Roth 2002, CogComp UIUC): 5,952 real English questions (TREC QA
tracks, USC, and others) labelled with the type of answer they expect (6 coarse / 50 fine classes).

Template "trec_qc.answer_type": Choice "What kind of answer is `question` looking for?" over the 6 coarse
types, truth = the coarse label (meta keeps the fine label). All abbreviation questions (the smallest class,
95) plus an even split of the remaining target over the other 5 types, salted hash order. The questions are
space-tokenized in the source; light detokenization is applied.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "trec_qc"
BASE = "https://cogcomp.seas.upenn.edu/Data/QA/QC/"
FILES = ("train_5500.label", "TREC_10.label")
TARGET = env_int("TARGET_TREC_QC", 2500)
LICENSE = "Research use (CogComp UIUC question classification data)"
TEXT = "What kind of answer is `question` looking for?"
OPTIONS = {
    "abbreviation": "What an abbreviation stands for, or the abbreviation of something",
    "description": "A definition, description, explanation, reason or manner (how or why)",
    "entity": "A thing: an animal, product, event, substance, term, color, work of art, sport...",
    "human": "A person, group of people or organization, or a description of one",
    "location": "A place: a city, country, mountain, state or other location",
    "numeric": "A number: a date, count, amount of money, distance, period, percentage, speed...",
}
COARSE = {"ABBR": "abbreviation", "DESC": "description", "ENTY": "entity", "HUM": "human", "LOC": "location", "NUM": "numeric"}


def _detok(s: str) -> str:
    s = s.replace("`` ", '"').replace(" ''", '"').replace("``", '"').replace("''", '"')
    s = re.sub(r" ([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[]) ", r"\1", s)
    s = re.sub(r" (n't|'s|'re|'ll|'ve|'d|'m)\b", r"\1", s)
    return " ".join(s.split())


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=60)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list[tuple]] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for f in FILES:
        for i, line in enumerate((raw_dir / f).read_bytes().decode("latin-1").splitlines()):
            if not line.strip():
                continue
            lab, q = line.split(" ", 1)
            coarse, fine = lab.split(":")
            q = _detok(q)
            if len(q) < 8 or q.lower() in seen:
                continue
            seen.add(q.lower())
            pools[COARSE[coarse]].append((f, i, q, fine))

    picked: list[tuple] = []
    order = sorted(pools, key=lambda k: len(pools[k]))
    for n, lab in enumerate(order):
        want = min(len(pools[lab]), (TARGET - len(picked)) // (len(order) - n))
        picked += [(lab, *x) for x in hash_order(pools[lab], lambda x: (x[0], x[1]), f"trec_qc|{lab}")[:want]]
    picked.sort(key=lambda x: (x[1], x[2]))

    for lab, f, i, q, fine in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"question": q},
            shape="classify",
            node_hint="machine.search",
            template_id="trec_qc.answer_type",
            source_item_id=f"{f}:{i}",
            license=LICENSE,
            truth=lab,
            meta={"file": f, "fine_label": fine},
        )
