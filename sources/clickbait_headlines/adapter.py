"""Stop Clickbait (Chakraborty et al. 2016): 32,000 English news headlines, 16,000 clickbait (BuzzFeed,
Upworthy, ViralNova, Thatscoop, Scoopwhoop, ViralStories) and 16,000 not (WikiNews, New York Times,
The Guardian, The Hindu). Labels follow the outlet, so a few straight BuzzFeed headlines count as
clickbait.

Template "clickbait.is_clickbait": Noul "Is `headline` clickbait?" Truth = the file it comes from.
Balanced 50/50, exact dedup, salted hash order. Contested politics flagged.
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "clickbait_headlines"
BASE = "https://raw.githubusercontent.com/bhargaviparanjape/clickbait/master/dataset/"
FILES = {True: "clickbait_data.gz", False: "non_clickbait_data.gz"}
TARGET = env_int("TARGET_CLICKBAIT_HEADLINES", 2500)
LICENSE = "No license file; public research dataset (bhargaviparanjape/clickbait), cite Chakraborty et al. 2016"
TEXT = "Is `headline` clickbait?"
CRITERIA = {
    "true": "The headline withholds or teases the story to lure a click (a curiosity gap, a listicle hook, "
    "'you won't believe', a question it does not answer)",
    "false": "The headline states what the story reports",
}
POLITICAL = re.compile(
    r"\b(trump\w*|obama\w*|clinton\w*|hillary|biden|sanders|bernie|pence|cruz|rubio|pelosi|romney|bush|"
    r"democrat\w*|republican\w*|gop|election\w*|campaign\w*|ballot\w*|voter\w*|abortion\w*|gun|guns|nra|"
    r"immigra\w*|refugee\w*|deport\w*|brexit|modi|bjp|congress party)\b",
    re.I,
)
SENSITIVE = re.compile(r"\b(sex\w*|porn\w*|rape\w*|suicid\w*|nude\w*|naked|molest\w*|masturbat\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for f in FILES.values():
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[str, str]]] = {True: [], False: []}
    seen: set[str] = set()
    for label, f in FILES.items():
        with gzip.open(raw_dir / f, "rt", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                h = " ".join(line.split())
                if len(h.split()) < 4 or h.lower() in seen or "�" in h:
                    continue
                seen.add(h.lower())
                pools[label].append((f"{'cb' if label else 'ncb'}:{i}", h))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += [(label, x) for x in hash_order(pools[label], lambda x: x[0], f"clickbait.{label}")[:k]]
    picked.sort(key=lambda x: (x[1][0].split(":")[0], int(x[1][0].split(":")[1])))

    for label, (sid, h) in picked:
        flags = (["political"] if POLITICAL.search(h) else []) + (["sensitive"] if SENSITIVE.search(h) else [])
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"headline": h},
            shape="detect",
            node_hint="machine.trust_safety.brand_safety",
            template_id="clickbait.is_clickbait",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"file": FILES[label], **({"flags": flags} if flags else {})},
        )
