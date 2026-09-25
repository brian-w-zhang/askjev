"""CaseHOLD (Zheng et al. 2021, via LexGLUE `case_hold`): citing contexts from US court opinions where the
parenthetical holding of a cited case was masked as <HOLDING>, with five candidate holdings (the real one and
four holdings of other cases retrieved as similar).

Template "casehold.holding_fits": one Noul per citing context: is `holding` the holding of the case cited
at <HOLDING>? Half the rows show the real holding, half one of the four distractors (seeded pick).
Truth = the dataset label. Pool = validation + test splits (the train split is left alone).
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "casehold_verify"
URL = "https://huggingface.co/api/datasets/coastalcph/lex_glue/parquet/case_hold/{split}/0.parquet"
SPLITS = ("validation", "test")
TARGET = env_int("TARGET_CASEHOLD_VERIFY", 2500)
SEED = 2021
LICENSE = "Apache-2.0 (CaseHOLD via LexGLUE, CC-BY-4.0 card)"
TEXT = (
    "Is `holding` the holding of the case cited at <HOLDING> in `excerpt`, a passage from a US court opinion?"
)
OPTIONS = {
    "true": "This is the cited case's holding: it fits the proposition the opinion cites the case for",
    "false": "This is the holding of some other case",
}
SENSITIVE = re.compile(r"\b(rape\w*|raped|sexual\w*|molest\w*|incest|child porn\w*|sodomy|suicid\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = []
    seen = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for i, r in enumerate(df.iter_rows(named=True)):
            ctx = r["context"].strip()
            if "<HOLDING>" not in ctx or len(ctx) > 1500 or len(ctx) < 200:
                continue
            ends = [e.strip() for e in r["endings"]]
            if len(set(ends)) != 5 or ctx in seen:
                continue
            seen.add(ctx)
            rows.append((f"{split}:{i}", ctx, ends, int(r["label"])))
    picked = hash_order(rows, lambda x: x[0], NAME)[:TARGET]
    rng = random.Random(SEED)
    for n, (sid, ctx, ends, lab) in enumerate(sorted(picked, key=lambda x: x[0])):
        pos = n % 2 == 0
        if pos:
            shown = ends[lab]
        else:
            shown = rng.choice([e for j, e in enumerate(ends) if j != lab])
        flags = ["sensitive"] if SENSITIVE.search(ctx + " " + shown) else []
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"excerpt": ctx, "holding": shown},
            shape="verify",
            node_hint="machine.legal",
            template_id="casehold.holding_fits",
            source_item_id=sid,
            license=LICENSE,
            truth=pos,
            meta={"flags": flags} if flags else {},
        )
