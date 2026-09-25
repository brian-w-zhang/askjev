"""AI2 Reasoning Challenge (Clark et al. 2018): grade-school science multiple choice, World factual Choice with truth.

All of ARC-Challenge, then ARC-Easy to fill the target. Filters and keys are shared with the mmlu adapter;
questions already taken by mmlu (normalized text) are skipped.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "arc"
LICENSE = "CC BY-SA 4.0"
TARGET = env_int("TARGET_ARC", 7500)  # every clean item
SALT = "arc-20260924"
CONFIGS = ("ARC-Challenge", "ARC-Easy")
SPLITS = ("train", "validation", "test")
EARLIER = ("mmlu",)

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "allenai/ai2_arc",
               {f"{c}_{s}.parquet": f"{c}/{s}/0.parquet" for c in CONFIGS for s in SPLITS})


def taken_norms(names: tuple[str, ...]) -> set[str]:
    out: set[str] = set()
    for n in names:
        mod, raw = M.load(n)
        out |= {it["norm"] for it in mod.selected(raw)}
    return out


def _pool(raw_dir: Path, config: str, seen: set[str]) -> list[dict]:
    pool = []
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{config}_{split}.parquet")
        for qid, q, choices, key in df.select("id", "question", "choices", "answerKey").iter_rows():
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
            pool.append({"id": qid, "config": config, "split": split, "q": stem, "answers": answers,
                         "correct": correct, "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    seen = taken_norms(EARLIER)
    challenge = _pool(raw_dir, "ARC-Challenge", seen)
    picked = top_up([], challenge, TARGET, lambda x: x["id"], SALT)
    easy = _pool(raw_dir, "ARC-Easy", seen)
    return picked + top_up(picked, easy, TARGET - len(picked), lambda x: x["id"], SALT)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: (x["config"], x["id"])):
        text, origin = M.completion_text(it["q"])
        meta = {"config": it["config"], "split": it["split"]}
        fl = M.flags(" ".join([it["q"], *it["answers"]]))
        if fl:
            meta["flags"] = fl
        node = M.science_hint(it["q"], it["answers"][it["correct"]])
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=node,
                              item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
