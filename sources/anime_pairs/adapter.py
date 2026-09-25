"""MyAnimeList (Anime Recommendations Database): pairwise "Which anime would you rather watch?" between two
well-known anime of the same format sharing a genre, with the human split from users who rated both."""

from __future__ import annotations

import html
import itertools
import re
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "anime_pairs"
BASE = "https://huggingface.co/datasets/jason1966/CooperUnion_anime-recommendations-database/resolve/main/"
FILES = ("anime.csv", "rating.csv")
LICENSE = "CC0 1.0 (Kaggle 'Anime Recommendations Database', CooperUnion; MyAnimeList data), HF mirror jason1966"
TARGET = env_int("TARGET_ANIME_PAIRS", 4000)
SALT = "anime_pairs.v1"
MIN_RATINGS = 2000  # explicit 1-10 ratings in rating.csv (73.5k MAL users)
MIN_MEMBERS = 100_000  # MyAnimeList members (site-wide popularity)
MIN_CORATERS = 200
MAX_PER_ANIME = 25
TEXT = "Which anime would you rather watch?"
FORMATS = {"TV": "TV series", "Movie": "film"}
SKIP_GENRES = {"Hentai", "Ecchi"}  # adult and fan-service genres: dropped entirely
SENSITIVE_GENRES = {"Ecchi"}  # suggestive fan service: kept, flagged
STOP = {"no", "wa", "ga", "to", "the", "a", "of", "kara", "de"}


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        with httpx.stream("GET", BASE + f, timeout=600, follow_redirects=True) as r:
            r.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if len(s) > 40:
        s = s[:40].rsplit("_", 1)[0]
    return s


def _franchise(name: str) -> str:
    """First distinctive word: 'Shingeki no Kyojin Season 2' -> 'shingeki', 'Gintama°' -> 'gintama'."""
    words = [w for w in re.findall(r"[a-z0-9]+", _slug(name).replace("_", " ")) if w not in STOP]
    return words[0] if words else ""


def _anime(raw_dir: Path, counts: pl.DataFrame) -> list[dict]:
    a = pl.read_csv(raw_dir / "anime.csv").join(counts, on="anime_id")
    out, seen = [], set()
    for row in a.sort("n", "anime_id", descending=[True, False]).iter_rows(named=True):
        fmt = FORMATS.get(row["type"])
        genres = {g.strip() for g in (row["genre"] or "").split(",") if g.strip()}
        if not fmt or not genres or genres & SKIP_GENRES or (row["members"] or 0) < MIN_MEMBERS:
            continue
        name = html.unescape(row["name"] or "").strip()
        slug = _slug(name)
        if not slug or slug in seen:  # "Gintama", "Gintama'", "Gintama°" share a slug: keep the most-rated
            continue
        seen.add(slug)
        out.append({
            "id": row["anime_id"], "name": name, "format": row["type"], "genres": genres, "slug": slug,
            "franchise": _franchise(name), "n": row["n"], "members": row["members"],
            "flags": {"sensitive"} if genres & SENSITIVE_GENRES else set(),
        })
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    ratings = pl.read_csv(raw_dir / "rating.csv").filter(pl.col("rating") > 0)  # -1 = watched, not rated
    counts = ratings.group_by("anime_id").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_RATINGS)
    anime = _anime(raw_dir, counts)
    by_id = {x["id"]: x for x in anime}
    sub = (
        ratings.filter(pl.col("anime_id").is_in(list(by_id)))
        .unique(["user_id", "anime_id"], keep="first", maintain_order=True)
        .sort("anime_id", "user_id")
    )
    arrays = {aid: (g["user_id"].to_numpy(), g["rating"].to_numpy())
              for (aid,), g in sub.group_by("anime_id", maintain_order=True)}

    pairs = [
        (a, b)
        for a, b in itertools.combinations(sorted(anime, key=lambda x: x["id"]), 2)
        if a["format"] == b["format"] and a["genres"] & b["genres"] and a["franchise"] != b["franchise"]
    ]
    uses: dict[int, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}-{p[1]['id']}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a["id"], 0) >= MAX_PER_ANIME or uses.get(b["id"], 0) >= MAX_PER_ANIME:
            continue
        ua, ra = arrays[a["id"]]
        ub, rb = arrays[b["id"]]
        _, ia, ib = np.intersect1d(ua, ub, assume_unique=True, return_indices=True)
        n = len(ia)
        if n < MIN_CORATERS:
            continue
        xa, xb = ra[ia], rb[ib]
        wins_a = float((xa > xb).sum()) + 0.5 * float((xa == xb).sum())
        ka, kb = a["slug"], b["slug"]
        if ka == kb:
            continue
        uses[a["id"]] = uses.get(a["id"], 0) + 1
        uses[b["id"]] = uses.get(b["id"], 0) + 1
        taken += 1
        flags = sorted(a["flags"] | b["flags"])
        opts = sorted([(ka, f"{a['name']} (anime {FORMATS[a['format']]})"), (kb, f"{b['name']} (anime {FORMATS[b['format']]})")])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=dict(opts),
            node_hint="self.lifestyle.screens_media",
            source_item_id=f"{a['id']}-{b['id']}",
            license=LICENSE,
            template_id="anime_pairs.watch",
            human=[
                HumanDist(
                    population="MyAnimeList users who rated both anime",
                    distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                    n=n,
                    source="Anime Recommendations Database (MyAnimeList ratings, 2016): share rating each higher, ties split",
                )
            ],
            meta={
                "mal_ids": [a["id"], b["id"]],
                "format": a["format"],
                "shared_genres": sorted(a["genres"] & b["genres"]),
                "ratings_n": [a["n"], b["n"]],
                "members": [a["members"], b["members"]],
                **({"flags": flags} if flags else {}),
            },
        )
