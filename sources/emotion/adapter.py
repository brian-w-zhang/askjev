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
from askjev.sampling import env_int, top_up

NAME = "emotion"
URL = "https://huggingface.co/api/datasets/dair-ai/emotion/parquet/split/train/0.parquet"
TARGET_V1 = 400  # the original seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_EMOTION", TARGET_V1)  # Phase 6: 2,500
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

    def split(total: int) -> list[int]:
        per, extra = divmod(total, len(LABELS))
        return [per + (1 if lab < extra else 0) for lab in range(len(LABELS))]

    rng = random.Random(SEED)
    items = []
    for lab, (n1, n) in enumerate(zip(split(min(TARGET, TARGET_V1)), split(TARGET))):
        got = rng.sample(pools[lab], n1)
        got += top_up(got, pools[lab], n - n1, lambda x: x[0], f"emotion.{lab}")  # Phase 6, prefix-stable
        items += [(row, text, lab) for row, text in got]
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
