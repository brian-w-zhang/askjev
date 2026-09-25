"""CoLA (Corpus of Linguistic Acceptability; Warstadt et al. 2019, GLUE): English sentences taken from
linguistics publications, each marked acceptable or unacceptable by the linguists who wrote them.

Template "cola.grammatical": Noul "Is `sentence` grammatical English?" Truth = acceptable. Train +
validation (in-domain) pooled; balanced 50/50, exact dedup, salted hash order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "cola_grammar"
BASE = "https://huggingface.co/api/datasets/nyu-mll/glue/parquet/cola/"
SPLITS = ("train", "validation")
TARGET = env_int("TARGET_COLA_GRAMMAR", 2000)
LICENSE = "CoLA terms: sentences from published linguistics literature, released for research (GLUE)"
TEXT = "Is `sentence` grammatical English?"
CRITERIA = {
    "true": "A native speaker would accept it as a well-formed English sentence, even if its meaning is odd",
    "false": "A native speaker would reject it as ill-formed: wrong word order, agreement, argument "
    "structure or a word that cannot be used that way",
}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}{split}/0.parquet", follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[str, str]]] = {True: [], False: []}
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for sent, label, idx in df.select("sentence", "label", "idx").iter_rows():
            s = " ".join(sent.split())
            if len(s.split()) < 3 or s.lower() in seen:
                continue
            seen.add(s.lower())
            pools[label == 1].append((f"{split}:{idx}", s))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += [(label, x) for x in hash_order(pools[label], lambda x: x[0], f"cola.{label}")[:k]]
    picked.sort(key=lambda x: (x[1][0].split(":")[0], int(x[1][0].split(":")[1])))

    for label, (sid, s) in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"sentence": s},
            shape="detect",
            node_hint="machine.documents",
            template_id="cola.grammatical",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"label_raw": int(label)},
        )
