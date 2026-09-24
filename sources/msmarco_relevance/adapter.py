"""MS MARCO v1.1 (Nguyen et al. 2016), validation split: real Bing queries, each with ~10 retrieved web
passages; `is_selected` marks the passage(s) the human annotator used to write the answer.

Template "msmarco.answers_query": one Noul per (query, passage): does the passage contain an answer to
the query? Truth = is_selected. One pair per query (distinct queries throughout), 50/50 seeded.
Negatives are unselected passages retrieved for the same query (hard negatives). MS MARCO is known to
have false negatives (unselected passages that also answer), so negatives whose text contains the
annotator's (short) answer string are skipped; some false negatives will remain.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "msmarco_relevance"
URL = "https://huggingface.co/api/datasets/microsoft/ms_marco/parquet/v1.1/validation/0.parquet"
TARGET_V1 = 200  # the original seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_MSMARCO_RELEVANCE", TARGET_V1)  # Phase 6: 4,000
EXTRA = env_int("EXTRA_MSMARCO_RELEVANCE", 0)  # secondary template size; Phase 6: 1,500
SEED = 2016
MAX_CHARS = 1500
LICENSE = "MS MARCO terms (non-commercial research)"
TEXT = "Does `passage` contain an answer to `query`?"
CRITERIA = {
    "true": "The passage states the information the query is looking for",
    "false": "The passage does not state it, even if it is on a related topic",
}

LEVEL_TEXT = "How relevant is `passage` to `query`?"
LEVELS = [
    "The passage is about a different subject from the query",
    "The passage shares the query's general subject but does not address what the query asks",
    "The passage addresses what the query asks but only partly or indirectly answers it",
    "The passage directly and fully answers the query",
]


def _pool(passages, query: str, label: bool, answers: list) -> list[tuple[int, str, str]]:
    short_answers = [a.strip().lower().rstrip(".") for a in answers if 0 < len(a.strip()) <= 60]
    pool = []
    for pi, (s, text, url) in enumerate(passages):
        text = " ".join(text.split())
        if bool(s) != label or not text or len(query) + len(text) > MAX_CHARS:
            continue
        if not label and any(a and a in text.lower() for a in short_answers):
            continue
        pool.append((pi, text, url))
    return pool


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "v1.1_validation.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "v1.1_validation.parquet").select("query_id", "query", "query_type", "answers", "passages")
    cands: list[tuple[int, str, str, list, list]] = []
    for qid, query, qtype, answers, passages in df.iter_rows():
        sel = passages["is_selected"]
        if not any(sel) or not answers or answers[0] == "No Answer Present.":
            continue
        cands.append((qid, " ".join(query.split()), qtype, answers, list(zip(sel, passages["passage_text"], passages["url"]))))
    cands.sort(key=lambda x: x[0])

    rng = random.Random(SEED)
    rng.shuffle(cands)
    items = []
    v1 = min(TARGET, TARGET_V1)
    want = {True: v1 // 2, False: v1 - v1 // 2}
    for i, (qid, query, qtype, answers, passages) in enumerate(cands):
        label = i % 2 == 0  # alternate so each query contributes one pair and labels stay balanced
        if want[label] == 0:
            label = not label
            if want[label] == 0:
                break
        short_answers = [a.strip().lower().rstrip(".") for a in answers if 0 < len(a.strip()) <= 60]
        pool = []
        for pi, (s, text, url) in enumerate(passages):
            text = " ".join(text.split())
            if bool(s) != label or not text or len(query) + len(text) > MAX_CHARS:
                continue
            if not label and any(a and a in text.lower() for a in short_answers):
                continue
            pool.append((pi, text, url))
        if not pool:
            continue
        pi, text, url = rng.choice(pool)
        want[label] -= 1
        items.append((qid, pi, query, qtype, text, url, label, answers))

    # Phase 6 top-up: remaining queries in hash order, split by position parity into a positive stream
    # (even) and a negative stream (odd), each taking its first `want` usable pairs, passage picked by hash
    # order. No decision depends on TARGET, so the top-up is prefix-stable (one pair per query still holds).
    used = {x[0] for x in items}
    want = {True: TARGET // 2 - sum(x[6] for x in items)}
    want[False] = TARGET - len(items) - want[True]
    rest = hash_order([c for c in cands if c[0] not in used], lambda c: c[0], "msmarco.topup")
    for label in (True, False):
        n = 0
        for qid, query, qtype, answers, passages in rest[0 if label else 1 :: 2]:
            if n >= want[label]:
                break
            pool = _pool(passages, query, label, answers)
            if not pool:
                continue
            pi, text, url = hash_order(pool, lambda p: p[0], f"msmarco.{qid}")[0]
            n += 1
            items.append((qid, pi, query, qtype, text, url, label, answers))
    items.sort(key=lambda x: (x[0], x[1]))

    for qid, pi, query, qtype, text, url, label, answers in items:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"query": query, "passage": text},
            shape="rank",
            node_hint="machine.search.relevance",
            template_id="msmarco.answers_query",
            source_item_id=f"validation:{qid}:{pi}",
            license=LICENSE,
            truth=label,
            meta={"split": "validation", "query_type": qtype, "url": url, "answers": answers[:3]},
        )

    # Secondary template: graded relevance on the first EXTRA sampled pairs (hash order). No truth:
    # is_selected says whether the annotator used the passage, not how relevant it is.
    tid = "msmarco.relevance_level"
    sub = sorted(hash_order(items, lambda x: (x[0], x[1]), tid)[:EXTRA], key=lambda x: (x[0], x[1]))
    for qid, pi, query, qtype, text, url, label, answers in sub:
        yield Question(
            text=LEVEL_TEXT,
            primitive="score",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            state={"query": query, "passage": text},
            shape="rank",
            node_hint="machine.search.relevance",
            template_id=tid,
            source_item_id=f"validation:{qid}:{pi}",
            license=LICENSE,
            truth=None,
            meta={"split": "validation", "query_type": qtype, "url": url, "is_selected": label},
        )
