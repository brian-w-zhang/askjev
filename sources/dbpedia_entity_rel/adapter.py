"""DBpedia-Entity v2 (Hasibi et al., SIGIR 2017) via BEIR: 467 entity-search queries (keyword queries,
named-entity queries, list questions, natural-language questions) over DBpedia 2015-10 entity abstracts,
with graded relevance judged by crowd workers on pooled results (0 irrelevant, 1 relevant, 2 highly relevant).

Template "dbpedia_entity.pair": Choice "Which entity, `entity_a` or `entity_b`, is the better result for the
entity search `query`?" over a highly relevant (2) and an irrelevant (0) entity judged for the same query.
Both were retrieved by real systems and pooled for judging, so the irrelevant one usually shares words with
the query. Position of the relevant one alternates; round-robin over queries (test + dev qrels).
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "dbpedia_entity_rel"
BASE = "https://huggingface.co/api/datasets/BeIR/"
FILES = {
    "qrels_test.parquet": BASE + "dbpedia-entity-qrels/parquet/default/test/0.parquet",
    "qrels_dev.parquet": BASE + "dbpedia-entity-qrels/parquet/default/validation/0.parquet",
    "queries.parquet": BASE + "dbpedia-entity/parquet/queries/queries/0.parquet",
    "corpus.parquet": BASE + "dbpedia-entity/parquet/corpus/corpus/0.parquet",
}
TARGET = env_int("TARGET_DBPEDIA_ENTITY_REL", 2500)
MIN_CHARS, MAX_CHARS = 80, 900
LICENSE = "CC-BY-SA-3.0 (DBpedia abstracts); DBpedia-Entity v2 judgments public; BEIR CC-BY-SA-4.0"
TEXT = "Which entity, `entity_a` or `entity_b`, is the better result for the entity search `query`?"
OPTIONS = {
    "entity_a": "The first entity is what the search is looking for, or one of the things it asks to list",
    "entity_b": "The second entity is what the search is looking for, or one of the things it asks to list",
}
POLITICAL = re.compile(
    r"\b(president|senator|congress|election|party|parliament|politician|prime minister|republican|democrat|"
    r"obama|bush|clinton|trump|abortion|gun|immigra)", re.I)


def fetch(raw_dir: Path) -> None:
    for name, url in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=1200)
        r.raise_for_status()
        out.write_bytes(r.content)


def _doc(title: str, text: str) -> str:
    title, text = " ".join(title.split()), " ".join(text.split())
    if len(text) > 700:
        cut = text[:700]
        text = cut[: cut.rfind(". ") + 1] if ". " in cut[200:] else cut + "..."
    return f"{title}\n\n{text}" if title else text


def normalize(raw_dir: Path) -> Iterator[Question]:
    qrels = pl.concat([pl.read_parquet(raw_dir / "qrels_test.parquet"), pl.read_parquet(raw_dir / "qrels_dev.parquet")])
    qrels = qrels.filter(pl.col("score").is_in([0, 2]))
    queries = dict(pl.read_parquet(raw_dir / "queries.parquet").select("_id", "text").rows())
    need = set(qrels["corpus-id"].to_list())
    corpus = {}
    for cid, title, text in (
        pl.scan_parquet(raw_dir / "corpus.parquet").filter(pl.col("_id").is_in(list(need)))
        .select("_id", "title", "text").collect().rows()
    ):
        t = " ".join((text or "").split())
        if MIN_CHARS <= len(t) and title:
            corpus[cid] = _doc(title, t)
    by_q: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    for qid, cid, score in qrels.select("query-id", "corpus-id", "score").unique().rows():
        if cid in corpus and qid in queries:
            by_q[qid][score].append(cid)
    qids = sorted(by_q)
    for q in qids:
        for s in by_q[q]:
            by_q[q][s] = hash_order(by_q[q][s], lambda c: c, f"dbpedia_entity.{q}.{s}")
    cursor = {q: 0 for q in qids}
    pairs = []
    k = 0
    while len(pairs) < TARGET:
        progressed = False
        for q in qids:
            if len(pairs) >= TARGET:
                break
            i = cursor[q]
            if i < len(by_q[q][2]) and i < len(by_q[q][0]):
                cursor[q] += 1
                pairs.append((q, by_q[q][2][i], by_q[q][0][i], "entity_a" if k % 2 == 0 else "entity_b"))
                k += 1
                progressed = True
        if not progressed:
            break

    for q, good, bad, truth in pairs:
        a, b = (good, bad) if truth == "entity_a" else (bad, good)
        query = " ".join(queries[q].split())
        state = {"query": query, "entity_a": corpus[a], "entity_b": corpus[b]}
        flags = ["political"] if POLITICAL.search(query) else []
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state=state,
            shape="rank",
            node_hint="machine.search.reranking",
            template_id="dbpedia_entity.pair",
            source_item_id=f"{q}:{a}:{b}",
            license=LICENSE,
            truth=truth,
            meta={"query_id": q, "relevant": good, "not_relevant": bad, **({"flags": flags} if flags else {})},
        )
