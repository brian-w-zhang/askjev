"""Amazon Shopping Queries (ESCI; Reddy et al. 2022, amazon-science/esci-data): real, difficult
Amazon search queries paired with up to 40 candidate products, each labelled by annotators as
Exact, Substitute, Complement or Irrelevant for the query. US locale only.

Source file: the first test shard of the HF copy tasksource/esci (the official examples joined with the
official products table; 163k rows, 125k US). The official GitHub products parquet is 1.1 GB, so the
joined copy is used instead; its labels and product fields are unchanged.

Templates:
- "esci.match" (Score, node search.relevance): how well one product matches one query, four
  levels Irrelevant < Complement < Substitute < Exact written as situations. Truth = level index.
  Balanced 25% per label.
- "esci.pairwise" (Choice, node search.reranking): two products for the same query with different
  labels; which one matches better. Truth = the product with the higher label (Exact > Substitute >
  Complement > Irrelevant, the ESCI gain order). Position of the better product set by hash (~50/50).
"""

from __future__ import annotations

import hashlib
import html
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "esci_rerank"
URL = "https://huggingface.co/api/datasets/tasksource/esci/parquet/default/test/0.parquet"
TARGET_MATCH = env_int("TARGET_ESCI_MATCH", 2000)
TARGET_PAIR = env_int("TARGET_ESCI_PAIR", 1500)
LICENSE = "Apache-2.0"

LABELS = ["Irrelevant", "Complement", "Substitute", "Exact"]
MATCH_TEXT = "How well does the product in `product` match the shopping query `query`?"
MATCH_LEVELS = [
    "The product is not what the shopper searched for and is not something used with it",
    "The product is not what the shopper searched for, but it is something used together with it, "
    "such as an accessory, part, refill or add-on for the searched item",
    "The product is a different item that could stand in for what the shopper searched for, but it "
    "misses one or more details stated in the query, such as the brand, size, color, model or quantity",
    "The product is exactly what the shopper searched for and matches every detail stated in the query",
]
PAIR_TEXT = "Which product better matches the shopping query `query`: `product_a` or `product_b`?"
PAIR_OPTIONS = {
    "product_a": "The first product is the better match for what the shopper searched for",
    "product_b": "The second product is the better match for what the shopper searched for",
}
# (better, worse) label pairs for the pairwise template, sampled round-robin.
PAIR_TYPES = [
    ("Exact", "Substitute"), ("Exact", "Complement"), ("Exact", "Irrelevant"),
    ("Substitute", "Complement"), ("Substitute", "Irrelevant"), ("Complement", "Irrelevant"),
]
SENSITIVE = re.compile(
    r"\b(sex|sexy|porn\w*|nude\w*|naked|erotic\w*|dildo\w*|vibrator\w*|lingerie|condom\w*|lube|bdsm|"
    r"fetish\w*|thong\w*|masturbat\w*|suicid\w*)\b",
    re.I,
)
TAG = re.compile(r"<[^>]+>")


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test_0.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(html.unescape(TAG.sub(" ", s)).split())


def _product(r: dict, limit: int) -> str:
    parts = [_clean(r["product_title"])]
    if r["product_brand"]:
        parts.append(f"Brand: {_clean(r['product_brand'])}")
    if r["product_color"]:
        parts.append(f"Color: {_clean(r['product_color'])}")
    bullets = [_clean(b) for b in (r["product_bullet_point"] or "").split("\n") if _clean(b)]
    if bullets:
        parts.append("Features: " + " | ".join(bullets))
    elif _clean(r["product_description"]):
        parts.append("Description: " + _clean(r["product_description"]))
    text = "\n".join(parts)
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return text


