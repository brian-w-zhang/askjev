"""SQuAD 2.0 (Rajpurkar et al. 2018), dev set: Wikipedia paragraphs with crowd-written questions, some of
them deliberately unanswerable from the paragraph.

Template "squad2_spans.answer_span": Choice "Which span from `passage` answers `question`?" over 4 candidate
spans plus "not_in_passage". Candidates are the gold answer (the most common crowd answer text) and answers to
other questions about the same paragraph (real spans of the same text, never overlapping any gold answer).
Unanswerable questions get 4 such spans and truth "not_in_passage". 60% answerable / 40% unanswerable.
"""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "squad2_spans"
URL = "https://huggingface.co/api/datasets/rajpurkar/squad_v2/parquet/squad_v2/validation/0.parquet"
TARGET = env_int("TARGET_SQUAD2_SPANS", 2500)
ANSWERABLE_SHARE = 0.6
N_SPANS = 4
MAX_SPAN = 60
MAX_PASSAGE = 1500
LICENSE = "CC-BY-SA-4.0"
TEXT = "Which span from `passage` answers `question`?"
NONE_KEY = "not_in_passage"
NONE_DESC = "The passage does not contain the answer to the question"
POLITICAL = re.compile(
    r"\b(abortion|gun control|immigra\w+|Republican|Democrat\w*|Trump|Obama|Clinton|Biden|election\w*|"
    r"Brexit|Israel\w*|Palestin\w+|gay marriage|same-sex marriage)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "validation.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", s.lower()).split())


def _overlaps(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    return not na or not nb or na in nb or nb in na


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "validation.parquet")
    rows = df.select("id", "title", "context", "question", "answers").rows()
    spans_by_ctx: dict[str, list[str]] = defaultdict(list)
    for _id, _t, ctx, _q, ans in rows:
        for t in ans["text"]:
            t = t.strip()
            if t and len(t) <= MAX_SPAN and t not in spans_by_ctx[ctx]:
                spans_by_ctx[ctx].append(t)

    items = []  # (id, title, ctx, question, truth_key, options_list)
    for _id, title, ctx, q, ans in rows:
        if len(ctx) > MAX_PASSAGE:  # never truncate: the answer or a candidate could be cut off
            continue
        golds = [t.strip() for t in ans["text"] if t.strip()]
        rng = random.Random(_id)
        if golds:
            gold = Counter(golds).most_common(1)[0][0]
            if len(gold) > MAX_SPAN:
                continue
            pool = [s for s in spans_by_ctx[ctx] if not any(_overlaps(s, g) for g in golds)]
        else:
            gold = None
            pool = list(spans_by_ctx[ctx])
        # Distractors must not overlap each other either.
        rng.shuffle(pool)
        picked: list[str] = []
        for s in pool:
            if not any(_overlaps(s, p) for p in picked):
                picked.append(s)
            if len(picked) == N_SPANS - (1 if gold else 0):
                break
        if len(picked) < N_SPANS - (1 if gold else 0):
            continue
        opts = picked + ([gold] if gold else [])
        rng.shuffle(opts)
        items.append((_id, title, ctx, q.strip(), gold or NONE_KEY, opts))

    n_ans = round(TARGET * ANSWERABLE_SHARE)
    ans_items = [x for x in items if x[4] != NONE_KEY]
    none_items = [x for x in items if x[4] == NONE_KEY]
    chosen = hash_order(ans_items, lambda x: x[0], "squad2.ans")[:n_ans]
    chosen += hash_order(none_items, lambda x: x[0], "squad2.none")[: TARGET - len(chosen)]
    for _id, title, ctx, q, truth, opts in sorted(chosen, key=lambda x: x[0]):
        flags = ["political"] if POLITICAL.search(ctx + " " + q) else []
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={**{o: None for o in opts}, NONE_KEY: NONE_DESC},
            state={"passage": ctx, "question": q},
            shape="extract",
            node_hint="machine.search.rag_gating",
            template_id="squad2_spans.answer_span",
            source_item_id=f"dev:{_id}",
            license=LICENSE,
            truth=truth,
            meta={"title": title, "answerable": truth != NONE_KEY, **({"flags": flags} if flags else {})},
        )
