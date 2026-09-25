"""Twitter Financial News Sentiment (zeroshot/twitter-financial-news-sentiment): 11,932 English
finance-news tweets annotated bearish / bullish / neutral for the market or stock they mention.

Template "fin_tweet.market_signal": Choice "Is `post` a bearish, bullish or neutral signal for the stock or
market it mentions?" Truth = the dataset label. Train + validation pooled, t.co links removed, exact
dedup, balanced to one third per label in salted hash order.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "fin_tweet_sentiment"
BASE = "https://huggingface.co/api/datasets/zeroshot/twitter-financial-news-sentiment/parquet/default/"
SPLITS = ("train", "validation")
TARGET = env_int("TARGET_FIN_TWEET_SENTIMENT", 2500)
LICENSE = "MIT"
TEXT = "Is `post` a bearish, bullish or neutral signal for the stock or market it mentions?"
OPTIONS = {
    "bearish": "It points to falling prices, weaker demand or worse prospects (a downgrade, a miss, a cut, a loss)",
    "bullish": "It points to rising prices, stronger demand or better prospects (an upgrade, a beat, a raise, a win)",
    "neutral": "It reports news or data with no clear direction for the price",
}
LABELS = {0: "bearish", 1: "bullish", 2: "neutral"}
URL_RE = re.compile(r"https?://\S+")
POLITICAL = re.compile(r"\b(trump\w*|biden|obama|pelosi|mcconnell|democrat\w*|republican\w*|gop|election\w*|"
                       r"abortion|gun control|immigra\w*|impeach\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}{split}/0.parquet", follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list[tuple[str, str]]] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, text, label in df.select("row", "text", "label").iter_rows():
            post = " ".join(URL_RE.sub("", text).split())
            if len(post) < 20 or post.lower() in seen:
                continue
            seen.add(post.lower())
            pools[LABELS[label]].append((f"{split}:{row}", post))

    per = TARGET // 3
    picked = []
    for i, lab in enumerate(OPTIONS):
        k = per + (1 if i < TARGET - 3 * per else 0)
        picked += [(lab, x) for x in hash_order(pools[lab], lambda x: x[0], f"fin_tweet.{lab}")[:k]]
    picked.sort(key=lambda x: (x[1][0].split(":")[0], int(x[1][0].split(":")[1])))

    for lab, (sid, post) in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"post": post[:1500]},
            shape="classify",
            node_hint="machine.commerce.demand_signals",
            template_id="fin_tweet.market_signal",
            source_item_id=sid,
            license=LICENSE,
            truth=lab,
            meta={"label_raw": lab, **({"flags": ["political"]} if POLITICAL.search(post) else {})},
        )
