"""goodbooks-10k (Goodreads): pairwise "Which book would you rather read?" between two popular books of the
same genre, with the human split from users who rated both."""

from __future__ import annotations

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

NAME = "goodreads_pairs"
BASE = "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/"
FILES = ("ratings.csv", "books.csv", "book_tags.csv", "tags.csv")
LICENSE = "CC BY-SA 4.0 (goodbooks-10k, Zygmunt Zając)"
TARGET = env_int("TARGET_GOODREADS_PAIRS", 3000)
SALT = "goodreads_pairs.v1"
MIN_RATINGS = 500  # ratings in goodbooks-10k's ratings.csv (a 53k-user sample): 2,526 books
MIN_CORATERS = 50
MAX_PER_BOOK = 25
TEXT = "Which book would you rather read?"
ENGLISH = {"eng", "en-US", "en-GB", "en-CA", "en"}

# Goodreads shelf name -> genre bucket; a book's genre is the bucket with the most shelvings.
GENRES = {
    "fantasy": ["fantasy", "urban-fantasy", "epic-fantasy", "high-fantasy", "magic"],
    "science_fiction": ["science-fiction", "sci-fi", "dystopian", "dystopia"],
    "romance": ["romance", "chick-lit", "paranormal-romance", "contemporary-romance", "new-adult"],
    "mystery_thriller": ["mystery", "thriller", "crime", "suspense", "mystery-thriller"],
    "horror": ["horror"],
    "classics": ["classics", "classic"],
    "historical_fiction": ["historical-fiction"],
    "young_adult": ["young-adult", "ya", "teen"],
    "childrens": ["childrens", "children", "children-s", "children-s-books", "picture-books"],
    "comics": ["graphic-novels", "comics", "manga", "graphic-novel"],
    "nonfiction": ["non-fiction", "nonfiction", "history", "science", "philosophy", "biography", "memoir",
                   "self-help", "business", "psychology"],
    "poetry": ["poetry"],
}
SENSITIVE_TAGS = {"erotica", "erotic-romance", "bdsm", "erotic"}
POLITICAL_TAGS = {"politics", "political"}
# Books by politicians and contested-politics polemicists (flag political).
POLITICAL_AUTHORS = {"Barack Obama", "Michelle Obama", "Hillary Rodham Clinton", "Hillary Clinton", "Bill Clinton",
                     "Donald J. Trump", "Sarah Palin", "Ann Coulter", "Glenn Beck", "Bill O'Reilly", "Michael Moore",
                     "Al Franken", "Bernie Sanders", "Adolf Hitler", "Karl Marx", "Howard Zinn", "George W. Bush"}
TAG_FLAG_SHARE = 0.05  # a flag tag must hold at least this share of the book's shelvings
OMNIBUS = re.compile(r"\b(box(ed)? set|collection|omnibus|complete|boxset|trilogy|anthology)\b|#\d+\s*-\s*\d+", re.I)
SERIES = re.compile(r"\s*\(([^()]*#[^()]*)\)\s*$")


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, timeout=600, follow_redirects=True)
        r.raise_for_status()
        out.write_bytes(r.content)


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if len(s) > 40:
        s = s[:40].rsplit("_", 1)[0]
    return s


