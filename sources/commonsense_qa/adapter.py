"""CommonsenseQA (Talmor et al. 2019): crowd-written 5-way commonsense questions, World factual Choice with truth.

Choice over the five answer texts (readable keys), truth = the labeled answer. Train + validation (the test split has
no answers). Filters, keys, flags and dedupe are shared with the mmlu adapter; the node hint is boolq's keyword map,
then the science keyword map, else plain `world` so the beam walk places it.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "commonsense_qa"
LICENSE = "MIT"
TARGET = env_int("TARGET_COMMONSENSE_QA", 6000)
SALT = "commonsense_qa-20260924"
SPLITS = ("train", "validation")

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "tau/commonsense_qa", {f"{s}.parquet": f"default/{s}/0.parquet" for s in SPLITS})


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for qid, q, concept, choices, key in df.select(
                "id", "question", "question_concept", "choices", "answerKey").iter_rows():
            labels, texts = list(choices["label"]), [M.clean(t) for t in choices["text"]]
            if key not in labels:
                continue
            stem = " ".join(M.clean(q).split())
            if not stem.endswith("?"):
                stem = stem.rstrip(" .") + "?"
            kept = M.snap_filter(stem, texts, labels.index(key))
            if not kept or len(kept[0]) < 3:
                continue
            answers, correct = kept
            k = M.item_key(stem, answers[correct])
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": f"{split}:{qid}", "q": stem, "concept": concept, "answers": answers, "correct": correct})
    return pool


FALSE_FRIENDS = re.compile(r"\b(lead(s|ing)? (to|up)|push\w*|pull\w*|rest\w*|current\w*|light(ly)?|forces? (him|her|them|you)|"
                           r"(in|at|on) motion|seasons?)\b", re.I)


def _node(q: str, answer: str) -> str:
    """boolq's keyword hint; else the science map, but only on a clear signal (the everyday verbs of these
    questions, like "lead to" or "push", would otherwise land in chemistry or physics); else `world`."""
    h = M.topic_hint(q + " " + answer, within="world")
    if h != "world":
        return h
    qs, ans = FALSE_FRIENDS.sub(" ", q), FALSE_FRIENDS.sub(" ", answer)
    sci = M.science_hint(qs, ans, default="world")
    if sci == "world":
        return sci
    rx = next(r for r, n in M.SCIENCE_RE if n == sci)
    return sci if 2 * len(rx.findall(qs)) + len(rx.findall(ans)) >= 3 else "world"


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(top_up([], _pool(raw_dir), TARGET, lambda x: x["id"], SALT), key=lambda x: x["id"]):
        meta = {"split": it["id"].split(":")[0], "concept": it["concept"]}
        fl = M.flags(" ".join([it["q"], *it["answers"]]))
        if fl:
            meta["flags"] = fl
        q = M.choice_question(source=NAME, text=it["q"], answers=it["answers"], correct=it["correct"],
                              node=_node(it["q"], it["answers"][it["correct"]]), item_id=it["id"], license=LICENSE,
                              meta=meta)
        if q:
            yield q
