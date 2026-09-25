"""GoEmotions (Demszky et al. 2020, Google): 58k Reddit comments labelled by raters with 27 emotions plus
neutral. The "simplified" config keeps only labels that at least two of the (3-5) raters chose.

Template "goemotions.gratitude": Noul "Does `comment` express gratitude?" Truth = gratitude is among the
comment's labels. Gratitude is the category raters agreed on most, so the label is clean. Half of the
negatives are other warm comments (admiration, approval, joy, love, caring, optimism, amusement) so
"positive" alone does not decide it; the other half are any other non-gratitude comments. Train split,
balanced 50/50, salted hash order. The existing `emotion` source covers the 6-way emotion template.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "goemotions_gratitude"
URL = "https://huggingface.co/api/datasets/google-research-datasets/go_emotions/parquet/simplified/train/0.parquet"
TARGET = env_int("TARGET_GOEMOTIONS_GRATITUDE", 2000)
LICENSE = "Apache-2.0"
TEXT = "Does `comment` express gratitude?"
CRITERIA = {
    "true": "The writer thanks someone or says they are grateful or appreciative for something done or given",
    "false": "The comment expresses no thanks or gratitude, even if it is friendly or positive",
}
GRATITUDE = 15
WARM = {0, 1, 4, 5, 17, 18, 20}  # admiration, amusement, approval, caring, joy, love, optimism
NAMES = ["admiration", "amusement", "anger", "annoyance", "approval", "caring", "confusion", "curiosity",
         "desire", "disappointment", "disapproval", "disgust", "embarrassment", "excitement", "fear",
         "gratitude", "grief", "joy", "love", "nervousness", "optimism", "pride", "realization", "relief",
         "remorse", "sadness", "surprise", "neutral"]
SENSITIVE = re.compile(r"\b(sex\w*|porn\w*|rape\w*|nude\w*|naked|dick|cock|pussy|tits|boobs|hooker\w*|prostitut\w*|masturbat\w*|"
                       r"suicid\w*|kill (my|your)sel(f|ves)|kms|kys|self[- ]harm)\b", re.I)
POLITICAL = re.compile(r"\b(trump\w*|obama|hillary|clinton|biden|bernie|sanders|democrat\w*|republican\w*|"
                       r"gop|liberal\w*|conservative\w*|election\w*|abortion\w*|immigra\w*|gun control|"
                       r"maga|brexit)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pos, warm, other = [], [], []
    seen: set[str] = set()
    df = pl.read_parquet(raw_dir / "train.parquet")
    for text, labels, cid in df.select("text", "labels", "id").iter_rows():
        t = " ".join(text.split())
        if len(t.split()) < 4 or t.lower() in seen:
            continue
        seen.add(t.lower())
        item = (cid, t, [NAMES[i] for i in labels])
        if GRATITUDE in labels:
            pos.append(item)
        elif set(labels) & WARM:
            warm.append(item)
        else:
            other.append(item)

    n_pos = TARGET // 2
    n_warm = (TARGET - n_pos) // 2
    picked = [(True, x) for x in hash_order(pos, lambda x: x[0], "goemotions.pos")[:n_pos]]
    picked += [(False, x) for x in hash_order(warm, lambda x: x[0], "goemotions.warm")[:n_warm]]
    picked += [(False, x) for x in hash_order(other, lambda x: x[0], "goemotions.other")[:TARGET - n_pos - n_warm]]
    picked.sort(key=lambda x: x[1][0])

    for label, (cid, t, names) in picked:
        flags = (["sensitive"] if SENSITIVE.search(t) else []) + (["political"] if POLITICAL.search(t) else [])
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"comment": t[:1500]},
            shape="detect",
            node_hint="machine.research.qualitative_coding",
            template_id="goemotions.gratitude",
            source_item_id=f"train:{cid}",
            license=LICENSE,
            truth=label,
            meta={"labels": names, **({"flags": flags} if flags else {})},
        )
