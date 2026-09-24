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
from askjev.sampling import env_int, hash_order, top_up

NAME = "sms_spam"
URL = "https://huggingface.co/api/datasets/ucirvine/sms_spam/parquet/plain_text/train/0.parquet"
TARGET_V1 = 700  # the original seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_SMS_SPAM", TARGET_V1)  # Phase 6: 3,000
EXTRA = env_int("EXTRA_SMS_SPAM", 0)  # secondary template size; Phase 6: 1,500
SPAM_SHARE = 0.40
SEED = 228
LICENSE = "CC-BY-4.0"
TEXT = "Is `message` spam?"
CTA_TEXT = "Does `message` ask the recipient to click a link or call a number?"
CTA = {
    "true": "It asks the reader to open a link, visit a web address, call or text a number, or reply to a short code",
    "false": "It contains no such request",
}
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
    n_spam = round(min(TARGET, TARGET_V1) * SPAM_SHARE)
    spam = rng.sample(pools[1], n_spam)
    ham = rng.sample(pools[0], min(TARGET, TARGET_V1) - n_spam)
    # Phase 6 top-up (hash order, prefix-stable): spam up to SPAM_SHARE of TARGET while it lasts, then ham.
    extra = max(0, TARGET - TARGET_V1)
    more_spam = top_up(spam, pools[1], min(extra, round(TARGET * SPAM_SHARE) - len(spam)), lambda x: x[0], "sms.spam")
    spam += more_spam
    ham += top_up(ham, pools[0], extra - len(more_spam), lambda x: x[0], "sms.ham")
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

    # Secondary template: call-to-action detection on the first EXTRA sampled messages (hash order).
    for row, text, is_spam in sorted(hash_order(items, lambda x: x[0], "sms.call_to_action")[:EXTRA]):
        yield Question(
            text=CTA_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CTA,
            state={"message": text[:1500]},
            shape="detect",
            node_hint="machine.trust_safety.spam_phishing",
            template_id="sms.call_to_action",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=None,
            meta={
                "label_raw": "spam" if is_spam else "ham",
                **({"flags": ["sensitive"]} if SEXUAL.search(text) else {}),
            },
        )
