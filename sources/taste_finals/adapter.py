"""Taste finals: a round robin among Jev's 24 top-rated items in each taste domain (docs/15 "Taste").

The ratings rank every item but crowd the top with near-ties; the finals settle the order with direct head-to-heads,
every finalist against every other (276 pairs per domain), each asked in both orders by the normal shuffle probes.
Finalists come from scripts/experiments/taste_finals_pool.py (Jev's own ratings, so nothing outside the model).
"""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "taste_finals"
LICENSE = "Items from the taste sources' catalogs (see taste_ratings and g5_w13_ratings); pairs authored for this project"
ASK = {"film": "Which film would you rather watch?", "book": "Which book would you rather read?",
       "board_game": "Which board game would you rather play?", "anime": "Which anime would you rather watch?",
       "beer": "Which beer would you rather drink?", "music": "Which would you rather listen to?",
       "food": "Which would you rather eat or drink?", "place": "Which place would you rather visit?",
       "art": "Which would you rather see or experience?", "nature": "Which would you rather see or experience?",
       "activity": "Which would you rather play or do?", "culture": "Which would you rather experience?"}


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "top24.json").exists():
        raise SystemExit("run scripts/experiments/taste_finals_pool.py first")


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:60]


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = json.loads((raw_dir / "top24.json").read_text())
    for dom, p in pool.items():
        for a, b in combinations(p["items"], 2):
            ka, kb = _key(a["name"]), _key(b["name"])
            if ka == kb:
                kb += "_2"
            yield Question(text=ASK[dom], primitive="choice", hemisphere="self", kind="taste", origin="template",
                           source=NAME, options={ka: a["name"], kb: b["name"]}, node_hint=p["node"], license=LICENSE,
                           source_item_id=f"{dom}:{a['id']}:{b['id']}",
                           meta={"experiment": "taste_finals", "domain": dom, "a": a["id"], "b": b["id"]})
