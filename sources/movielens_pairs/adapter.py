"""MovieLens 32M: pairwise "Which movie would you rather watch?" between two well-known films of a similar
era and genre, with the human split from users who rated both."""

from __future__ import annotations

import itertools
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "movielens_pairs"
URL = "https://files.grouplens.org/datasets/movielens/ml-32m.zip"
ZIP = "ml-32m.zip"
LICENSE = "MovieLens 32M usage license (GroupLens, research use, non-commercial, cite Harper & Konstan 2015)"
TARGET = env_int("TARGET_MOVIELENS_PAIRS", 4000)
SALT = "movielens_pairs.v1"
MIN_RATINGS = 5000  # per film: 1,489 films, the well-known end of the catalog (brief floor was 500)
MIN_CORATERS = 200  # users who rated both films
MAX_PER_FILM = 25
MAX_YEAR_GAP = 10
TEXT = "Which movie would you rather watch?"
ARTICLES = ("The", "A", "An", "Les", "La", "Le", "L'", "Il", "El", "Das", "Der", "Die", "Los", "Las")
# Content filter (flag, never drop): films built around sexual content, and contested-politics documentaries/biopics.
SENSITIVE = {("Showgirls", 1995), ("Basic Instinct", 1992), ("Kids", 1995), ("Eyes Wide Shut", 1999),
             ("Irreversible", 2002), ("Lolita", 1997), ("Fifty Shades of Grey", 2015), ("Nymphomaniac: Volume I", 2013),
             ("Shame", 2011), ("Blue Is the Warmest Color", 2013), ("Y Tu Mamá También", 2001)}
POLITICAL = {("Fahrenheit 9/11", 2004), ("Bowling for Columbine", 2002), ("An Inconvenient Truth", 2006),
             ("Sicko", 2007), ("W.", 2008), ("Vice", 2018), ("Fahrenheit 11/9", 2018)}
TITLE = re.compile(r"^(.*?)\s*\((\d{4})\)\s*$")


def fetch(raw_dir: Path) -> None:
    z = raw_dir / ZIP
    if not z.exists():
        with httpx.stream("GET", URL, timeout=600, follow_redirects=True) as r:
            r.raise_for_status()
            with open(z, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    if not (raw_dir / "ratings.parquet").exists():
        with zipfile.ZipFile(z) as zf:
            zf.extract("ml-32m/movies.csv", raw_dir)
            zf.extract("ml-32m/ratings.csv", raw_dir)
        pl.scan_csv(raw_dir / "ml-32m/ratings.csv").select("userId", "movieId", "rating").sink_parquet(
            raw_dir / "ratings.parquet"
        )
        (raw_dir / "ml-32m/ratings.csv").unlink()


def _display(raw_title: str) -> tuple[str, int] | None:
    """'Hunt, The (Jagten) (2012)' -> ('The Hunt', 2012). Alternate-language titles in parentheses are dropped."""
    m = TITLE.match(raw_title.strip())
    if not m:
        return None
    name, year = m.group(1), int(m.group(2))
    name = re.sub(r"\s*\([^)]*\)", "", name).strip()
    for art in ARTICLES:
        suffix = f", {art}"
        if name.endswith(suffix):
            name = f"{art}{'' if art.endswith(chr(39)) else ' '}{name[: -len(suffix)]}"
            break
        # 'Lord of the Rings, The: The Fellowship...' style: article before a subtitle
        if f"{suffix}:" in name:
            head, tail = name.split(f"{suffix}:", 1)
            name = f"{art} {head}:{tail}"
            break
    if not name or not any(ch.isalpha() for ch in name):
        return None
    return name, year


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if len(s) > 40:
        s = s[:40].rsplit("_", 1)[0]
    return s


def _films(raw_dir: Path, ratings: pl.DataFrame) -> list[dict]:
    counts = ratings.group_by("movieId").len().filter(pl.col("len") >= MIN_RATINGS)
    movies = pl.read_csv(raw_dir / "ml-32m/movies.csv").join(counts, on="movieId")
    out, seen = [], set()
    for row in movies.sort("len", descending=True).iter_rows(named=True):
        d = _display(row["title"])
        if not d:
            continue
        name, year = d
        if (name.casefold(), year) in seen:  # duplicate catalog entries: keep the most-rated
            continue
        seen.add((name.casefold(), year))
        genres = set(row["genres"].split("|")) - {"(no genres listed)", "IMAX"}
        slug = _slug(name)
        if not slug or not genres:
            continue
        out.append({"id": row["movieId"], "name": name, "year": year, "genres": genres, "slug": slug, "n": row["len"]})
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    ratings = pl.read_parquet(raw_dir / "ratings.parquet")
    films = _films(raw_dir, ratings)
    by_id = {f["id"]: f for f in films}
    sub = ratings.filter(pl.col("movieId").is_in(list(by_id))).sort("movieId", "userId")
    arrays: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for (mid,), g in sub.group_by("movieId", maintain_order=True):
        arrays[mid] = (g["userId"].to_numpy(), g["rating"].to_numpy())

    pairs = [
        (a, b)
        for a, b in itertools.combinations(sorted(films, key=lambda f: f["id"]), 2)
        if abs(a["year"] - b["year"]) <= MAX_YEAR_GAP and a["genres"] & b["genres"]
    ]
    uses: dict[int, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}-{p[1]['id']}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a["id"], 0) >= MAX_PER_FILM or uses.get(b["id"], 0) >= MAX_PER_FILM:
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
            ka, kb = f"{ka}_{a['year']}", f"{kb}_{b['year']}"
        if ka == kb:
            continue
        uses[a["id"]] = uses.get(a["id"], 0) + 1
        uses[b["id"]] = uses.get(b["id"], 0) + 1
        taken += 1
        flags = sorted(
            {"sensitive" for f in (a, b) if (f["name"], f["year"]) in SENSITIVE}
            | {"political" for f in (a, b) if (f["name"], f["year"]) in POLITICAL}
        )
        opts = sorted([(ka, f"{a['name']} ({a['year']})"), (kb, f"{b['name']} ({b['year']})")])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="template",
            source=NAME,
            options=dict(opts),
            node_hint="self.lifestyle.this_or_that",
            source_item_id=f"{a['id']}-{b['id']}",
            license=LICENSE,
            template_id="movielens_pairs.watch",
            human=[
                HumanDist(
                    population="MovieLens users who rated both films",
                    distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                    n=n,
                    source="MovieLens 32M ratings (GroupLens, 2023): share rating each film higher, ties split",
                )
            ],
            meta={
                "movie_ids": [a["id"], b["id"]],
                "years": [a["year"], b["year"]],
                "shared_genres": sorted(a["genres"] & b["genres"]),
                "ratings_n": [a["n"], b["n"]],
                **({"flags": flags} if flags else {}),
            },
        )
