"""Bitext customer-support dataset (Bitext 2023): 26,872 synthetic-but-curated customer messages to a retail
support assistant, each labelled with one of 27 intents, including `contact_human_agent`.

Template "human_escalation.wants_human": Noul "Is the customer in `message` asking to talk to a human agent?",
truth = intent is contact_human_agent. Negatives are drawn evenly from the other intents, except
`contact_customer_service` (asking how to reach customer service by phone/email: often a request for a person
too, so the label would be ambiguous). 45% positive. Bitext placeholders like {{Order Number}} become
"[order number]". Case-insensitive exact dedup; salted-hash order.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "human_escalation"
URL = ("https://huggingface.co/api/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset"
       "/parquet/default/train/0.parquet")
LICENSE = "CDLA-Sharing-1.0"
NODE = "machine.support.human_escalation"
TARGET = env_int("TARGET_HUMAN_ESCALATION", 1000)
POS_SHARE = 0.45
POS = "contact_human_agent"
SKIP = {"contact_customer_service"}
TEXT = "Is the customer in `message` asking to talk to a human agent?"
CRITERIA = {
    "true": "The customer asks to speak, chat or be connected with a person, live agent or operator",
    "false": "The customer asks about something else and does not ask for a person",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", lambda m: f"[{m.group(1).lower()}]", t or "")
    return " ".join(t.split())


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").with_row_index("row")
    seen: set[str] = set()
    pools: dict[str, list] = {}
    for row, text, intent, cat in df.select("row", "instruction", "intent", "category").iter_rows():
        t = _clean(text)
        if len(t) < 8 or t.lower() in seen or intent in SKIP:
            continue
        seen.add(t.lower())
        pools.setdefault(intent, []).append((row, t, intent, cat))
    n_pos = round(TARGET * POS_SHARE)
    picked = hash_order(pools[POS], lambda x: x[0], "bitext.human")[:n_pos]
    negs = sorted(k for k in pools if k != POS)
    n_neg = TARGET - n_pos
    for i, k in enumerate(negs):
        picked += hash_order(pools[k], lambda x: x[0], f"bitext.{k}")[: n_neg // len(negs) + (i < n_neg % len(negs))]
    for row, t, intent, cat in sorted(picked):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"message": t},
            shape="detect",
            node_hint=NODE,
            template_id="human_escalation.wants_human",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=intent == POS,
            meta={"intent": intent, "category": cat},
        )
