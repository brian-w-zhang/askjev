"""Amazon review helpfulness votes (McAuley et al. 2015/2016, SNAP "Amazon product data", 5-core files).

Each review carries `helpful: [yes_votes, total_votes]` from real shoppers answering "Was this review
helpful?". Template "amazon_helpful.helpful": Noul "Is `review` helpful to a shopper deciding whether to
buy the product?" on reviews with >= 10 votes. The shopper vote share is attached as HumanDist. Truth is
set only where the vote is clear (>= 85% helpful -> true, <= 40% -> false); mid-range reviews are not
sampled. Sample: all clear-unhelpful reviews up to 40% of the target, the rest clear-helpful, round-robin
over 7 product categories in salted hash order.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "amazon_helpful"
URL = "http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_{cat}_5.json.gz"
CATEGORIES = {
    "Cell_Phones_and_Accessories": "Cell phones and accessories",
    "Tools_and_Home_Improvement": "Tools and home improvement",
    "Toys_and_Games": "Toys and games",
    "Grocery_and_Gourmet_Food": "Grocery and gourmet food",
    "Office_Products": "Office products",
    "Baby": "Baby products",
    "Pet_Supplies": "Pet supplies",
}
TARGET = env_int("TARGET_AMAZON_HELPFUL", 2500)
MIN_VOTES = 10
HI, LO = 0.85, 0.40
LICENSE = "Research use (McAuley Amazon product data, SNAP)"
TEXT = "Is `review` helpful to a shopper deciding whether to buy the product?"
OPTIONS = {
    "true": "The review gives shoppers information that helps them decide",
    "false": "The review does not help shoppers decide",
}


def fetch(raw_dir: Path) -> None:
    with httpx.Client(follow_redirects=True, timeout=600) as client:
        for cat in CATEGORIES:
            out = raw_dir / f"reviews_{cat}_5.json.gz"
            if out.exists():
                continue
            r = client.get(URL.format(cat=cat))
            r.raise_for_status()
            out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[tuple[str, bool], list[dict]] = {}
    seen: set[str] = set()
    for cat in CATEGORIES:
        for line in gzip.open(raw_dir / f"reviews_{cat}_5.json.gz"):
            r = json.loads(line)
            up, tot = r["helpful"]
            text = " ".join((r.get("reviewText") or "").split())
            if tot < MIN_VOTES or not (40 <= len(text) <= 1500) or up > tot:
                continue
            share = up / tot
            if LO < share < HI or text.lower() in seen:
                continue
            seen.add(text.lower())
            r["_text"], r["_cat"], r["_share"] = text, cat, share
            pools.setdefault((cat, share >= HI), []).append(r)

    key = lambda r: f"{r['reviewerID']}|{r['asin']}"  # noqa: E731
    picked: list[dict] = []
    for helpful, quota in ((False, int(TARGET * 0.4)), (True, None)):
        quota = quota if quota is not None else TARGET - len(picked)
        queues = [hash_order(pools.get((c, helpful), []), key, f"amazon_helpful|{c}|{helpful}") for c in CATEGORIES]
        cursor = [0] * len(queues)
        taken = 0
        while taken < quota:
            progressed = False
            for i, q in enumerate(queues):
                if taken >= quota:
                    break
                if cursor[i] < len(q):
                    picked.append(q[cursor[i]])
                    cursor[i] += 1
                    taken += 1
                    progressed = True
            if not progressed:
                break
    picked.sort(key=lambda r: (r["_cat"], key(r)))

    for r in picked:
        up, tot = r["helpful"]
        summary = " ".join((r.get("summary") or "").split())
        state = {"product_category": CATEGORIES[r["_cat"]], "rating": f"{int(r['overall'])} out of 5 stars"}
        if summary:
            state["review_title"] = summary
        state["review"] = r["_text"]
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state=state,
            shape="classify",
            node_hint="machine.commerce.review_insights",
            template_id="amazon_helpful.helpful",
            source_item_id=f"{r['_cat']}:{key(r)}",
            license=LICENSE,
            truth=r["_share"] >= HI,
            human=[
                HumanDist(
                    population="Amazon shoppers who voted on the review",
                    distribution={"true": round(up / tot, 4), "false": round(1 - up / tot, 4)},
                    n=tot,
                    source="Amazon 'Was this review helpful?' votes (McAuley SNAP 5-core)",
                )
            ],
            meta={"category": r["_cat"], "asin": r["asin"], "helpful_votes": up, "total_votes": tot},
        )
