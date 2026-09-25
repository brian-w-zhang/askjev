"""StrategyQA (Geva et al. 2021): yes/no questions needing implicit multi-step world knowledge, World factual Noul.

The full annotated set (2,290 questions; wics/strategy-qa `strategyQA/test`, which is the original train file with
facts and decompositions). Truth = the dataset answer. Questions with digits (counting, dates, arithmetic;
docs/01-jev.md section 7) and exact duplicates are dropped. node_hint = the boolq keyword rules, scored over the
question, the item's Wikipedia term, and its short description.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "strategyqa"
LICENSE = "MIT"
TARGET = env_int("TARGET_STRATEGYQA", 2000)
SALT = "strategyqa-20260924"

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "wics/strategy-qa", {"strategyqa.parquet": "strategyQA/test/0.parquet"})


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    df = pl.read_parquet(raw_dir / "strategyqa.parquet")
    for qid, q, ans, term, desc, facts in df.select(
            "qid", "question", "answer", "term", "description", "facts").iter_rows():
        text = M.clean(q)
        if not text or M.DIGIT.search(text) or M.BOOLQ.SLUR.search(text):
            continue
        if not text.endswith("?"):
            text = text.rstrip(" .") + "?"
        text = text[0].upper() + text[1:]
        k = M.norm(text)
        if k in seen:
            continue
        seen.add(k)
        pool.append({"id": qid, "q": text, "answer": bool(ans), "term": M.clean(term or ""),
                     "description": M.clean(desc or ""), "facts": list(facts or [])})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    return top_up([], _pool(raw_dir), TARGET, lambda x: x["id"], SALT)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: x["id"]):
        passage = f"{it['term']} is a {it['description']}." if it["description"] else ""
        meta = {"term": it["term"], "term_description": it["description"], "facts": it["facts"]}
        fl = M.flags(it["q"])
        if fl:
            meta["flags"] = fl
        yield Question(
            text=it["q"],
            primitive="noul",
            hemisphere="world",
            kind="factual",
            origin="dataset",
            source=NAME,
            node_hint=M.BOOLQ.node_hint(it["q"], it["term"], passage),
            source_item_id=it["id"],
            license=LICENSE,
            truth=it["answer"],
            meta=meta,
        )
