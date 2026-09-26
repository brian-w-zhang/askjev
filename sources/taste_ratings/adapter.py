"""Single-item taste ratings: "How much would you enjoy watching <film>?" as a Score over concrete reactions, one
question per film, book, board game, anime and beer, with the human distribution of real user ratings for that item.

Head-to-head matchups (the *_pairs sources) only say which of two things wins; an absolute rating per item lets the
same items be ranked, gives Jev's favorites and dislikes directly, and lets the pairs be checked against the ratings.
The item pools come from the matching *_pairs adapter (same cleaning, franchise handling and content flags) with a
lower popularity floor; the raw files are the ones those adapters downloaded (this adapter reads them, no fetch).

Human ratings are binned onto five situation levels (docs/01-jev.md §7: situations, not degrees):
  MovieLens 0.5-5 stars and BeerAdvocate 1-5: <=1.5 | 2-2.5 | 3-3.5 | 4 | 4.5-5
  Goodreads 1-5 stars: 1 | 2 | 3 | 4 | 5 (goodbooks-10k's full Goodreads rating counts per book)
  BoardGameGeek 1-10: <4 | 4-6 | 6-7.5 | 7.5-9 | >=9
  MyAnimeList 1-10: 1-3 | 4-5 | 6-7 | 8 | 9-10
The binning is a mapping choice, recorded in each question's meta; the levels are judged alone, so Jev never sees it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "taste_ratings"
SALT = "taste_ratings.v1"
RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
NODE = "self.lifestyle.ratings"

LEVELS = {
    "film": [
        "You'd turn it off within the first twenty minutes",
        "You'd finish it but forget it within a week",
        "You'd enjoy it once and not seek it out again",
        "You'd recommend it to a friend",
        "You'd rewatch it and count it among your favorites",
    ],
    "book": [
        "You'd put it down after a chapter or two",
        "You'd finish it out of duty and forget it soon after",
        "You'd enjoy it once and not reread it",
        "You'd recommend it to a friend",
        "You'd reread it and count it among your favorite books",
    ],
    "board_game": [
        "You'd want to quit before the first game ended",
        "You'd play one game and never ask for it again",
        "You'd play it again if someone else suggested it",
        "You'd suggest it yourself at the next game night",
        "You'd want to own it and play it again and again",
    ],
    "anime": [
        "You'd give up on it early",
        "You'd finish it but forget it within a week",
        "You'd enjoy it once and not rewatch it",
        "You'd recommend it to a friend",
        "You'd rewatch it and count it among your favorites",
    ],
    "beer": [
        "You'd pour it out after a sip",
        "You'd finish the glass but not order it again",
        "You'd drink it again if it was what's on offer",
        "You'd order it again by name",
        "You'd seek it out and keep it stocked at home",
    ],
}
BINS = {  # rating -> level index
    "stars": lambda r: 0 if r <= 1.5 else 1 if r <= 2.5 else 2 if r <= 3.5 else 3 if r <= 4 else 4,
    "bgg": lambda r: 0 if r < 4 else 1 if r < 6 else 2 if r < 7.5 else 3 if r < 9 else 4,
    "mal": lambda r: 0 if r <= 3 else 1 if r <= 5 else 2 if r <= 7 else 3 if r == 8 else 4,
}
TARGETS = {
    "film": env_int("TARGET_TASTE_RATINGS_FILM", 4000),
    "book": env_int("TARGET_TASTE_RATINGS_BOOK", 3000),
    "board_game": env_int("TARGET_TASTE_RATINGS_BOARD_GAME", 2500),
    "anime": env_int("TARGET_TASTE_RATINGS_ANIME", 1500),
    "beer": env_int("TARGET_TASTE_RATINGS_BEER", 1500),
}
MIN_N = {"film": 300, "book": 2000, "board_game": 500, "anime": 300, "beer": 100}
LICENSES = {  # the pools' own adapters (one download each)
    "film": "movielens_pairs", "book": "goodreads_pairs", "board_game": "boardgame_pairs", "anime": "anime_pairs",
    "beer": "beer_pairs",
}


def _pairs_module(name: str):
    path = Path(__file__).resolve().parents[1] / name / "adapter.py"
    spec = importlib.util.spec_from_file_location(f"_ratings_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(raw_dir: Path) -> None:
    missing = [d for d in ("movielens_pairs", "goodreads_pairs", "boardgame_pairs", "anime_pairs", "beer_pairs")
               if not (RAW / d).exists()]
    if missing:
        raise SystemExit(f"run `askjev source {' '.join(missing)}` first: this adapter reads their raw files")


def _dist(values: pl.Series, scale: str) -> tuple[dict[str, float], int]:
    counts = [0] * 5
    for v, c in values.value_counts().iter_rows():
        counts[BINS[scale](v)] += c
    n = sum(counts)
    return {str(i): round(c / n, 4) for i, c in enumerate(counts)}, n


def _q(domain: str, text: str, item_id, dist: dict, n: int, population: str, src: str, node: str,
       flags: set, meta: dict) -> Question:
    return Question(
        text=text, primitive="score", hemisphere="self", kind="taste", origin="template", source=NAME,
        options=LEVELS[domain], node_hint=node, source_item_id=f"{domain}:{item_id}", license=_pairs_module(LICENSES[domain]).LICENSE,
        template_id=f"taste_ratings.{domain}",
        human=[HumanDist(population=population, distribution=dist, n=n, source=src)],
        meta={"domain": domain, **meta, **({"flags": sorted(flags)} if flags else {})},
    )


def _films() -> Iterator[Question]:
    m = _pairs_module("movielens_pairs")
    ratings = pl.read_parquet(RAW / "movielens_pairs" / "ratings.parquet")
    m.MIN_RATINGS = MIN_N["film"]
    films = hash_order(m._films(RAW / "movielens_pairs", ratings)[:TARGETS["film"] * 2], lambda f: str(f["id"]), SALT)
    films = sorted(films[:TARGETS["film"]], key=lambda f: f["id"])
    by_id = ratings.filter(pl.col("movieId").is_in([f["id"] for f in films])).partition_by("movieId", as_dict=True)
    for f in films:
        dist, n = _dist(by_id[(f["id"],)]["rating"], "stars")
        yield _q("film", f"How much would you enjoy watching {f['name']} ({f['year']})?", f["id"], dist, n,
                 "MovieLens users who rated the film", "MovieLens 32M star ratings (1995-2023), binned to levels",
                 f"{NODE}.film_ratings", set(), {"movie_id": f["id"], "genres": sorted(f["genres"]),
                                                 "binning": "stars <=1.5|2-2.5|3-3.5|4|4.5-5"})


def _books() -> Iterator[Question]:
    m = _pairs_module("goodreads_pairs")
    books_csv = pl.read_csv(RAW / "goodreads_pairs" / "books.csv", infer_schema_length=20000)
    counts = books_csv.select("book_id", pl.col("work_ratings_count").alias("n")).filter(pl.col("n") >= MIN_N["book"])
    books = m._books(RAW / "goodreads_pairs", counts)
    books = sorted(hash_order(books, lambda b: str(b["id"]), SALT)[:TARGETS["book"]], key=lambda b: b["id"])
    stars = {r["book_id"]: [r[f"ratings_{i}"] for i in range(1, 6)] for r in books_csv.iter_rows(named=True)}
    for b in books:
        c = stars[b["id"]]
        n = sum(c)
        dist = {str(i): round(x / n, 4) for i, x in enumerate(c)}
        yield _q("book", f"How much would you enjoy reading {b['title']} by {b['author']}?", b["id"], dist, n,
                 "Goodreads users who rated the book", "goodbooks-10k Goodreads rating counts (1-5 stars, 2017)",
                 f"{NODE}.book_ratings", b["flags"], {"book_id": b["id"], "genre": b["genre"], "year": b["year"],
                                                      "binning": "stars 1|2|3|4|5"})


def _games() -> Iterator[Question]:
    m = _pairs_module("boardgame_pairs")
    ratings = pl.read_parquet(RAW / "boardgame_pairs" / "ratings.parquet").unique(["user", "ID"], keep="first")
    counts = ratings.group_by("ID").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_N["board_game"])
    games = m._games(RAW / "boardgame_pairs", counts)
    games = sorted(hash_order(games, lambda g: str(g["id"]), SALT)[:TARGETS["board_game"]], key=lambda g: g["id"])
    by_id = ratings.filter(pl.col("ID").is_in([g["id"] for g in games])).partition_by("ID", as_dict=True)
    for g in games:
        dist, n = _dist(by_id[(g["id"],)]["rating"], "bgg")
        yield _q("board_game", f"How much would you enjoy playing {m._label(g)}?", g["id"], dist, n,
                 "BoardGameGeek users who rated the game", "BoardGameGeek user ratings (1-10), binned to levels",
                 f"{NODE}.board_game_ratings", g["flags"], {"bgg_id": g["id"], "weight": g["weight"],
                                                            "binning": "bgg <4|4-6|6-7.5|7.5-9|>=9"})


def _anime() -> Iterator[Question]:
    m = _pairs_module("anime_pairs")
    ratings = pl.read_csv(RAW / "anime_pairs" / "rating.csv").filter(pl.col("rating") > 0) \
        .unique(["user_id", "anime_id"], keep="first")
    counts = ratings.group_by("anime_id").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_N["anime"])
    m.MIN_MEMBERS = 20_000
    anime = m._anime(RAW / "anime_pairs", counts)
    anime = sorted(hash_order(anime, lambda a: str(a["id"]), SALT)[:TARGETS["anime"]], key=lambda a: a["id"])
    by_id = ratings.filter(pl.col("anime_id").is_in([a["id"] for a in anime])).partition_by("anime_id", as_dict=True)
    for a in anime:
        dist, n = _dist(by_id[(a["id"],)]["rating"], "mal")
        yield _q("anime", f"How much would you enjoy watching {a['name']} ({m.FORMATS[a['format']]})?", a["id"],
                 dist, n, "MyAnimeList users who rated it", "MyAnimeList user ratings (1-10), binned to levels",
                 f"{NODE}.anime_ratings", a["flags"], {"mal_id": a["id"], "genres": sorted(a["genres"]),
                                                       "binning": "mal 1-3|4-5|6-7|8|9-10"})


def _beers() -> Iterator[Question]:
    m = _pairs_module("beer_pairs")
    reviews = (
        pl.read_csv(RAW / "beer_pairs" / m.FILE)
        .filter(pl.col("review_profilename").is_not_null() & (pl.col("review_overall") > 0))
        .sort("review_time", "beer_beerid", "review_profilename")
        .unique(["review_profilename", "beer_beerid"], keep="first", maintain_order=True)
    )
    m.MIN_REVIEWS = MIN_N["beer"]
    beers = m._beers(reviews)
    beers = sorted(hash_order(beers, lambda b: str(b["id"]), SALT)[:TARGETS["beer"]], key=lambda b: b["id"])
    by_id = reviews.filter(pl.col("beer_beerid").is_in([b["id"] for b in beers])).partition_by("beer_beerid", as_dict=True)
    for b in beers:
        dist, n = _dist(by_id[(b["id"],)]["review_overall"], "stars")
        yield _q("beer", f"How much would you enjoy drinking {b['name']} by {b['brewery']} ({b['style']})?", b["id"],
                 dist, n, "BeerAdvocate reviewers of the beer", "BeerAdvocate overall scores (1-5), binned to levels",
                 f"{NODE}.beer_ratings", set(), {"beer_id": b["id"], "style": b["style"], "abv": b["abv"],
                                                 "binning": "stars <=1.5|2-2.5|3-3.5|4|4.5-5"})


def normalize(raw_dir: Path) -> Iterator[Question]:
    for gen in (_films, _books, _games, _anime, _beers):
        yield from gen()
