"""PAWS (Zhang, Baldridge & He 2019, Google): Paraphrase Adversaries from Word Scrambling. Wikipedia
sentence pairs with high word overlap, built by word swapping and back-translation, human-labelled as
paraphrase or not. labeled_final test split (8,000 pairs).

Template "paws.same_meaning" (Noul, node documents.entity_resolution, the node for deciding whether two
records say the same thing): do the two sentences mean the same thing. Truth = label (1 = paraphrase).
Balanced 50/50, salted hash order. The release's tokenised spacing (" , ", " 's") is undone.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "paws_paraphrase"
URL = "https://huggingface.co/api/datasets/google-research-datasets/paws/parquet/labeled_final/test/0.parquet"
TARGET = env_int("TARGET_PAWS_PARAPHRASE", 2500)
LICENSE = "PAWS license (free use for any purpose; attribution to Google LLC requested)"
TEXT = "Do `sentence_a` and `sentence_b` mean the same thing?"
CRITERIA = {
    "true": "Both sentences state the same facts, even if the wording or word order differs",
    "false": "The sentences state different facts, for example because who did what to whom or which "
    "detail belongs to which entity changed",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def detok(s: str) -> str:
    s = " ".join(s.split())
    s = re.sub(r" ([,.;:!?%)\]])", r"\1", s)
    s = re.sub(r"([(\[]) ", r"\1", s)
    s = re.sub(r" (['’](?:s|re|ve|d|ll|m|t)\b)", r"\1", s)
    s = re.sub(r" n't\b", "n't", s)
    s = re.sub(r"(\w) - (\w)", r"\1-\2", s)  # hyphenated words were split as "Jean - Luc"
    s = re.sub(r"`` ?| ?''", '"', s)
    return s


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet")
    pools = {True: [], False: []}
    seen = set()
    for pid, s1, s2, label in df.select("id", "sentence1", "sentence2", "label").iter_rows():
        a, b = detok(s1), detok(s2)
        if a == b or (a, b) in seen or len(a) < 20:
            continue
        seen.add((a, b))
        pools[label == 1].append((pid, a, b))
    picked = []
    for lab in (True, False):
        k = TARGET // 2 if lab else TARGET - TARGET // 2
        picked += [(lab, x) for x in hash_order(pools[lab], lambda x: x[0], f"paws.{lab}")[:k]]
    picked.sort(key=lambda x: x[1][0])
    for lab, (pid, a, b) in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"sentence_a": a, "sentence_b": b},
            shape="verify",
            node_hint="machine.documents.entity_resolution",
            template_id="paws.same_meaning",
            source_item_id=f"test:{pid}",
            license=LICENSE,
            truth=lab,
            meta={"split": "test", "label_raw": int(lab)},
        )
