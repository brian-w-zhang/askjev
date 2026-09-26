"""Twitter US Airline Sentiment (Figure Eight / CrowdFlower "Data for Everyone", February 2015): 14,640
tweets to six US airlines, crowd-labelled for sentiment and, for negative tweets, the reason.

Template "airline_complaints.reason" (Choice, classify): what is the customer complaining about? Negative
tweets only, over the nine concrete reasons (the "Can't Tell" reason is dropped), with the crowd's
reason confidence >= 0.66. Truth = negativereason. The release's global "Cancel" -> "Cancelled Flight" and
"late" -> "Late Flight" text substitution (which leaks the label) is undone. Stratified seeded round-robin over reasons.
"""

from __future__ import annotations

import html
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int

NAME = "airline_complaints"
URL = "https://huggingface.co/api/datasets/osanseviero/twitter-airline-sentiment/parquet/default/train/0.parquet"
LICENSE = "CC-BY-NC-SA-4.0"
TARGET = env_int("TARGET_AIRLINE_COMPLAINTS", 2000)
MIN_CONF = 0.66
SEED = 2015
TEXT = "What is the customer complaining about in `tweet` to an airline?"
REASONS = {
    "Customer Service Issue": ("customer_service", "Rude, slow or unhelpful staff, phone lines or replies"),
    "Late Flight": ("late_flight", "A delayed flight"),
    "Cancelled Flight": ("cancelled_flight", "A cancelled flight"),
    "Lost Luggage": ("lost_luggage", "Luggage that is lost or has not arrived"),
    "Damaged Luggage": ("damaged_luggage", "Luggage that arrived damaged"),
    "Bad Flight": ("bad_flight", "A bad experience on board: the seat, food, wifi, cleanliness or entertainment"),
    "Flight Booking Problems": ("booking_problem", "Trouble booking, changing or paying for a ticket"),
    "Flight Attendant Complaints": ("flight_attendant", "The behaviour of flight attendants or crew"),
    "longlines": ("long_lines", "Long lines or waits at the airport"),
}
OPTIONS = {k: d for k, d in REASONS.values()}
SLURS = re.compile(r"\b(n[i1]gg(er|a|ers|as)|fag(got)?s?|retards?|kikes?|spics?|chinks?|trann(y|ies))\b", re.I)


def _repair(text: str) -> str:
    # The public release globally replaced "Cancel" with "Cancelled Flight" and "late" with "Late Flight"
    # ("Cancelled Flightled", "Late Flightr"), which leaks the label; undo it.
    return html.unescape(text.replace("Cancelled Flight", "Cancel").replace("Late Flight", "late"))


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").filter(
        (pl.col("airline_sentiment") == "negative") & (pl.col("negativereason_confidence") >= MIN_CONF)
    )
    by_label: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for r in df.sort("tweet_id").iter_rows(named=True):
        if r["negativereason"] not in REASONS:
            continue
        text = _repair((r["text"] or "").strip())
        norm = re.sub(r"\W+", " ", re.sub(r"^(@\w+\s*)+", "", text.lower())).strip()
        if len(norm.split()) < 4 or norm in seen or SLURS.search(text):
            continue
        seen.add(norm)
        by_label[REASONS[r["negativereason"]][0]].append(r)
    rng = random.Random(SEED)
    labels = sorted(by_label)
    for lab in labels:
        rng.shuffle(by_label[lab])
    picked, cursor = [], {lab: 0 for lab in labels}
    while len(picked) < TARGET:
        progressed = False
        for lab in labels:
            if len(picked) < TARGET and cursor[lab] < len(by_label[lab]):
                picked.append((lab, by_label[lab][cursor[lab]]))
                cursor[lab] += 1
                progressed = True
        if not progressed:
            break
    for lab, r in picked:
        yield Question(
            text=TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME, options=OPTIONS,
            state={"tweet": _repair(r["text"].strip())[:1500]}, shape="classify", node_hint="machine.support.intent_topic",
            template_id="airline_complaints.reason", source_item_id=str(r["tweet_id"]), license=LICENSE, truth=lab,
            meta={"airline": r["airline"], "reason_confidence": r["negativereason_confidence"]},
        )
