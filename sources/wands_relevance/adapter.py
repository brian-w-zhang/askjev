"""WANDS (Wayfair ANnotation DataSet, Chen et al. 2022): 480 real Wayfair search queries, 42,994 products,
233,448 query-product judgments by trained annotators: Exact (the product fully matches the query),
Partial (matches some of it, e.g. right product type but wrong attribute), Irrelevant.

Templates:
- "wands.fit": Score (3 levels) "How well does the home-goods listing `product` fit the search `query`?",
  truth = the annotator label, balanced across the three labels, round-robin over queries.
- "wands.pairwise": Choice "Which listing should rank higher for the search `query`: `listing_a` or
  `listing_b`?" over an Exact and a non-Exact product for the same query (half Partial, half Irrelevant
  negatives). Position of the Exact one alternates. Products are disjoint from the fit set per query.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wands_relevance"
BASE = "https://github.com/wayfair/WANDS/raw/main/dataset/"
FILES = ("label.csv", "query.csv", "product.csv")
TARGET_FIT = env_int("TARGET_WANDS_FIT", 2000)
TARGET_PAIR = env_int("TARGET_WANDS_PAIR", 2000)
LICENSE = "MIT"
NODE_FIT = "machine.search.relevance"
NODE_PAIR = "machine.search.reranking"

FIT_TEXT = "How well does the home-goods listing `product` fit the search `query`?"
FIT_LEVELS = [
    "The listing is a different kind of product from the one the search asks for",
    "The listing is the right kind of product but misses something the search specifies, such as the style, "
    "material, color, size or brand",
    "The listing is the kind of product the search asks for and matches everything the search specifies",
]
LABEL_LEVEL = {"Irrelevant": 0, "Partial": 1, "Exact": 2}
PAIR_TEXT = "Which listing should rank higher for the search `query`: `listing_a` or `listing_b`?"
PAIR_OPTIONS = {
    "listing_a": "The first listing matches the search better",
    "listing_b": "The second listing matches the search better",
}


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(s: str | None) -> str:
    return " ".join((s or "").split())


def _render(row: dict) -> str:
    parts = [f"Name: {_clean(row['product_name'])}"]
    if row.get("product_class"):
        parts.append(f"Type: {_clean(row['product_class'])}")
    if row.get("category hierarchy"):
        parts.append(f"Category: {_clean(row['category hierarchy'])}")
    desc = _clean(row.get("product_description"))
    if desc:
        parts.append(f"Description: {desc[:600]}{'...' if len(desc) > 600 else ''}")
    feats = [f.strip() for f in (row.get("product_features") or "").split("|") if f.strip()]
    if feats:
        ft = "; ".join(" ".join(f.replace(" : ", ": ").split()) for f in feats)
        parts.append(f"Features: {ft[:500]}{'...' if len(ft) > 500 else ''}")
    return "\n".join(parts)


def normalize(raw_dir: Path) -> Iterator[Question]:
    labels = pl.read_csv(raw_dir / "label.csv", separator="\t")
    queries = {qid: _clean(q) for qid, q, _ in pl.read_csv(raw_dir / "query.csv", separator="\t").rows()}
    prod = pl.read_csv(raw_dir / "product.csv", separator="\t", quote_char=None, infer_schema_length=0)
    products = {int(r["product_id"]): r for r in prod.iter_rows(named=True) if _clean(r["product_name"])}

    by_q: dict[int, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for _, qid, pid, lab in labels.rows():
        if pid in products and queries.get(qid):
            by_q[qid][lab].append(pid)
    qids = sorted(by_q)
    for q in qids:
        for lab in by_q[q]:
            by_q[q][lab] = hash_order(by_q[q][lab], lambda p: p, f"wands.{q}.{lab}")
    used: dict[int, set[int]] = defaultdict(set)

    def take(q: int, lab: str) -> int | None:
        for p in by_q[q][lab]:
            if p not in used[q]:
                used[q].add(p)
                return p
        return None

    # Pairs first (Exact products are the scarce resource), round-robin over queries.
    pairs = []
    k = 0
    while len(pairs) < TARGET_PAIR:
        progressed = False
        for q in qids:
            if len(pairs) >= TARGET_PAIR:
                break
            neg_lab = "Partial" if k % 2 == 0 else "Irrelevant"
            if not by_q[q]["Exact"] or not [p for p in by_q[q][neg_lab] if p not in used[q]]:
                continue
            if not [p for p in by_q[q]["Exact"] if p not in used[q]]:
                continue
            good, bad = take(q, "Exact"), take(q, neg_lab)
            truth = "listing_a" if (k // 2) % 2 == 0 else "listing_b"
            pairs.append((q, good, bad, neg_lab, truth))
            k += 1
            progressed = True
        if not progressed:
            break

    fit = []
    per = TARGET_FIT // 3
    for lab in ("Irrelevant", "Partial", "Exact"):
        n = 0
        while n < per + (TARGET_FIT % 3 if lab == "Exact" else 0):
            progressed = False
            for q in qids:
                if n >= per + (TARGET_FIT % 3 if lab == "Exact" else 0):
                    break
                p = take(q, lab)
                if p is not None:
                    fit.append((q, p, lab))
                    n += 1
                    progressed = True
            if not progressed:
                break

    for q, good, bad, neg_lab, truth in pairs:
        a, b = (good, bad) if truth == "listing_a" else (bad, good)
        yield Question(
            text=PAIR_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=PAIR_OPTIONS,
            state={"query": queries[q], "listing_a": _render(products[a]), "listing_b": _render(products[b])},
            shape="rank",
            node_hint=NODE_PAIR,
            template_id="wands.pairwise",
            source_item_id=f"q{q}:{a}:{b}",
            license=LICENSE,
            truth=truth,
            meta={"query_id": q, "exact": good, "other": bad, "other_label": neg_lab},
        )
    for q, p, lab in fit:
        yield Question(
            text=FIT_TEXT,
            primitive="score",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=FIT_LEVELS,
            state={"query": queries[q], "product": _render(products[p])},
            shape="score",
            node_hint=NODE_FIT,
            template_id="wands.fit",
            source_item_id=f"q{q}:{p}",
            license=LICENSE,
            truth=LABEL_LEVEL[lab],
            meta={"query_id": q, "product_id": p, "label": lab},
        )
