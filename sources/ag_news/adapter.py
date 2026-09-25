"""AG News (Zhang, Zhao & LeCun 2015): news articles (title + lead) from AG's corpus in 4 sections.

Template "ag_news.section": one Choice per article over world / sports / business / sci_tech,
truth = the dataset label. Test split, balanced across the 4 classes, salted-hash order.
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

NAME = "ag_news"
URL = "https://huggingface.co/api/datasets/fancyzhx/ag_news/parquet/default/test/0.parquet"
LICENSE = "AG's corpus: non-commercial research use (Zhang et al. 2015)"
TARGET = env_int("TARGET_AG_NEWS", 1500)
TEXT = "Which section of a news site does `article` belong in?"
LABELS = ["world", "sports", "business", "sci_tech"]  # dataset ClassLabel order
SECTIONS = {
    "world": "International news, politics, conflicts and world affairs",
    "sports": "Sports results, athletes, teams and competitions",
    "business": "Companies, markets, the economy and personal finance",
    "sci_tech": "Science, technology, computing, the internet and space",
}
POLITICAL = re.compile(
    r"\b(elections?|electoral|campaign\w*|ballot\w*|republican\w*|democrat\w*|gop|bush|kerry|cheney|edwards|"
    r"nader|clinton|obama|trump|putin|abortion|gun control|immigra\w*|same.sex|gay marriage|stem.cell)\b",
    re.I,
)
SENSITIVE = re.compile(r"\b(porn\w*|sexual\w*|rape\w*|nude\w*|suicid\w*|beheaded|beheading)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = re.sub(r"(?<![&\w])#(\d+);", r"&#\1;", t)  # "#36;" is "&#36;" with the ampersand stripped
    t = html.unescape(html.unescape(t))
    t = re.sub(r"<[^>]+>", " ", t).replace("\\", " ")
    return " ".join(t.split())


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet").with_row_index("row")
    seen: set[str] = set()
    pools: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row, text, label in df.select("row", "text", "label").iter_rows():
        t = _clean(text)
        if len(t) < 40 or t.lower() in seen:
            continue
        seen.add(t.lower())
        pools[LABELS[label]].append((row, t))

    per = TARGET // len(LABELS)
    picked = []
    for i, lab in enumerate(LABELS):
        k = per + (1 if i < TARGET - per * len(LABELS) else 0)
        picked += [(row, t, lab) for row, t in hash_order(pools[lab], lambda x: x[0], "ag_news.section")[:k]]

    for row, t, lab in sorted(picked):
        flags = (["political"] if POLITICAL.search(t) else []) + (["sensitive"] if SENSITIVE.search(t) else [])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SECTIONS,
            state={"article": t[:1500]},
            shape="classify",
            node_hint="machine.documents.taxonomy_classification",
            template_id="ag_news.section",
            source_item_id=f"test:{row}",
            license=LICENSE,
            truth=lab,
            meta={"split": "test", **({"flags": flags} if flags else {})},
        )
