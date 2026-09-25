"""Twitter Financial News Topic (HF zeroshot/twitter-financial-news-topic): 21,107 English finance
tweets from news and market accounts, annotated with one of 20 topics.

Template "fin_news_topic.topic" (Choice, node machine.finance; no finance leaf fits news-topic
tagging, so placement walks down from the parent): what is the post about, over the 20 topics. Truth =
label. train + validation pooled, round-robin over topics in salted hash order (~132 per topic at
2,500; gold_metals_materials and ipo have only 68 and 54 unique posts). Posts in the Politics topic, or naming politicians / contested issues, are flagged "political".
"""

from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "fin_news_topic"
BASE = "https://huggingface.co/api/datasets/zeroshot/twitter-financial-news-topic/parquet/default/{split}/0.parquet"
SPLITS = ("train", "validation")
TARGET = env_int("TARGET_FIN_NEWS_TOPIC", 2500)
LICENSE = "MIT"
TEXT = "What is the financial news post in `post` about?"
TOPICS = [  # dataset label order -> (key, description)
    ("analyst_update", "Analyst ratings, upgrades, downgrades and price targets"),
    ("central_banks", "The Fed and other central banks: rates, policy, officials' remarks"),
    ("company_product_news", "News about a company, its products, deals or operations"),
    ("treasuries_corporate_debt", "Government bonds, yields and corporate debt"),
    ("dividend", "Dividend declarations, raises, cuts and yields"),
    ("earnings", "Earnings results, revenue, guidance and earnings calls"),
    ("energy_oil", "Oil, gas and energy markets"),
    ("financials", "Banks, insurers and other financial-sector companies"),
    ("currencies", "Currencies and exchange rates, including crypto"),
    ("general_news_opinion", "General news or opinion not tied to one market topic"),
    ("gold_metals_materials", "Gold, metals and other raw materials"),
    ("ipo", "Initial public offerings and listings"),
    ("legal_regulation", "Lawsuits, regulators, fines and rules"),
    ("mergers_investments", "Mergers, acquisitions and investments in companies"),
    ("macro", "Macroeconomic data such as inflation, jobs and GDP"),
    ("markets", "Overall market moves and indexes"),
    ("politics", "Politics, governments and elections"),
    ("personnel_change", "Executive hires, departures and appointments"),
    ("stock_commentary", "Commentary, ideas or opinions about particular stocks"),
    ("stock_movement", "A particular stock's price moving up or down"),
]
OPTIONS = dict(TOPICS)
POLITICAL = re.compile(
    r"\b(trump|biden|harris|pelosi|mcconnell|schumer|sanders|warren|aoc|desantis|obama|putin|xi jinping|"
    r"zelensky|boris johnson|macron|modi|bolsonaro|republican\w*|democrat\w*|gop|election\w*|impeach\w*|"
    r"abortion|gun control|immigra\w*|brexit)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_label: dict[int, list] = defaultdict(list)
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, text, label in df.select("row", "text", "label").iter_rows():
            post = " ".join(html.unescape(text).split())
            key = re.sub(r"https?://\S+", "", post).lower().strip()
            if len(key) < 15 or key in seen:
                continue
            seen.add(key)
            by_label[label].append((f"{split}:{row}", split, post))
    assert set(by_label) == set(range(len(TOPICS))), sorted(by_label)
    orders = {l: hash_order(v, lambda x: x[0], f"finnews.{l}") for l, v in by_label.items()}
    picked, i = [], 0
    while len(picked) < TARGET and any(i < len(v) for v in orders.values()):
        for l in sorted(orders):
            if len(picked) < TARGET and i < len(orders[l]):
                picked.append((l, orders[l][i]))
        i += 1
    picked.sort(key=lambda x: (SPLITS.index(x[1][1]), int(x[1][0].split(":")[1])))
    for label, (sid, split, post) in picked:
        key = TOPICS[label][0]
        political = key == "politics" or POLITICAL.search(post)
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"post": post[:1500]},
            shape="classify",
            node_hint="machine.finance",
            template_id="fin_news_topic.topic",
            source_item_id=sid,
            license=LICENSE,
            truth=key,
            meta={"split": split, "label_raw": label, **({"flags": ["political"]} if political else {})},
        )
