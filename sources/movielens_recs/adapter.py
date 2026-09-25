"""MovieLens 32M (GroupLens): 32 million 0.5-5 star ratings by 200k users. Real taste histories make a
recommendation check with a known outcome: show a user's profile (films they loved and films they
disliked) and one more film they rated, and ask whether they will enjoy it.

Template "movielens.will_enjoy": Noul "Based on `profile`, will this user enjoy `candidate`?"
Truth = the user's own rating of the candidate: >= 4.5 stars (true) or <= 2 stars (false); middling
ratings are never used as candidates. Films restricted to well-known ones (>= 2,000 ratings). Profile =
5 films the user rated >= 4.5 and 3 rated <= 2 (salted hash order), none of them the candidate. One
question per user; half the users get a loved candidate, half a disliked one.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "movielens_recs"
URL = "https://files.grouplens.org/datasets/movielens/ml-32m.zip"
TARGET = env_int("TARGET_MOVIELENS_RECS", 2500)
LICENSE = "MovieLens 32M usage license (GroupLens, research use, non-commercial, cite Harper & Konstan 2015)"
MIN_FILM_RATINGS = 2000
N_LOVED, N_DISLIKED = 5, 3
TEXT = "Based on `profile`, will this user enjoy `candidate`?"
CRITERIA = {
    "true": "The user would rate the film 4.5 or 5 stars out of 5",
    "false": "The user would rate the film 2 stars or lower out of 5",
}
ARTICLES = ("The", "A", "An", "Les", "La", "Le", "L'", "Il", "El", "Das", "Der", "Die", "Los", "Las")
TITLE = re.compile(r"^(.*?)\s*\((\d{4})\)\s*$")
SENSITIVE = {("Showgirls", 1995), ("Basic Instinct", 1992), ("Kids", 1995), ("Eyes Wide Shut", 1999),
             ("Irreversible", 2002), ("Lolita", 1997), ("Fifty Shades of Grey", 2015), ("Shame", 2011),
             ("Blue Is the Warmest Color", 2013), ("Y Tu Mamá También", 2001), ("A Serbian Film", 2010),
             ("The Human Centipede", 2009), ("Salò, or the 120 Days of Sodom", 1975)}
POLITICAL = {("Fahrenheit 9/11", 2004), ("Bowling for Columbine", 2002), ("An Inconvenient Truth", 2006),
             ("Sicko", 2007), ("W.", 2008), ("Vice", 2018), ("Fahrenheit 11/9", 2018)}


def fetch(raw_dir: Path) -> None:
    """Reuse movielens_pairs' extracted ratings when present (same release), else download the zip."""
    ratings, movies = raw_dir / "ratings.parquet", raw_dir / "movies.csv"
    if ratings.exists() and movies.exists():
        return
    sib = raw_dir.parent / "movielens_pairs"
    if (sib / "ratings.parquet").exists() and (sib / "ml-32m/movies.csv").exists():
        for src, dst in ((sib / "ratings.parquet", ratings), (sib / "ml-32m/movies.csv", movies)):
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy(src, dst)
        return
    z = raw_dir / "ml-32m.zip"
    if not z.exists():
        with httpx.stream("GET", URL, timeout=600, follow_redirects=True) as r:
            r.raise_for_status()
            with open(z, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    with zipfile.ZipFile(z) as zf:
        zf.extract("ml-32m/movies.csv", raw_dir)
        zf.extract("ml-32m/ratings.csv", raw_dir)
    shutil.move(raw_dir / "ml-32m/movies.csv", movies)
    pl.scan_csv(raw_dir / "ml-32m/ratings.csv").select("userId", "movieId", "rating").sink_parquet(ratings)
    (raw_dir / "ml-32m/ratings.csv").unlink()


def _display(raw_title: str) -> tuple[str, int] | None:
    """'Hunt, The (Jagten) (2012)' -> ('The Hunt', 2012)."""
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
        if f"{suffix}:" in name:
            head, tail = name.split(f"{suffix}:", 1)
            name = f"{art} {head}:{tail}"
            break
    if not name or not any(ch.isalpha() for ch in name):
        return None
    return name, year


def _h(*parts) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def normalize(raw_dir: Path) -> Iterator[Question]:
    films: dict[int, tuple[str, int]] = {}
    for mid, title in pl.read_csv(raw_dir / "movies.csv").select("movieId", "title").iter_rows():
        d = _display(title)
        if d:
            films[mid] = d
    r = pl.scan_parquet(raw_dir / "ratings.parquet")
    known = (
        r.group_by("movieId").len().filter(pl.col("len") >= MIN_FILM_RATINGS).select("movieId").collect()["movieId"]
    )
    known = [m for m in known.to_list() if m in films]
    strong = (
        r.filter(pl.col("movieId").is_in(known) & ((pl.col("rating") >= 4.5) | (pl.col("rating") <= 2.0)))
        .collect()
    )
    users = (
        strong.group_by("userId")
        .agg(
            loved=pl.col("movieId").filter(pl.col("rating") >= 4.5),
            disliked=pl.col("movieId").filter(pl.col("rating") <= 2.0),
        )
        .filter((pl.col("loved").list.len() >= N_LOVED + 1) & (pl.col("disliked").list.len() >= N_DISLIKED + 1))
    )
    rows = users.select("userId", "loved", "disliked").rows()
    picked = hash_order(rows, lambda x: x[0], "movielens_recs.users")[:TARGET]
    for uid, loved, disliked in sorted(picked):
        loved = sorted(loved, key=lambda m: _h("loved", uid, m))
        disliked = sorted(disliked, key=lambda m: _h("disliked", uid, m))
        label = int(_h("label", uid), 16) % 2 == 0
        cand = loved[0] if label else disliked[0]
        prof_loved, prof_dis = (loved[1:1 + N_LOVED], disliked[:N_DISLIKED]) if label else \
            (loved[:N_LOVED], disliked[1:1 + N_DISLIKED])
        fmt = lambda m: f"{films[m][0]} ({films[m][1]})"  # noqa: E731
        profile = {"loved (rated 4.5-5 stars)": [fmt(m) for m in prof_loved],
                   "disliked (rated 2 stars or lower)": [fmt(m) for m in prof_dis]}
        shown = [films[m] for m in prof_loved + prof_dis + [cand]]
        flags = sorted({"sensitive" for f in shown if f in SENSITIVE} | {"political" for f in shown if f in POLITICAL})
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"profile": profile, "candidate": fmt(cand)},
            shape="detect",
            node_hint="machine.search.recommendation",
            template_id="movielens.will_enjoy",
            source_item_id=f"user:{uid}:movie:{cand}",
            license=LICENSE,
            truth=label,
            meta={"user_id": uid, "candidate_movie_id": cand, **({"flags": flags} if flags else {})},
        )
