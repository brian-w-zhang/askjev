"""BoardGameGeek: pairwise "Which board game would you rather play?" between two well-known games of the same
BGG subdomain and similar weight, with the human split from users who rated both."""

from __future__ import annotations

import ast
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

NAME = "boardgame_pairs"
BASE = "https://huggingface.co/datasets/mmpa/board_game_analysis/resolve/main/"
REVIEWS = "bgg-26m-reviews.csv"
GAMES = "games_detailed_info2025.csv"
LICENSE = "BoardGameGeek user ratings (Kaggle 'BoardGameGeek Reviews' by jvanelteren, HF mirror mmpa/board_game_analysis; research use)"
TARGET = env_int("TARGET_BOARDGAME_PAIRS", 4000)
SALT = "boardgame_pairs.v1"
MIN_RATINGS = 5000  # BGG user ratings per game: 987 games, the well-known end of the hobby
MIN_CORATERS = 300
MAX_PER_GAME = 25
MAX_WEIGHT_GAP = 1.0  # BGG complexity weight (1-5)
TEXT = "Which board game would you rather play?"
SUBDOMAINS = {
    "Strategy Game Rank": "strategy", "Family Game Rank": "family", "Party Game Rank": "party",
    "Thematic Rank": "thematic", "War Game Rank": "wargame", "Abstract Game Rank": "abstract",
    "Customizable Rank": "customizable", "Children's Game Rank": "childrens",
}


def fetch(raw_dir: Path) -> None:
    for f in (REVIEWS, GAMES):
        out = raw_dir / f
        if out.exists() or (f == REVIEWS and (raw_dir / "ratings.parquet").exists()):
            continue
        with httpx.stream("GET", BASE + f, timeout=1800, follow_redirects=True) as r:
            r.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    if not (raw_dir / "ratings.parquet").exists():
        pl.scan_csv(
            raw_dir / REVIEWS, schema_overrides={"user": pl.String, "rating": pl.Float64, "ID": pl.Int64}
        ).select("user", "ID", "rating").sink_parquet(raw_dir / "ratings.parquet")
        (raw_dir / REVIEWS).unlink()


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if len(s) > 40:
        s = s[:40].rsplit("_", 1)[0]
    return s


def _head(name: str) -> str:
    """Franchise head: 'Ticket to Ride: Europe' -> 'ticket to ride'."""
    return re.split(r"[:–(]", name)[0].strip().casefold()


def _same_franchise(a: dict, b: dict) -> bool:
    ha, hb = a["head"], b["head"]
    return ha == hb or ha.startswith(hb + " ") or hb.startswith(ha + " ")


def _games(raw_dir: Path, counts: pl.DataFrame) -> list[dict]:
    g = pl.read_csv(raw_dir / GAMES, infer_schema_length=0).with_columns(pl.col("id").cast(pl.Int64))
    g = g.join(counts, left_on="id", right_on="ID")
    out, seen = [], set()
    for row in g.sort("n", "id", descending=[True, False]).iter_rows(named=True):
        name = (row["name"] or "").strip()
        subs = {v for k, v in SUBDOMAINS.items() if row[k] not in (None, "", "Not Ranked")}
        try:
            weight = float(row["averageweight"])
        except (TypeError, ValueError):
            continue
        year = int(float(row["yearpublished"])) if row["yearpublished"] else 0
        slug = _slug(name)
        if not name or not slug or not subs or weight <= 0 or slug in seen:  # same (truncated) slug: keep the most-rated
            continue
        seen.add(slug)
        cats = ast.literal_eval(row["boardgamecategory"]) if row["boardgamecategory"] else []
        out.append({
            "id": row["id"], "name": name, "year": year, "subs": subs, "weight": weight, "slug": slug,
            "head": _head(name), "n": row["n"], "flags": {"sensitive"} if "Mature / Adult" in cats else set(),
        })
    return out


def _label(g: dict) -> str:
    return f"{g['name']} ({g['year']})" if g["year"] > 0 else g["name"]


def normalize(raw_dir: Path) -> Iterator[Question]:
    ratings = pl.read_parquet(raw_dir / "ratings.parquet")
    counts = ratings.group_by("ID").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_RATINGS)
    games = _games(raw_dir, counts)
    by_id = {x["id"]: x for x in games}
    users = ratings.select("user").unique().sort("user").with_row_index("uid")
    sub = (
        ratings.filter(pl.col("ID").is_in(list(by_id)))
        .join(users, on="user")
        .unique(["uid", "ID"], keep="first", maintain_order=True)
        .sort("ID", "uid")
    )
    arrays = {gid: (g["uid"].to_numpy(), g["rating"].to_numpy())
              for (gid,), g in sub.group_by("ID", maintain_order=True)}

    pairs = [
        (a, b)
        for a, b in itertools.combinations(sorted(games, key=lambda x: x["id"]), 2)
        if a["subs"] & b["subs"] and abs(a["weight"] - b["weight"]) <= MAX_WEIGHT_GAP and not _same_franchise(a, b)
    ]
    uses: dict[int, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}-{p[1]['id']}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a["id"], 0) >= MAX_PER_GAME or uses.get(b["id"], 0) >= MAX_PER_GAME:
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
        flags = sorted(a["flags"] | b["flags"])
        opts = sorted([(ka, _label(a)), (kb, _label(b))])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=dict(opts),
            node_hint="self.lifestyle.leisure_hobbies",
            source_item_id=f"{a['id']}-{b['id']}",
            license=LICENSE,
            template_id="boardgame_pairs.play",
            human=[
                HumanDist(
                    population="BoardGameGeek users who rated both games",
                    distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                    n=n,
                    source="BoardGameGeek user ratings (bgg-26m-reviews): share rating each game higher, ties split",
                )
            ],
            meta={
                "bgg_ids": [a["id"], b["id"]],
                "years": [a["year"], b["year"]],
                "shared_subdomains": sorted(a["subs"] & b["subs"]),
                "weights": [round(a["weight"], 2), round(b["weight"], 2)],
                "ratings_n": [a["n"], b["n"]],
                **({"flags": flags} if flags else {}),
            },
        )
