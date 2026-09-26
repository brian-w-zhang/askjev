"""SemEval-2014 Task 4 aspect-based sentiment (Pontiki et al. 2014): sentences from restaurant reviews
(Ganu et al. 2009) and laptop reviews, with every aspect term the reviewer mentions annotated for polarity
(positive / negative / neutral / conflict) by trained annotators.

Template "absa.aspect_polarity" (Choice, node commerce.review_insights): how does the reviewer feel about
`aspect` in `review_sentence`. Truth = the annotated polarity ("conflict" shown as "mixed"). Pool: the
restaurant and laptop train + validation splits of the jakartaresearch HF export. One aspect per
sentence, polarity quotas (positive capped so it isn't the majority), salted hash order.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "absa_aspects"
BASE = "https://huggingface.co/api/datasets/jakartaresearch/semeval-absa/parquet"
FILES = [(d, s) for d in ("restaurant", "laptop") for s in ("train", "validation")]
TARGET = env_int("TARGET_ABSA_ASPECTS", 1200)
LICENSE = "CC-BY-4.0 (HF export); SemEval-2014 Task 4 data, research use"
TEXT = "How does the reviewer feel about `aspect` in `review_sentence`?"
OPTIONS = {
    "positive": "The sentence praises or speaks well of this aspect",
    "negative": "The sentence criticizes or complains about this aspect",
    "neutral": "The sentence mentions this aspect without judging it",
    "mixed": "The sentence both praises and criticizes this aspect",
}
POL = {"positive": "positive", "negative": "negative", "neutral": "neutral", "conflict": "mixed"}
SHARE = {"mixed": 0.06, "neutral": 0.29, "negative": 0.325, "positive": 0.325}


def fetch(raw_dir: Path) -> None:
    for d, s in FILES:
        out = raw_dir / f"{d}_{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{d}/{s}/0.parquet", follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list] = defaultdict(list)
    seen = set()
    for d, s in FILES:
        df = pl.read_parquet(raw_dir / f"{d}_{s}.parquet")
        for sid, text, asp in df.select("id", "text", "aspects").iter_rows():
            text = " ".join(text.split())
            if len(text) < 15 or text.lower() in seen:
                continue
            seen.add(text.lower())
            for j, (term, pol) in enumerate(zip(asp["term"], asp["polarity"])):
                if pol in POL and term.strip():
                    pools[POL[pol]].append((f"{d}:{s}:{sid}:{j}", f"{d}:{sid}", d, text, term.strip()))
    used: set[str] = set()
    alloc = {k: int(TARGET * v) for k, v in SHARE.items()}
    alloc["positive"] += TARGET - sum(alloc.values())
    for lab in ["mixed", "neutral", "negative", "positive"]:  # scarcest first
        n = 0
        for iid, sent_key, domain, text, term in hash_order(pools[lab], lambda x: x[0], f"absa|{lab}"):
            if n >= alloc[lab]:
                break
            if sent_key in used:
                continue
            used.add(sent_key)
            n += 1
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OPTIONS,
                state={"review_sentence": text[:1000], "aspect": term},
                shape="classify",
                node_hint="machine.commerce.review_insights",
                template_id="absa.aspect_polarity",
                source_item_id=iid,
                license=LICENSE,
                truth=lab,
                meta={"domain": domain},
            )
