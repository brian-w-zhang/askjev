"""OpenBookQA (Mihaylov et al. 2018): elementary science questions, World factual Choice with truth.

The `main` config, all splits. Many stems are sentence fragments ("The sun is responsible for"); those are
wrapped in a fixed completion wording (origin=template). Filters, keys and node hints are shared with the mmlu
adapter; items already taken by mmlu, arc or sciq (near-duplicates) are skipped.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "openbookqa"
LICENSE = "Apache-2.0"
TARGET = env_int("TARGET_OPENBOOKQA", 2000)
SALT = "openbookqa-20260924"
SPLITS = ("train", "validation", "test")
EARLIER = ("mmlu", "arc", "sciq")

_spec = importlib.util.spec_from_file_location("sources.arc", Path(__file__).parents[1] / "arc" / "adapter.py")
ARC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ARC)
M = ARC.M


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "allenai/openbookqa", {f"{s}.parquet": f"main/{s}/0.parquet" for s in SPLITS})


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], ARC.taken_norms(EARLIER)
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for qid, q, choices, key in df.select("id", "question_stem", "choices", "answerKey").iter_rows():
            labels = list(choices["label"])
            if key not in labels:
                continue
            stem = M.clean(q)
            kept = M.snap_filter(stem, [M.clean(t) for t in choices["text"]], labels.index(key))
            if not kept:
                continue
            answers, correct = kept
            k = M.item_key(stem, answers[correct])
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": qid, "split": split, "q": stem, "answers": answers, "correct": correct, "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    return top_up([], _pool(raw_dir), TARGET, lambda x: x["id"], SALT)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: x["id"]):
        text, origin = M.completion_text(it["q"])
        meta = {"split": it["split"]}
        fl = M.flags(" ".join([it["q"], *it["answers"]]))
        if fl:
            meta["flags"] = fl
        node = M.science_hint(it["q"], it["answers"][it["correct"]])
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=node,
                              item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
