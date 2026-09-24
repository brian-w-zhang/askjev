"""dair-ai/emotion (Saravia et al., EMNLP 2018): English tweets labelled with one of six emotions.

Template "emotion.primary": one Choice per tweet, truth = the dataset label. Balanced across the six
labels from the train split, seeded.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question

NAME = "emotion"
URL = "https://huggingface.co/api/datasets/dair-ai/emotion/parquet/split/train/0.parquet"
TARGET = 400
SEED = 2018
LICENSE = "other (dataset card: educational and research use only)"
TEXT = "Which emotion does `text` express most strongly?"
LABELS = ["sadness", "joy", "love", "anger", "fear", "surprise"]  # dataset label ids 0..5
OPTIONS = {
    "sadness": "Sad, down, hurt, lonely or disappointed",
    "joy": "Happy, pleased, content, excited or proud",
    "love": "Loving, affectionate, caring or tender toward someone or something",
    "anger": "Angry, irritated, resentful or annoyed",
    "fear": "Afraid, anxious, nervous or worried",
    "surprise": "Surprised, amazed, shocked or startled",
}
SEXUAL = re.compile(r"\b(sex|sexual\w*|sexy|porn\w*|horny|naked|nude\w*|erotic\w*|orgasm\w*)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|kill (my|him|her)self|self[- ]harm\w*|cutting myself)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").with_row_index("row")
    seen: set[str] = set()
    pools: dict[int, list[tuple[int, str]]] = {i: [] for i in range(len(LABELS))}
    for row, text, label in df.select("row", "text", "label").iter_rows():
        text = " ".join(text.split())
        if not text or text in seen:
            continue
        seen.add(text)
        pools[label].append((row, text))

    rng = random.Random(SEED)
    per = TARGET // len(LABELS)
    extra = TARGET - per * len(LABELS)
    items = []
    for lab in range(len(LABELS)):
        n = per + (1 if lab < extra else 0)
        items += [(row, text, lab) for row, text in rng.sample(pools[lab], n)]
    items.sort()

    for row, text, lab in items:
        flags = []
        if SEXUAL.search(text) or SELF_HARM.search(text):
            flags.append("sensitive")
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"text": text[:1500]},
            shape="classify",
            node_hint="machine.research.qualitative_coding",
            template_id="emotion.primary",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=LABELS[lab],
            meta={"split": "train", **({"flags": flags} if flags else {})},
        )
