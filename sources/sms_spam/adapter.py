"""UCI SMS Spam Collection (Almeida & Hidalgo 2011): 5,574 SMS messages labelled ham/spam.

Template "sms.spam": one Noul per message, truth = spam. Balanced to ~40% spam, seeded.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question

NAME = "sms_spam"
URL = "https://huggingface.co/api/datasets/ucirvine/sms_spam/parquet/plain_text/train/0.parquet"
TARGET = 700
SPAM_SHARE = 0.40
SEED = 228
LICENSE = "CC-BY-4.0"
TEXT = "Is `message` spam?"
SEXUAL = re.compile(
    r"\b(sex|sexual\w*|sexy|porn\w*|nude\w*|naked|erotic\w*|horny|xxx|slut\w*|dick|cock|pussy|shag\w*|"
    r"orgasm\w*|masturbat\w*)\b",
    re.I,
)
CRITERIA = {
    "true": "Unsolicited promotional, scam or phishing text",
    "false": "A normal personal or transactional message",
}


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
    pools: dict[int, list[tuple[int, str]]] = {0: [], 1: []}
    for row, sms, label in df.select("row", "sms", "label").iter_rows():
        text = " ".join(sms.split())
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        pools[label].append((row, text))

    rng = random.Random(SEED)
    n_spam = round(TARGET * SPAM_SHARE)
    spam = rng.sample(pools[1], n_spam)
    ham = rng.sample(pools[0], TARGET - n_spam)
    items = [(r, t, True) for r, t in spam] + [(r, t, False) for r, t in ham]
    items.sort(key=lambda x: x[0])

    for row, text, is_spam in items:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"message": text[:1500]},
            shape="detect",
            node_hint="machine.trust_safety.spam_phishing",
            template_id="sms.spam",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=is_spam,
            meta={
                "label_raw": "spam" if is_spam else "ham",
                **({"flags": ["sensitive"]} if SEXUAL.search(text) else {}),
            },
        )
