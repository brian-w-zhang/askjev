"""TruthfulQA multiple choice (mc1: one correct answer), shuffled, with category-based node hints."""

from __future__ import annotations

import hashlib
import random
import string
from pathlib import Path
from typing import Iterator

import httpx
import pyarrow.parquet as pq

from askjev.model import Question

NAME = "truthfulqa"
BASE = "https://huggingface.co/datasets/truthfulqa/truthful_qa/resolve/main"
FILES = {
    "mc.parquet": f"{BASE}/multiple_choice/validation-00000-of-00001.parquet",
    "generation.parquet": f"{BASE}/generation/validation-00000-of-00001.parquet",
}
LICENSE = "Apache-2.0"
SEED = "truthfulqa-20260924"

NODES = {
    "Misconceptions": "world.science",
    "Misconceptions: Topical": "world.society",
    "Law": "world.society.crime_law",
    "Sociology": "world.society",
    "Health": "world.health",
    "Nutrition": "world.health.nutrition",
    "Psychology": "world.science.psychology_neuroscience",
    "Economics": "world.money.economics",
    "Finance": "world.money.investing",
    "Advertising": "world.money.companies_brands",
    "Fiction": "world.arts.books",
    "Mandela Effect": "world.arts",
    "Paranormal": "world.science.fringe_mysteries",
    "Conspiracies": "world.science.fringe_mysteries",
    "Superstitions": "world.society.mythology_folklore",
    "Myths and Fairytales": "world.society.mythology_folklore",
    "Religion": "world.society.world_religions",
    "History": "world.history",
    "Confusion: People": "world.history.figures",
    "Misquotations": "world.history.figures",
    "Confusion: Places": "world.places",
    "Language": "world.society.languages",
    "Proverbs": "world.society.languages",
    "Weather": "world.nature.weather_climate",
    "Science": "world.science",
    "Statistics": "world.science.mathematics",
    "Logical Falsehood": "world.science.mathematics",
    "Misinformation": "world.society.media_news",
    "Education": "world.society.education",
    "Politics": "world.society",
}


def fetch(raw_dir: Path) -> None:
    for name, url in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    gen = pq.read_table(raw_dir / "generation.parquet").to_pylist()
    category = {r["question"].strip(): r["category"] for r in gen}
    for i, r in enumerate(pq.read_table(raw_dir / "mc.parquet").to_pylist()):
        q = r["question"].strip()
        choices, labels = r["mc1_targets"]["choices"], r["mc1_targets"]["labels"]
        if sum(labels) != 1 or not 2 <= len(choices) <= 26:
            continue
        pairs = list(zip((c.strip() for c in choices), labels))
        rng = random.Random(int(hashlib.sha256(f"{SEED}:{q}".encode()).hexdigest()[:16], 16))
        rng.shuffle(pairs)
        keys = string.ascii_lowercase[: len(pairs)]
        cat = category.get(q)
        meta = {"category": cat}
        if cat == "Politics":
            meta["flags"] = ["political"]
        yield Question(
            text=q,
            primitive="choice",
            hemisphere="world",
            kind="factual",
            origin="dataset",
            source=NAME,
            options={k: c for k, (c, _) in zip(keys, pairs)},
            truth=next(k for k, (_, lab) in zip(keys, pairs) if lab == 1),
            node_hint=NODES.get(cat, "world.society"),
            source_item_id=f"mc{i}",
            license=LICENSE,
            meta=meta,
        )
