"""SciQ (Welbl et al. 2017): crowdsourced science exam questions, World factual Choice with truth.

Choice over the correct answer and its 3 distractors, shuffled deterministically per question. Filters, keys and
node hints are shared with the mmlu adapter; items already taken by mmlu or arc (near-duplicates) are skipped.
"""

from __future__ import annotations

import hashlib
import importlib.util
import random
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "sciq"
LICENSE = "CC BY-NC 3.0"
TARGET = env_int("TARGET_SCIQ", 3900)
SALT = "sciq-20260924"
SPLITS = ("train", "validation", "test")
EARLIER = ("mmlu", "arc")

_spec = importlib.util.spec_from_file_location("sources.arc", Path(__file__).parents[1] / "arc" / "adapter.py")
ARC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ARC)
M = ARC.M


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "allenai/sciq", {f"{s}.parquet": f"default/{s}/0.parquet" for s in SPLITS})


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], ARC.taken_norms(EARLIER)
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, q, right, d1, d2, d3 in df.select(
                "row", "question", "correct_answer", "distractor1", "distractor2", "distractor3").iter_rows():
            stem = M.clean(q)
            if stem.endswith("?."):
                stem = stem[:-1]
            answers = [M.clean(x) for x in (right, d1, d2, d3)]
            rng = random.Random(int(hashlib.sha256(f"{SALT}:{split}:{row}".encode()).hexdigest()[:16], 16))
            order = list(range(4))
            rng.shuffle(order)
            kept = M.snap_filter(stem, [answers[i] for i in order], order.index(0))
            if not kept:
                continue
            answers, correct = kept
            k = M.item_key(stem, answers[correct])
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": f"{split}:{row}", "q": stem, "answers": answers, "correct": correct, "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    return top_up([], _pool(raw_dir), TARGET, lambda x: x["id"], SALT)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: (x["id"].split(":")[0], int(x["id"].split(":")[1]))):
        text, origin = M.completion_text(it["q"])
        meta = {"split": it["id"].split(":")[0]}
        fl = M.flags(" ".join([it["q"], *it["answers"]]))
        if fl:
            meta["flags"] = fl
        node = M.science_hint(it["q"], it["answers"][it["correct"]])
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=node,
                              item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
