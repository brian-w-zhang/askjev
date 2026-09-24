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
from askjev.sampling import env_int, hash_order, top_up

NAME = "unfair_tos"
URL = "https://huggingface.co/api/datasets/coastalcph/lex_glue/parquet/unfair_tos/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
TARGET_V1 = 200  # the original seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_UNFAIR_TOS", TARGET_V1)  # Phase 6: 4,000
EXTRA = env_int("EXTRA_UNFAIR_TOS", 0)  # secondary template size; Phase 6: 1,500
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

TYPE_TEXT = "Which kind of potentially unfair clause is `clause`, if any?"
TYPE_OPTIONS = {
    "limitation_of_liability": "Limits or excludes the provider's liability for losses or damages",
    "unilateral_termination": "Lets the provider suspend or terminate the service or account at its discretion",
    "unilateral_change": "Lets the provider change the terms or the service at its discretion",
    "content_removal": "Lets the provider remove or edit the user's content at its discretion",
    "contract_by_using": "Binds the user to the terms simply by using the service",
    "choice_of_law": "Sets which country's or state's law governs the terms",
    "jurisdiction": "Sets which courts or place disputes must be brought in",
    "arbitration": "Sends disputes to arbitration instead of court",
    "none": "None of these",
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
    v1 = min(TARGET, TARGET_V1)
    n_pos = v1 // 2
    items = [(True, *x) for x in rng.sample(pools[True], n_pos)]
    items += [(False, *x) for x in rng.sample(pools[False], v1 - n_pos)]
    # Phase 6 top-up (hash order, prefix-stable): unfair clauses up to half of TARGET while they last.
    key = lambda x: (x[1], x[2])  # noqa: E731
    pos = [(True, *x) for x in pools[True]]
    more = top_up(items, pos, min(TARGET - len(items), TARGET // 2 - n_pos), key, "unfair_tos.pos")
    items += more
    items += top_up(items, [(False, *x) for x in pools[False]], TARGET - len(items), key, "unfair_tos.neg")
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

    # Secondary template: which clause type (truth only when the sentence has zero or one label).
    tid = "unfair_tos.clause_type"
    half = EXTRA // 2
    sub = hash_order([x for x in items if x[0]], key, tid)[:half]
    sub += hash_order([x for x in items if not x[0]], key, tid)[: EXTRA - len(sub)]
    sub.sort(key=lambda x: (order[x[1]], x[2]))
    for unfair, split, row, clause, labels in sub:
        truth = LABELS[labels[0]] if len(labels) == 1 else ("none" if not labels else None)
        yield Question(
            text=TYPE_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=TYPE_OPTIONS,
            state={"clause": clause},
            shape="classify",
            node_hint="machine.legal.clause_detection",
            template_id=tid,
            source_item_id=f"{split}:{row}",
            license=LICENSE,
            truth=truth,
            meta={"split": split, "label_raw": [LABELS[i] for i in labels]},
        )
