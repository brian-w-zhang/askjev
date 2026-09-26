"""YouTube Spam Collection (Alberto, Lochter & Almeida 2015; UCI ML Repository #380).

1,956 real comments from five of the most-viewed YouTube music videos of 2013-2015 (Psy, Katy Perry,
LMFAO, Eminem, Shakira), hand-labelled spam / not spam by the authors (~51% spam).

Template "youtube_spam.spam" (Noul): "Is `comment` on `video` spam?" over every usable comment
(the whole collection is below the 3,000 template cap); truth = CLASS == 1.
Cleanup: BOM characters stripped, whitespace collapsed, HTML line breaks -> spaces. Dropped: empty or
duplicate (same video + text) comments.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "youtube_spam"
URL = "https://archive.ics.uci.edu/static/public/380/youtube+spam+collection.zip"
LICENSE = "CC-BY-4.0"
NODE = "machine.trust_safety.spam_phishing"
TARGET = env_int("TARGET_YOUTUBE_SPAM", 2000)
VIDEOS = {
    "Youtube01-Psy.csv": "PSY - Gangnam Style (official music video)",
    "Youtube02-KatyPerry.csv": "Katy Perry - Roar (official music video)",
    "Youtube03-LMFAO.csv": "LMFAO - Party Rock Anthem (official music video)",
    "Youtube04-Eminem.csv": "Eminem - Love the Way You Lie ft. Rihanna (official music video)",
    "Youtube05-Shakira.csv": "Shakira - Waka Waka (This Time for Africa) (official music video)",
}
TEXT = "Is `comment`, posted under the YouTube video `video`, spam?"
OPTIONS = {
    "true": "Self-promotion, requests to subscribe or visit a channel or site, money-making offers, or links "
    "unrelated to the video",
    "false": "A genuine reaction to or discussion of the video or song",
}
SEXUAL = re.compile(r"\b(sex|sexy|porn\w*|nude\w*|naked|xxx|horny|dick|cock|pussy|boobs?|tits)\b", re.I)


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / f).exists() for f in VIDEOS):
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for f in VIDEOS:
            (raw_dir / f).write_bytes(z.read(f))


def normalize(raw_dir: Path) -> Iterator[Question]:
    items = []
    seen: set[tuple[str, str]] = set()
    for f, video in VIDEOS.items():
        d = pl.read_csv(raw_dir / f)
        for r in d.iter_rows(named=True):
            t = (r["CONTENT"] or "").replace("﻿", "")
            t = re.sub(r"<br\s*/?>", " ", t)
            t = " ".join(t.split())
            if not t or (video, t.lower()) in seen:
                continue
            seen.add((video, t.lower()))
            items.append((r["COMMENT_ID"], video, t[:1500], int(r["CLASS"]) == 1, f))
    for cid, video, t, spam, f in sorted(hash_order(items, lambda x: x[0], "youtube_spam")[:TARGET], key=lambda x: x[0]):
        yield Question(
            text=TEXT, primitive="noul", hemisphere="machine", origin="dataset", source=NAME,
            options=OPTIONS, state={"video": video, "comment": t}, shape="detect", node_hint=NODE,
            template_id="youtube_spam.spam", source_item_id=cid, license=LICENSE, truth=spam,
            meta={"file": f, **({"flags": ["sensitive"]} if SEXUAL.search(t) else {})},
        )