def _books(raw_dir: Path, counts: pl.DataFrame) -> list[dict]:
    books = pl.read_csv(raw_dir / "books.csv", infer_schema_length=20000).join(counts, on="book_id")
    tags = pl.read_csv(raw_dir / "tags.csv")
    bt = pl.read_csv(raw_dir / "book_tags.csv").join(tags, on="tag_id")
    bucket = {t: g for g, ts in GENRES.items() for t in ts}
    shelf: dict[int, dict[str, int]] = {}
    for gid, name, cnt in bt.select("goodreads_book_id", "tag_name", "count").iter_rows():
        if cnt > 0:
            d = shelf.setdefault(gid, {})
            d[name] = d.get(name, 0) + cnt
    out, seen = [], set()
    for row in books.sort("n", descending=True).iter_rows(named=True):
        if row["language_code"] is not None and row["language_code"] not in ENGLISH:
            continue
        raw_title = row["title"] or ""
        series = SERIES.search(raw_title)
        if OMNIBUS.search(raw_title):
            continue
        title = SERIES.sub("", raw_title).strip()
        author = (row["authors"] or "").split(",")[0].strip()
        if not title or not author or not any(ch.isalpha() for ch in title):
            continue
        slug = _slug(title)
        if not slug or (title.casefold(), author.casefold()) in seen:
            continue
        seen.add((title.casefold(), author.casefold()))
        tags_ = shelf.get(row["goodreads_book_id"], {})
        scores: dict[str, int] = {}
        for t, c in tags_.items():
            if t in bucket:
                scores[bucket[t]] = scores.get(bucket[t], 0) + c
        if not scores:
            continue
        total = sum(tags_.values()) or 1
        flags = set()
        if sum(c for t, c in tags_.items() if t in SENSITIVE_TAGS) / total >= TAG_FLAG_SHARE:
            flags.add("sensitive")
        if sum(c for t, c in tags_.items() if t in POLITICAL_TAGS) / total >= TAG_FLAG_SHARE:
            flags.add("political")
        if author in POLITICAL_AUTHORS:
            flags.add("political")
        year = row["original_publication_year"]
        out.append({
            "id": row["book_id"], "title": title, "author": author, "slug": slug, "n": row["n"],
            "genre": max(sorted(scores), key=lambda g: scores[g]), "flags": flags,
            "year": int(year) if year is not None else None,
            "series": series.group(1).split("#")[0].strip(" ,") if series else None,
        })
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    ratings = pl.read_csv(raw_dir / "ratings.csv")
    counts = ratings.group_by("book_id").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_RATINGS)
    books = _books(raw_dir, counts)
    ids = [b["id"] for b in books]
    sub = ratings.filter(pl.col("book_id").is_in(ids)).unique(["user_id", "book_id"], keep="first").sort("book_id", "user_id")
    arrays = {bid: (g["user_id"].to_numpy(), g["rating"].to_numpy())
              for (bid,), g in sub.group_by("book_id", maintain_order=True)}

    pairs = [
        (a, b)
        for a, b in itertools.combinations(sorted(books, key=lambda x: x["id"]), 2)
        if a["genre"] == b["genre"] and a["author"] != b["author"]
        and not (a["series"] and a["series"] == b["series"])
    ]
    uses: dict[int, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}-{p[1]['id']}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a["id"], 0) >= MAX_PER_BOOK or uses.get(b["id"], 0) >= MAX_PER_BOOK:
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
            ka, kb = f"{ka}_{_slug(a['author']).split('_')[-1]}", f"{kb}_{_slug(b['author']).split('_')[-1]}"
        if ka == kb:
            continue
        uses[a["id"]] = uses.get(a["id"], 0) + 1
        uses[b["id"]] = uses.get(b["id"], 0) + 1
        taken += 1
        flags = sorted(a["flags"] | b["flags"])
        opts = sorted([(ka, f"{a['title']} by {a['author']}"), (kb, f"{b['title']} by {b['author']}")])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="template",
            source=NAME,
            options=dict(opts),
            node_hint="self.lifestyle.leisure_hobbies",
            source_item_id=f"{a['id']}-{b['id']}",
            license=LICENSE,
            template_id="goodreads_pairs.read",
            human=[
                HumanDist(
                    population="Goodreads users who rated both books",
                    distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                    n=n,
                    source="goodbooks-10k ratings (Goodreads, 2017): share rating each book higher, ties split",
                )
            ],
            meta={
                "book_ids": [a["id"], b["id"]],
                "genre": a["genre"],
                "years": [a["year"], b["year"]],
                "ratings_n": [a["n"], b["n"]],
                **({"flags": flags} if flags else {}),
            },
        )
