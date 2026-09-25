"""TREC-COVID (Voorhees et al. 2020) via BEIR: 50 COVID-19 research questions, CORD-19 paper abstracts,
graded relevance judgments by medical experts at NIST (0 not relevant, 1 partially, 2 relevant).

Templates:
- "trec_covid.pair": Choice "Which of `document_a` and `document_b` better answers `query`?" over a judged-
  relevant (2) and a judged-not-relevant (0) abstract for the same question. Both were retrieved by real
  systems and pooled for judging, so the non-relevant one is on topic. Position of the better one alternates.
- "trec_covid.relevance": Score (3 levels) "How well does `document` answer the research question in `query`?"
  on single abstracts, truth = the judged grade, balanced across grades. Disjoint documents from the pairs.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "trec_covid"
BASE = "https://huggingface.co/api/datasets/BeIR/"
FILES = {
    "qrels.parquet": BASE + "trec-covid-qrels/parquet/default/test/0.parquet",
    "queries.parquet": BASE + "trec-covid/parquet/queries/queries/0.parquet",
    "corpus.parquet": BASE + "trec-covid/parquet/corpus/corpus/0.parquet",
}
TARGET_PAIR = env_int("TARGET_TREC_COVID_PAIR", 2500)
TARGET_REL = env_int("TARGET_TREC_COVID_REL", 1500)
MIN_CHARS, MAX_CHARS = 300, 1300
LICENSE = "CORD-19 dataset license (Allen AI; per-paper licenses); TREC-COVID judgments public (NIST); BEIR CC-BY-SA-4.0"
PAIR_TEXT = "Which of `document_a` and `document_b` better answers `query`?"
PAIR_OPTIONS = {
    "document_a": "The first document gives more information that answers the question",
    "document_b": "The second document gives more information that answers the question",
}
REL_TEXT = "How well does `document` answer the research question in `query`?"
REL_LEVELS = [
    "The document does not address the question asked in the query",
    "The document addresses part of the question, or discusses the topic without giving an answer to it",
    "The document gives information that answers the question in the query",
]


def fetch(raw_dir: Path) -> None:
    for name, url in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _doc(title: str, text: str) -> str:
    title, text = " ".join(title.split()), " ".join(text.split())
    return f"{title}\n\n{text}" if title else text


def normalize(raw_dir: Path) -> Iterator[Question]:
    qrels = pl.read_parquet(raw_dir / "qrels.parquet").filter(pl.col("score") >= 0)
    queries = dict(pl.read_parquet(raw_dir / "queries.parquet").select("_id", "text").rows())
    need = set(qrels["corpus-id"].to_list())
    corpus = {}
    seen_text: set[str] = set()
    for cid, title, text in pl.read_parquet(raw_dir / "corpus.parquet").filter(pl.col("_id").is_in(need)).select("_id", "title", "text").rows():
        t = " ".join(text.split())
        if MIN_CHARS <= len(t) <= MAX_CHARS and t.lower() not in seen_text:
            seen_text.add(t.lower())
            corpus[cid] = _doc(title, text)
    by_q: dict[int, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    for qid, cid, score in qrels.select("query-id", "corpus-id", "score").rows():
        if cid in corpus:
            by_q[qid][score].append(cid)
    qids = sorted(by_q)
    for q in qids:
        for s in by_q[q]:
            by_q[q][s] = hash_order(by_q[q][s], lambda c: c, f"trec_covid.{q}.{s}")
    used: set[str] = set()

    # Single-document relevance first (balanced across grades, round-robin over questions), then pairs.
    rel = []
    per_grade = TARGET_REL // 3
    for grade in (0, 1, 2):
        n = 0
        while n < per_grade:
            progressed = False
            for q in qids:
                if n >= per_grade:
                    break
                docs = [c for c in by_q[q][grade] if c not in used]
                # take from the tail of the hash order; the head is left for the pairs
                pick = docs[-1] if docs else None
                if pick and len(by_q[q][grade]) > 30:
                    used.add(pick)
                    rel.append((q, pick, grade))
                    n += 1
                    progressed = True
            if not progressed:
                break
    pairs = []
    k = 0
    while len(pairs) < TARGET_PAIR:
        progressed = False
        for q in qids:
            if len(pairs) >= TARGET_PAIR:
                break
            good = next((c for c in by_q[q][2] if c not in used), None)
            bad = next((c for c in by_q[q][0] if c not in used), None)
            if good and bad:
                used.update((good, bad))
                pairs.append((q, good, bad, "document_a" if k % 2 == 0 else "document_b"))
                k += 1
                progressed = True
        if not progressed:
            break

    for q, good, bad, truth in pairs:
        a, b = (good, bad) if truth == "document_a" else (bad, good)
        yield Question(
            text=PAIR_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=PAIR_OPTIONS,
            state={"query": queries[str(q)], "document_a": corpus[a], "document_b": corpus[b]},
            shape="rank",
            node_hint="machine.search.reranking",
            template_id="trec_covid.pair",
            source_item_id=f"q{q}:{a}:{b}",
            license=LICENSE,
            truth=truth,
            meta={"query_id": q, "relevant": good, "not_relevant": bad},
        )
    for q, cid, grade in rel:
        yield Question(
            text=REL_TEXT,
            primitive="score",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=REL_LEVELS,
            state={"query": queries[str(q)], "document": corpus[cid]},
            shape="score",
            node_hint="machine.search.relevance",
            template_id="trec_covid.relevance",
            source_item_id=f"q{q}:{cid}",
            license=LICENSE,
            truth=grade,
            meta={"query_id": q},
        )
