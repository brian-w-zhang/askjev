"""UNFAIR-ToS (Lippi et al. 2019, via LexGLUE): sentences from 50 online Terms of Service, each
labelled with zero or more of 8 potentially-unfair clause types.

Template "unfair_tos.unfair": one Noul per sentence: is it potentially unfair to the consumer?
Truth = the sentence has at least one unfair-clause label. Balanced 50/50, seeded, across all splits.
The dataset text is lowercased and tokenized ("terms , at any time"); a light detokenization
(punctuation spacing, `` '' quotes) is applied, case is left as is.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question

NAME = "unfair_tos"
URL = "https://huggingface.co/api/datasets/coastalcph/lex_glue/parquet/unfair_tos/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
TARGET = 200
SEED = 2019
LICENSE = "CC-BY-4.0"
LABELS = [
    "limitation_of_liability",
    "unilateral_termination",
    "unilateral_change",
    "content_removal",
    "contract_by_using",
    "choice_of_law",
    "jurisdiction",
    "arbitration",
]
TEXT = (
    "Is `clause` potentially unfair to the consumer (e.g. limitation of liability, unilateral "
    "termination or change, content removal, contract by using, choice of law, jurisdiction, arbitration)?"
)
CRITERIA = {
    "true": "The clause limits the provider's liability, lets it terminate, change the terms or remove "
    "content at its discretion, binds the user just by using the service, or imposes a governing law, "
    "forum or arbitration on disputes",
    "false": "The clause does none of these",
}


def _detok(s: str) -> str:
    s = " ".join(s.split())
    s = s.replace("`` ", '"').replace(" ''", '"').replace("``", '"').replace("''", '"')
    s = re.sub(r" ([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[]) ", r"\1", s)
    s = re.sub(r" (n't|'s|'re|'ll|'ve|'d|'m)\b", r"\1", s)
    return s


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[str, int, str, list[int]]]] = {True: [], False: []}
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for row, (text, labels) in enumerate(df.select("text", "labels").iter_rows()):
            clause = _detok(text)
            key = clause.lower()
            # Skip fragments (headings, dates) and anything too long.
            if len(clause) < 40 or len(clause) > 1500 or key in seen:
                continue
            seen.add(key)
            pools[bool(labels)].append((split, row, clause, sorted(labels)))

    rng = random.Random(SEED)
    n_pos = TARGET // 2
    items = [(True, *x) for x in rng.sample(pools[True], n_pos)]
    items += [(False, *x) for x in rng.sample(pools[False], TARGET - n_pos)]
    order = {s: i for i, s in enumerate(SPLITS)}
    items.sort(key=lambda x: (order[x[1]], x[2]))

    for unfair, split, row, clause, labels in items:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"clause": clause},
            shape="detect",
            node_hint="machine.legal.clause_detection",
            template_id="unfair_tos.unfair",
            source_item_id=f"{split}:{row}",
            license=LICENSE,
            truth=unfair,
            meta={"split": split, "label_raw": [LABELS[i] for i in labels]},
        )
