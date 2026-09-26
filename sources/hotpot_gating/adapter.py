"""HotpotQA (Yang et al. 2018) distractor setting, bridge questions only, used for RAG context gating.

Each HotpotQA question comes with 10 Wikipedia paragraphs: the 2 gold paragraphs whose sentences crowd
workers marked as the supporting facts needed to answer it (bridge questions need both: one names the
bridge entity, the other holds the answer), and 8 distractors retrieved by bigram TF-IDF against the
question, so they are on topic but were not needed.

Template "hotpot_gating.needed": Noul "Should `passage` go into the context for answering `question`?"
One item per question: either one of its gold paragraphs (truth true) or one of its distractors (truth
false), half and half. Comparison questions are left out (they are used closed-book by hotpot_compare).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "hotpot_gating"
URL = "https://huggingface.co/api/datasets/hotpotqa/hotpot_qa/parquet/distractor/validation/0.parquet"
TARGET = env_int("TARGET_HOTPOT_GATING", 2500)
LICENSE = "CC-BY-SA-4.0"
TEXT = "Should `passage` go into the context for answering `question`?"
OPTIONS = {
    "true": "The passage states a fact that is needed to answer the question",
    "false": "The passage may be on a related topic, but nothing in it is needed to answer the question",
}
MIN_CHARS, MAX_CHARS = 120, 1500


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "validation_0.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    out.write_bytes(r.content)


def _para(title: str, sents: list[str]) -> str:
    body = " ".join(" ".join(s.split()) for s in sents).strip()
    return f"{title}\n\n{body}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "validation_0.parquet").filter(pl.col("type") == "bridge")
    rows = hash_order(df.iter_rows(named=True), lambda r: r["id"], "hotpot_gating")
    n = {True: 0, False: 0}
    half = {True: TARGET // 2, False: TARGET - TARGET // 2}
    seen_q: set[str] = set()
    for r in rows:
        if n[True] >= half[True] and n[False] >= half[False]:
            break
        q = " ".join(r["question"].split())
        if q.lower() in seen_q:
            continue
        gold_titles = set(r["supporting_facts"]["title"])
        paras = list(zip(r["context"]["title"], r["context"]["sentences"]))
        gold = [(t, s) for t, s in paras if t in gold_titles]
        dist = [(t, s) for t, s in paras if t not in gold_titles]
        if len(gold) != 2 or len(dist) < 2:
            continue
        # alternate the label along the hash order; fall back to the other label once one half is full
        want = n[True] <= n[False]
        if n[want] >= half[want]:
            want = not want
        pool = gold if want else dist
        pool = [p for p in pool if MIN_CHARS <= len(_para(*p)) <= MAX_CHARS]
        if not pool:
            continue
        title, sents = hash_order(pool, lambda p: p[0], f"hotpot_gating.{r['id']}")[0]
        seen_q.add(q.lower())
        n[want] += 1
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"question": q, "passage": _para(title, sents)},
            shape="verify",
            node_hint="machine.search.rag_gating",
            template_id="hotpot_gating.needed",
            source_item_id=f"{r['id']}:{title}",
            license=LICENSE,
            truth=want,
            meta={"split": "validation", "answer": r["answer"], "gold_titles": sorted(gold_titles), "passage_title": title},
        )
