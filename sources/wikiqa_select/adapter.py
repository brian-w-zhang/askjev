"""WikiQA (Yang et al. 2015): Bing query-log questions paired with the sentences of a Wikipedia summary,
each sentence labelled by crowdworkers as answering the question or not.

Template "wikiqa_select.answer_sentence": Choice "Which sentence in `sentences` answers `question`?" over the
candidate sentences (keys sentence_1..sentence_n, in document order, at most 10), truth = the one sentence
labelled correct. Only questions with exactly one correct sentence and at least 3 candidates.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wikiqa_select"
URL = "https://huggingface.co/api/datasets/microsoft/wiki_qa/parquet/default/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
TARGET = env_int("TARGET_WIKIQA_SELECT", 2500)
MAX_CANDIDATES = 10
LICENSE = "Microsoft Research Data License Agreement (WikiQA); Wikipedia text CC-BY-SA"
TEXT = "Which sentence in `sentences` answers `question`?"


def fetch(raw_dir: Path) -> None:
    for s in SPLITS:
        out = raw_dir / f"{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=s), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    groups: dict[tuple[str, str], list] = defaultdict(list)
    meta: dict[tuple[str, str], tuple[str, str]] = {}
    for s in SPLITS:
        df = pl.read_parquet(raw_dir / f"{s}.parquet")
        for qid, q, title, sent, lab in df.select("question_id", "question", "document_title", "answer", "label").rows():
            groups[(s, qid)].append((" ".join(sent.split()), lab))
            meta[(s, qid)] = (q.strip(), title)
    items = []
    for key, cands in groups.items():
        if sum(l for _, l in cands) != 1 or len(cands) < 3:
            continue
        gold_i = next(i for i, (_, l) in enumerate(cands) if l == 1)
        # Keep a window of at most MAX_CANDIDATES sentences in document order that contains the gold one.
        start = max(0, min(gold_i - MAX_CANDIDATES // 2, len(cands) - MAX_CANDIDATES))
        window = cands[start : start + MAX_CANDIDATES]
        items.append((key, window, gold_i - start))
    for (split, qid), window, gi in sorted(hash_order(items, lambda x: x[0], "wikiqa.v1")[:TARGET], key=lambda x: x[0]):
        q, title = meta[(split, qid)]
        keys = [f"sentence_{i + 1}" for i in range(len(window))]
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={k: None for k in keys},
            state={"question": q, "sentences": {k: s for k, (s, _) in zip(keys, window)}},
            shape="rank",
            node_hint="machine.search.reranking",
            template_id="wikiqa_select.answer_sentence",
            source_item_id=f"{split}:{qid}",
            license=LICENSE,
            truth=keys[gi],
            meta={"document_title": title, "n_candidates": len(window)},
        )
