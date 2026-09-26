"""STS Benchmark (Cer et al. 2017, SemEval STS 2012-2017 selection): English sentence pairs from news
headlines, image captions and forum posts, each scored 0-5 for semantic similarity as the mean of five
crowdworker ratings under the STS annotation guidelines.

Template "stsb.meaning_overlap" (Score, 6 levels = the STS guideline's own level descriptions, node
search.relevance): how close in meaning `sentence_b` is to `sentence_a`. Truth = the gold score rounded
to the nearest level (half up). Pool: train + validation + test (8,628 pairs, via the sentence-transformers
parquet export whose scores are the gold / 5). Balanced across the six levels, salted hash order.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "stsb_similarity"
BASE = "https://huggingface.co/api/datasets/sentence-transformers/stsb/parquet/default"
SPLITS = ["train", "validation", "test"]
TARGET = env_int("TARGET_STSB_SIMILARITY", 1000)
LICENSE = "STS Benchmark: each part keeps its source license (news, captions, forums; research use)"
TEXT = "How close in meaning is `sentence_b` to `sentence_a`?"
LEVELS = [
    "The two sentences are about different things",
    "The sentences are on the same topic but say different things",
    "The sentences share some details but are not saying the same thing",
    "The sentences roughly say the same thing, but an important detail differs or is missing from one of them",
    "The sentences say the same thing and differ only in minor, unimportant details",
    "The sentences say exactly the same thing",
]


def fetch(raw_dir: Path) -> None:
    for sp in SPLITS:
        out = raw_dir / f"{sp}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{sp}/0.parquet", follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[int, list] = defaultdict(list)
    seen = set()
    for sp in SPLITS:
        df = pl.read_parquet(raw_dir / f"{sp}.parquet")
        for i, (a, b, score) in enumerate(df.select("sentence1", "sentence2", "score").iter_rows()):
            a, b = " ".join(a.split()), " ".join(b.split())
            key = (a.lower(), b.lower())
            if a == b or key in seen or len(a) < 8 or len(b) < 8:
                continue
            seen.add(key)
            gold = score * 5
            level = min(5, int(gold + 0.5))
            pools[level].append((f"{sp}:{i}", a, b, round(gold, 2)))
    for lvl in range(6):
        per = TARGET // 6 + (1 if lvl < TARGET % 6 else 0)
        for sid, a, b, gold in hash_order(pools[lvl], lambda x: x[0], f"stsb|{lvl}")[:per]:
            yield Question(
                text=TEXT,
                primitive="score",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=LEVELS,
                state={"sentence_a": a[:700], "sentence_b": b[:700]},
                shape="score",
                node_hint="machine.search.relevance",
                template_id="stsb.meaning_overlap",
                source_item_id=sid,
                license=LICENSE,
                truth=lvl,
                meta={"gold_mean_0_5": gold},
            )
