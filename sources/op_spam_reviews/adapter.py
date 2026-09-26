"""Deceptive Opinion Spam corpus v1.4 (Ott et al. 2011, 2013): 1,600 reviews of 20 Chicago hotels. 800
truthful reviews (400 positive from TripAdvisor, 400 negative from Expedia, Hotels.com, Orbitz, Priceline,
TripAdvisor and Yelp) and 800 deceptive ones written by Mechanical Turk workers told to write a
convincing fake review of a hotel they had not stayed at. The labels hold by construction.

Template "op_spam.genuine_stay" (Noul, node commerce.review_abuse): was `review` written by a guest who
actually stayed at the hotel. Truth = truthful (true) vs deceptive (false). Stratified: equal counts in
each polarity x truthfulness cell, salted hash order.
"""

from __future__ import annotations

import io
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "op_spam_reviews"
URL = "https://myleott.com/op_spam_v1.4.zip"
TARGET = env_int("TARGET_OP_SPAM_REVIEWS", 800)
LICENSE = "CC-BY-NC-SA-3.0"
TEXT = "Was `review` written by a guest who actually stayed at the hotel?"
CRITERIA = {
    "true": "A real guest wrote the review about a stay they had",
    "false": "The review is fake: written by someone who never stayed there, to look like a real guest review",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "op_spam_v1.4.zip"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    cells: dict[tuple[str, bool], list] = defaultdict(list)
    with zipfile.ZipFile(raw_dir / "op_spam_v1.4.zip") as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".txt") or "/fold" not in name:
                continue
            parts = name.split("/")  # op_spam_v1.4/<polarity>_polarity/<class>_from_X/foldN/<file>
            polarity = parts[1].split("_")[0]
            truthful = parts[2].startswith("truthful")
            fname = parts[-1]
            hotel = fname.split("_")[1]
            text = " ".join(io.TextIOWrapper(zf.open(name), encoding="utf-8", errors="replace").read().split())
            if len(text) < 80:
                continue
            cells[(polarity, truthful)].append((f"{polarity}/{fname}", hotel, polarity, truthful, text))
    per = TARGET // 4
    for key in sorted(cells):
        for iid, hotel, polarity, truthful, text in hash_order(cells[key], lambda x: x[0], "op_spam")[:per]:
            yield Question(
                text=TEXT,
                primitive="noul",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=CRITERIA,
                state={"review": text[:1500]},
                shape="detect",
                node_hint="machine.commerce.review_abuse",
                template_id="op_spam.genuine_stay",
                source_item_id=iid,
                license=LICENSE,
                truth=truthful,
                meta={"polarity": polarity, "hotel": hotel},
            )
