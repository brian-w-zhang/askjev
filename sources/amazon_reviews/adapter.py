"""Multilingual Amazon Reviews Corpus (Keung et al. 2020), English test split via the MTEB mirror:
product reviews (title + body) with the reviewer's own 1-5 star rating.

Template "amazon.satisfaction": one Score per review over 5 concrete satisfaction situations,
truth = stars - 1. Balanced 40 per star, seeded, reviews of 40-1,500 chars.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order, top_up

NAME = "amazon_reviews"
URL = "https://huggingface.co/api/datasets/mteb/amazon_reviews_multi/parquet/en/test/0.parquet"
TARGET_V1 = 200  # the original seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_AMAZON_REVIEWS", TARGET_V1)  # Phase 6: 4,000
EXTRA = env_int("EXTRA_AMAZON_REVIEWS", 0)  # secondary template size; Phase 6: 1,500
SEED = 2020
LICENSE = "Amazon MARC license (non-commercial research)"
TEXT = "How satisfied is the reviewer in `review`?"
LEVELS = [
    "The reviewer considers the purchase a failure and warns others away from it",
    "The reviewer is let down: the product fell short in ways that matter to them",
    "The reviewer is torn: the product has real upsides and real downsides for them",
    "The reviewer is pleased with the product, with a minor reservation",
    "The reviewer is delighted and recommends it without reservation",
]

TOPIC_TEXT = "What is the main topic of complaint or praise in `review`?"
TOPIC_OPTIONS = {
    "quality": "How well the product works, how it is made, or how long it lasts",
    "price": "What the product cost or whether it was worth the money",
    "shipping": "Delivery, arrival time, packaging, or the item arriving damaged or missing",
    "fit_size": "Size, fit, or dimensions compared with what was expected",
    "customer_service": "Dealings with the seller or support: returns, refunds, replies",
    "other": "Something else",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "en_test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "en_test.parquet")
    pools: dict[int, list[tuple[str, str]]] = {k: [] for k in range(5)}
    seen: set[str] = set()
    for rid, text, label in df.select("id", "text", "label").iter_rows():
        review = "\n\n".join(" ".join(p.split()) for p in text.split("\n\n") if p.strip())
        key = review.lower()
        if len(review) < 40 or len(review) > 1500 or key in seen:
            continue
        seen.add(key)
        pools[label].append((rid, review))

    rng = random.Random(SEED)
    per1, per = min(TARGET, TARGET_V1) // 5, TARGET // 5
    items = []
    for lab in range(5):
        got = rng.sample(sorted(pools[lab]), per1)
        got += top_up(got, pools[lab], per - per1, lambda x: x[0], f"amazon.{lab}")  # Phase 6, prefix-stable
        items += [(lab, *x) for x in got]
    items.sort(key=lambda x: x[1])

    for lab, rid, review in items:
        yield Question(
            text=TEXT,
            primitive="score",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            state={"review": review},
            shape="score",
            node_hint="machine.commerce.review_insights",
            template_id="amazon.satisfaction",
            source_item_id=f"en_test:{rid}",
            license=LICENSE,
            truth=lab,
            meta={"stars": lab + 1, "split": "test", "lang": "en"},
        )

    # Secondary template: main topic of the review (no truth), first EXTRA sampled reviews in hash order.
    tid = "amazon.topic"
    for lab, rid, review in sorted(hash_order(items, lambda x: x[1], tid)[:EXTRA], key=lambda x: x[1]):
        yield Question(
            text=TOPIC_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=TOPIC_OPTIONS,
            state={"review": review},
            shape="classify",
            node_hint="machine.commerce.review_insights",
            template_id=tid,
            source_item_id=f"en_test:{rid}",
            license=LICENSE,
            truth=None,
            meta={"stars": lab + 1, "split": "test", "lang": "en"},
        )
