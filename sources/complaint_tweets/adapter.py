"""Complaints on social media (Preotiuc-Pietro, Gaman & Aletras, ACL 2019): 3,449 English tweets
addressed to company customer-service accounts across nine industries, hand-labelled complaint / not.

Template "complaint_tweets.complaint" (Noul, detect): is the tweet a complaint? Truth = the paper's label
(a complaint states a breach of expectations: a problem, a failure or dissatisfaction). All complaints plus
an equal-ish number of non-complaints, seeded.
"""

from __future__ import annotations

import csv
import html
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "complaint_tweets"
URL = "https://raw.githubusercontent.com/danielpreotiuc/complaints-social-media/master/complaints-data.csv"
LICENSE = "research use (released with the ACL 2019 paper; no explicit license)"
TARGET = env_int("TARGET_COMPLAINT_TWEETS", 2500)
TEXT = "Is `tweet`, a reply or mention directed at a company or brand on Twitter, a complaint?"
OPTIONS = {
    "true": "It says something went wrong or fell short of what the customer expected: a problem, a failure, "
    "poor service or dissatisfaction.",
    "false": "It is a question, request, thanks, praise or other message that does not report a problem.",
}
SLURS = re.compile(r"\b(n[i1]gg(er|a|ers|as)|fag(got)?s?|retards?|kikes?|spics?|chinks?|trann(y|ies))\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "complaints-data.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows, seen = [], set()
    with open(raw_dir / "complaints-data.csv", newline="", encoding="utf-8") as fh:
        for tid, text, label, domain in csv.reader(fh):
            text = html.unescape(text).strip()
            norm = re.sub(r"\W+", " ", text.lower()).strip()
            if len(norm) < 10 or norm in seen or SLURS.search(text):
                continue
            seen.add(norm)
            rows.append({"id": tid, "text": text, "label": label == "1", "domain": domain})
    pos = [r for r in rows if r["label"]]
    neg = [r for r in rows if not r["label"]]
    n_pos = min(len(pos), TARGET // 2)
    pick = hash_order(pos, lambda r: r["id"], NAME)[:n_pos] + hash_order(neg, lambda r: r["id"], NAME)[: TARGET - n_pos]
    for r in hash_order(pick, lambda r: r["id"], NAME + ".order"):
        yield Question(
            text=TEXT, primitive="noul", hemisphere="machine", origin="dataset", source=NAME, options=OPTIONS,
            state={"tweet": r["text"][:1500]}, shape="detect", node_hint="machine.support.urgency_frustration",
            template_id="complaint_tweets.complaint", source_item_id=r["id"], license=LICENSE, truth=r["label"],
            meta={"industry": r["domain"]},
        )
