"""News Headlines Dataset for Sarcasm Detection (Misra & Arora 2023): 26,709 headlines, sarcastic ones
from The Onion and non-sarcastic ones from HuffPost (v1 file, GitHub rishabhmisra).

Template "sarcasm_headlines.sarcastic": Noul "Is `headline` sarcastic?" Truth = is_sarcastic.
Balanced 50/50, seeded hash order. The headline only (no link or outlet). Contested politics flagged.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "sarcasm_headlines"
URL = ("https://raw.githubusercontent.com/rishabhmisra/News-Headlines-Dataset-For-Sarcasm-Detection/"
       "master/Sarcasm_Headlines_Dataset.json")
TARGET = env_int("TARGET_SARCASM_HEADLINES", 1500)
LICENSE = "No license file; public research dataset, cite Misra & Arora 2023"
TEXT = "Is `headline` sarcastic?"
CRITERIA = {
    "true": "The headline is satire: it mocks its subject by reporting something absurd or ironic as if it were news",
    "false": "The headline straightforwardly reports or promotes a real story",
}
POLITICAL = re.compile(
    r"\b(trump\w*|obama\w*|clinton\w*|hillary|biden|sanders|bernie|pence|cruz|rubio|pelosi|mcconnell|"
    r"romney|bush|palin|democrat\w*|republican\w*|gop|dnc|rnc|liberal\w*|conservative\w*|election\w*|"
    r"campaign\w*|ballot\w*|vote\w*|voter\w*|senat\w*|congress\w*|abortion\w*|pro-life|pro-choice|"
    r"planned parenthood|gun|guns|nra|immigra\w*|refugee\w*|border wall|deport\w*|isis|muslim ban|"
    r"president\w*|white house|supreme court)\b",
    re.I,
)
SENSITIVE = re.compile(r"\b(sex\w*|porn\w*|rape\w*|suicid\w*|nude\w*|naked|molest\w*|masturbat\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "Sarcasm_Headlines_Dataset.json"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[int, str, str]]] = {True: [], False: []}
    seen: set[str] = set()
    with open(raw_dir / "Sarcasm_Headlines_Dataset.json", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if not line.strip():
                continue
            d = json.loads(line)
            h = " ".join(d["headline"].split())
            if len(h) < 15 or h in seen:
                continue
            seen.add(h)
            pools[bool(d["is_sarcastic"])].append((i, h, d["article_link"]))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += [(label, x) for x in hash_order(pools[label], lambda x: x[0], f"sarcasm.{label}")[:k]]
    picked.sort(key=lambda x: x[1][0])

    for label, (i, h, link) in picked:
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
            template_id="sarcasm_headlines.sarcastic",
            source_item_id=f"v1:{i}",
            license=LICENSE,
            truth=label,
            meta={"outlet": "The Onion" if label else "HuffPost", "article_link": link,
                  **({"flags": flags} if flags else {})},
        )