def _flags(*texts: str) -> dict:
    return {"flags": ["sensitive"]} if any(SENSITIVE.search(t) for t in texts) else {}


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test_0.parquet").filter(
        (pl.col("product_locale") == "us") & pl.col("product_title").is_not_null()
    )
    rows = list(df.iter_rows(named=True))
    for r in rows:
        r["query"] = " ".join(r["query"].split())
    rows = [r for r in rows if len(r["query"]) >= 3]

    # Score template: balanced per label, at most one product per query per label.
    per = TARGET_MATCH // len(LABELS)
    picked = []
    for lab in LABELS:
        used_q: set[int] = set()
        for r in hash_order([r for r in rows if r["esci_label"] == lab], lambda x: x["example_id"], f"esci.{lab}"):
            if len(used_q) >= per:
                break
            if r["query_id"] in used_q:
                continue
            used_q.add(r["query_id"])
            picked.append(r)
    picked.sort(key=lambda x: x["example_id"])
    for r in picked:
        prod = _product(r, 900)
        yield Question(
            text=MATCH_TEXT,
            primitive="score",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=MATCH_LEVELS,
            state={"query": r["query"], "product": prod},
            shape="score",
            node_hint="machine.search.relevance",
            template_id="esci.match",
            source_item_id=f"test:{r['example_id']}",
            license=LICENSE,
            truth=LABELS.index(r["esci_label"]),
            meta={"label_raw": r["esci_label"], "query_id": r["query_id"], "product_id": r["product_id"],
                  "small_version": r["small_version"], **_flags(r["query"], prod)},
        )

    # Pairwise template: one pair per query, round-robin over pair types; queries not used above.
    used_match = {r["query_id"] for r in picked}
    by_q: dict[int, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["query_id"] not in used_match:
            by_q[r["query_id"]][r["esci_label"]].append(r)
    queue = {t: hash_order([q for q, d in by_q.items() if d[t[0]] and d[t[1]]], lambda q: q, f"esci.pair.{t}")
             for t in PAIR_TYPES}
    cursor = {t: 0 for t in PAIR_TYPES}
    used_pair: set[int] = set()
    pairs = []
    per_type = TARGET_PAIR // len(PAIR_TYPES)
    counts = {t: 0 for t in PAIR_TYPES}
    # Round-robin with an equal cap per type; once the rarer pairings run out, lift the cap.
    capped, progressed = True, True
    while len(pairs) < TARGET_PAIR and (progressed or capped):
        if not progressed:
            capped = False
        progressed = False
        for t in PAIR_TYPES:
            if len(pairs) >= TARGET_PAIR or (capped and counts[t] >= per_type):
                continue
            qlist = queue[t]
            while cursor[t] < len(qlist) and qlist[cursor[t]] in used_pair:
                cursor[t] += 1
            if cursor[t] >= len(qlist):
                continue
            q = qlist[cursor[t]]
            cursor[t] += 1
            used_pair.add(q)
            good = hash_order(by_q[q][t[0]], lambda x: x["example_id"], "esci.good")[0]
            bad = hash_order(by_q[q][t[1]], lambda x: x["example_id"], "esci.bad")[0]
            pairs.append((t, good, bad))
            counts[t] += 1
            progressed = True
    pairs.sort(key=lambda x: x[1]["example_id"])
    for (gl, bl), good, bad in pairs:
        swap = int(hashlib.sha256(f"esci.side|{good['example_id']}|{bad['example_id']}".encode()).hexdigest(), 16) % 2
        a, b = (bad, good) if swap else (good, bad)
        pa, pb = _product(a, 600), _product(b, 600)
        yield Question(
            text=PAIR_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=PAIR_OPTIONS,
            state={"query": good["query"], "product_a": pa, "product_b": pb},
            shape="rank",
            node_hint="machine.search.reranking",
            template_id="esci.pairwise",
            source_item_id=f"test:{a['example_id']}|{b['example_id']}",
            license=LICENSE,
            truth="product_b" if swap else "product_a",
            meta={"labels_raw": [a["esci_label"], b["esci_label"]], "query_id": good["query_id"],
                  "pair_type": f"{gl}>{bl}", **_flags(good["query"], pa, pb)},
        )
