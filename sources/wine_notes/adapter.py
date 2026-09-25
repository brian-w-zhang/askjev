"""Wine Enthusiast reviews (winemag-data-130k, scraped by zackthoutt; HF copy GroNLP/ik-nlp-22_winemag,
the set the TypeSafe cookbook uses): a critic's tasting note plus its 80-100 point score.

Template "wine_notes.rating": Score "How highly does the critic rate the wine in `note`?" with five
situation levels mapped from point bands (80-84 / 85-87 / 88-90 / 91-93 / 94-100). Truth = band index.
Balanced 400 per band over train+validation+test, seeded hash order; exact-note dedup.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "wine_notes"
BASE = "https://huggingface.co/api/datasets/GroNLP/ik-nlp-22_winemag/parquet/default"
SPLITS = ("train", "validation", "test")
TARGET = env_int("TARGET_WINE_NOTES", 2000)
LICENSE = "CC-BY-SA-4.0 (HF card; the original Kaggle scrape is CC-BY-NC-SA-4.0)"
TEXT = "How highly does the critic rate the wine in `note`?"
LEVELS = [
    "A plain, simple wine the critic finds acceptable at best and would not go out of their way to recommend",
    "A decent everyday wine that is pleasant but unremarkable",
    "A very good wine the critic would happily recommend",
    "An excellent wine that stands out among the better examples of its kind",
    "A superb wine among the very best of its kind, worth seeking out",
]
BANDS = [(80, 84), (85, 87), (88, 90), (91, 93), (94, 100)]


def _band(points: int) -> int | None:
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= points <= hi:
            return i
    return None


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{split}/0.parquet", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[int, list[tuple[str, str, int, dict]]] = {i: [] for i in range(len(BANDS))}
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        cols = ("index", "description", "points", "price", "country", "province", "variety")
        for idx, desc, points, price, country, province, variety in df.select(cols).iter_rows():
            note = " ".join((desc or "").split())
            band = _band(points) if points is not None else None
            if band is None or len(note) < 40 or note.lower() in seen:
                continue
            seen.add(note.lower())
            meta = {"points": points, "price": price, "country": country, "province": province, "variety": variety}
            pools[band].append((f"winemag:{idx}", note, band, meta))

    per = TARGET // len(BANDS)
    picked = []
    for band in pools:
        k = per + (1 if band < TARGET - per * len(BANDS) else 0)
        picked += hash_order(pools[band], lambda x: x[0], f"wine.{band}")[:k]
    picked.sort(key=lambda x: int(x[0].split(":")[1]))

    for sid, note, band, meta in picked:
        yield Question(
            text=TEXT,
            primitive="score",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            state={"note": note[:1500]},
            shape="score",
            node_hint="machine.documents.feature_extraction",
            template_id="wine_notes.rating",
            source_item_id=sid,
            license=LICENSE,
            truth=band,
            meta=meta,
        )
