"""Phishing Email Dataset (zefang-liu on HF): 18,650 emails labelled "Phishing Email" or "Safe Email",
pooled from public corpora (Enron, SpamAssassin, Ling-Spam, Nazario phishing...).

The "Phishing Email" class is mostly bulk spam (pharma, stock pumps, adult, software offers) plus real
phishing and scams, so the question asks about all three rather than phishing alone.
Template "phishing_email.phishing" (Noul): truth = the label, ~40% positive. Emails are whitespace-collapsed,
deduplicated, and truncated to 1,500 chars.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "phishing_email"
URL = "https://huggingface.co/api/datasets/zefang-liu/phishing-email-dataset/parquet/default/train/0.parquet"
LICENSE = "LGPL-3.0"
NODE = "machine.trust_safety.spam_phishing"
TARGET = env_int("TARGET_PHISHING_EMAIL", 2500)
POS_SHARE = 0.40
MAX_CHARS = 1500

TEXT = "Is `email` spam, a scam or a phishing attempt?"
OPTIONS = {
    "true": "Unsolicited bulk advertising, a scam, or an attempt to trick the reader into giving up "
    "credentials, money or personal details",
    "false": "A legitimate personal, work, mailing-list or transactional email",
}
SEXUAL = re.compile(
    r"\b(sex|sexy|sexual\w*|porn\w*|nude\w*|naked|erotic\w*|horny|xxx|slut\w*|dick|cock|pussy|penis|"
    r"orgasm\w*|masturbat\w*|viagra|cialis|erection\w*|voyeur\w*|panty|panties|fuck\w*)\b",
    re.I,
)
MINOR = re.compile(r"\b(teen\w*|underage|lolita|schoolgirls?|child\w*|kids?)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet")
    seen: set[str] = set()
    pools: dict[bool, list[tuple[int, str, int]]] = {True: [], False: []}
    for idx, text, label in df.select("Unnamed: 0", "Email Text", "Email Type").iter_rows():
        t = re.sub(r"[ \t]+", " ", (text or "")).strip()
        t = re.sub(r"\s*\n\s*(\n\s*)+", "\n\n", t)
        key = " ".join(t[:MAX_CHARS].lower().split())  # truncated text is what Jev sees: dedup on it
        if len(key) < 40 or key == "empty" or key in seen or label not in ("Phishing Email", "Safe Email"):
            continue
        seen.add(key)
        is_pos = label == "Phishing Email"
        if is_pos and SEXUAL.search(t) and MINOR.search(t):
            continue  # sexual spam mentioning minors: dropped outright
        pools[is_pos].append((idx, t[:MAX_CHARS], len(t)))

    n_pos = min(len(pools[True]), round(TARGET * POS_SHARE))
    picked = [(x, True) for x in hash_order(pools[True], lambda x: x[0], "phish.pos")[:n_pos]]
    picked += [(x, False) for x in hash_order(pools[False], lambda x: x[0], "phish.neg")[: TARGET - n_pos]]
    for (idx, t, full_len), truth in sorted(picked, key=lambda x: x[0][0]):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"email": t},
            shape="detect",
            node_hint=NODE,
            template_id="phishing_email.phishing",
            source_item_id=f"train:{idx}",
            license=LICENSE,
            truth=truth,
            meta={
                "label_raw": "Phishing Email" if truth else "Safe Email",
                **({"truncated_from": full_len} if full_len > MAX_CHARS else {}),
                **({"flags": ["sensitive"]} if SEXUAL.search(t) else {}),
            },
        )
