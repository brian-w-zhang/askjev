"""How funny is a single word? (docs/13 experiment 6, the new part.)

Human data: Engelthaler & Hills 2018, "Humor norms for 4,997 English words" (Behavior Research Methods 50:1116-1124;
github.com/tomasengelthaler/HumorNorms, free for not-for-profit research): each word rated 1 (humorless) to 5
(humorous) by about 35 US adults. Only means and SDs are published, so the comparison is mean vs Jev's expected
level. 600 words sampled evenly across the range of mean funniness.
"""

from __future__ import annotations

import csv
import random
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "humor_words"
NODE = "world.society.languages.word.word_humor"
LICENSE = "Free for not-for-profit research (Engelthaler & Hills 2018 humor norms)"
URL = "https://raw.githubusercontent.com/tomasengelthaler/HumorNorms/master/humor_dataset.csv"
LEVELS = ["Not funny at all: an ordinary word with nothing amusing about it",
          "Barely funny: most people wouldn't notice anything amusing",
          "Somewhat funny: it might raise a small smile",
          "Funny: many people would find it amusing to say or hear",
          "Very funny: a word people giggle at just for how it sounds or what it means"]
N = 600


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "humor_dataset.csv").exists():
        urllib.request.urlretrieve(URL, raw_dir / "humor_dataset.csv")


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = sorted(csv.DictReader(open(raw_dir / "humor_dataset.csv")), key=lambda r: (float(r["mean"]), r["word"]))
    k = len(rows) / N
    rng = random.Random(2018)
    picks = [rows[min(len(rows) - 1, int(i * k + rng.random() * k))] for i in range(N)]
    for r in picks:
        yield Question(
            text=f'How funny is the word "{r["word"]}" on its own?', primitive="score", hemisphere="world",
            kind="perception", origin="dataset", source=NAME, options=LEVELS, node_hint=NODE, license=LICENSE,
            source_item_id=r["word"],
            meta={"experiment": "humor_words", "human_mean": float(r["mean"]), "human_sd": float(r["sd"]),
                  "human_n": int(r["n"]), "scale": "1 humorless - 5 humorous"})
