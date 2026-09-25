"""DBpedia-14 (Zhang, Zhao & LeCun 2015): Wikipedia abstracts of DBpedia entities in 14 non-overlapping classes.

Template "dbpedia14.entity_type": one Choice per abstract over the 14 classes, truth = the dataset label.
Test split, balanced across classes, salted-hash order.
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

NAME = "dbpedia14"
URL = "https://huggingface.co/api/datasets/fancyzhx/dbpedia_14/parquet/dbpedia_14/test/0.parquet"
LICENSE = "CC-BY-SA-3.0"
TARGET = env_int("TARGET_DBPEDIA14", 1500)
TEXT = "What kind of entity does `description` describe?"
# key -> description, in the dataset's ClassLabel order.
CLASSES: dict[str, str] = {
    "company": "A company, business or brand",
    "educational_institution": "A school, college or university",
    "artist": "A musician, painter, writer, actor or other artist",
    "athlete": "A sportsperson",
    "office_holder": "A politician, official or other holder of a public office",
    "means_of_transportation": "A ship, aircraft, car, locomotive or other vehicle or vehicle model",
    "building": "A building or other structure",
    "natural_place": "A mountain, river, lake, island or other natural feature",
    "village": "A village or small settlement",
    "animal": "An animal species or genus",
    "plant": "A plant species or genus",
    "album": "A music album",
    "film": "A film",
    "written_work": "A book, periodical or other written work",
}
LABELS = list(CLASSES)
POLITICAL = re.compile(
    r"\b(abortion|gun control|immigra\w*|same.sex marriage|gay marriage|trump|obama|biden|putin)\b", re.I
)
SENSITIVE = re.compile(r"\b(porn\w*|erotic\w*|sexual\w*|suicid\w*|rape\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=180)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet").with_row_index("row")
    seen: set[str] = set()
    pools: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for row, label, title, content in df.select("row", "label", "title", "content").iter_rows():
        t = " ".join(content.split())
        if len(t) < 40 or t.lower() in seen:
            continue
        seen.add(t.lower())
        pools[LABELS[label]].append((row, title.strip(), t))

    per = TARGET // len(LABELS)
    picked = []
    for i, lab in enumerate(LABELS):
        k = per + (1 if i < TARGET - per * len(LABELS) else 0)
        picked += [(*x, lab) for x in hash_order(pools[lab], lambda x: x[0], "dbpedia14.entity_type")[:k]]

    for row, title, t, lab in sorted(picked):
        flags = (["political"] if POLITICAL.search(t) else []) + (["sensitive"] if SENSITIVE.search(t) else [])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CLASSES,
            state={"description": t[:1500]},
            shape="classify",
            node_hint="machine.documents.taxonomy_classification",
            template_id="dbpedia14.entity_type",
            source_item_id=f"test:{row}",
            license=LICENSE,
            truth=lab,
            meta={"split": "test", "title": title, **({"flags": flags} if flags else {})},
        )
