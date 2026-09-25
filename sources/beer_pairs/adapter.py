"""BeerAdvocate reviews: pairwise "Which beer would you rather drink?" between two widely reviewed beers of the
same style family, with the human split from reviewers who rated both."""

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

NAME = "beer_pairs"
URL = "https://huggingface.co/datasets/SWilliams20/Kaggle_Beer_Reviews/resolve/main/beer_reviews.csv"
FILE = "beer_reviews.csv"
LICENSE = "BeerAdvocate reviews (McAuley et al. 2012 via Kaggle 'Beer Reviews'), HF mirror SWilliams20/Kaggle_Beer_Reviews tagged MIT; research use"
TARGET = env_int("TARGET_BEER_PAIRS", 4000)
SALT = "beer_pairs.v1"
MIN_REVIEWS = 400  # BeerAdvocate reviews per beer: 808 beers, the widely known end of the catalog
MIN_CORATERS = 100
MAX_PER_BEER = 25
TEXT = "Which beer would you rather drink?"
# BeerAdvocate style -> family; first matching pattern wins (order matters: "Belgian IPA" is an IPA).
FAMILIES = [
    ("sour", r"Lambic|Gueuze|Flanders|Wild Ale|Berliner"),
    ("ipa", r"IPA|India Pale Ale|American Black Ale"),
    ("wheat", r"Weizen|Weiss|Witbier|Wheat Ale|Weizenbock"),
    ("stout_porter", r"Stout|Porter|Black & Tan"),
    ("belgian", r"Belgian|Dubbel|Tripel|Quadrupel|Saison|Bière"),
    ("strong_ale", r"Barleywine|Strong Ale|Old Ale|Scotch Ale|Winter Warmer|Wheatwine"),
    ("lager", r"Lager|Pils|Bock|Märzen|Schwarzbier|Dortmunder|Rauchbier|Malt Liquor|Kölsch|California Common|Cream Ale"),
    ("amber_brown", r"Amber|Brown Ale|Red Ale|Altbier|Scottish Ale|Rye Beer"),
    ("pale_ale", r"Pale Ale|Blonde Ale|Bitter"),
    ("specialty", r"Fruit|Pumpkin|Herbed|Chile|Sahti|Gruit|Smoked|Low Alcohol"),
]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    with httpx.stream("GET", URL, timeout=600, follow_redirects=True) as r:
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


def _family(style: str) -> str | None:
    for fam, pat in FAMILIES:
        if re.search(pat, style):
            return fam
    return None


def _clean(name: str) -> str:
    """'Stone IPA (India Pale Ale)' -> 'Stone IPA'; collapse whitespace."""
    name = re.sub(r"\s+", " ", name).strip()
    stripped = re.sub(r"\s*\((India Pale Ale|IPA)\)\s*$", "", name)
    return stripped or name


def _beers(reviews: pl.DataFrame) -> list[dict]:
    meta = (
        reviews.group_by("beer_beerid")
        .agg(pl.len().alias("n"), pl.col("beer_name").first(), pl.col("brewery_name").first(),
             pl.col("beer_style").first(), pl.col("beer_abv").first())
        .filter(pl.col("n") >= MIN_REVIEWS)
        .sort("n", "beer_beerid", descending=[True, False])
    )
    out = []
    for row in meta.iter_rows(named=True):
        fam = _family(row["beer_style"] or "")
        name = _clean(row["beer_name"] or "")
        brewery = re.sub(r"\s+", " ", row["brewery_name"] or "").strip()
        if not fam or not name or not brewery or not _slug(name):
            continue
        out.append({"id": row["beer_beerid"], "name": name, "brewery": brewery, "style": row["beer_style"],
                    "family": fam, "abv": row["beer_abv"], "slug": _slug(name), "n": row["n"]})
    # Generic names shared by several beers ("Imperial Stout", "India Pale Ale") get the brewery's first word.
    dup = {s for s in (b["slug"] for b in out) if sum(x["slug"] == s for x in out) > 1}
    for b in out:
        if b["slug"] in dup:
            b["slug"] = _slug(f"{b['brewery'].split()[0]} {b['name']}")
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    reviews = (
        pl.read_csv(raw_dir / FILE)
        .filter(pl.col("review_profilename").is_not_null() & (pl.col("review_overall") > 0))
        .sort("review_time", "beer_beerid", "review_profilename")
        .unique(["review_profilename", "beer_beerid"], keep="first", maintain_order=True)  # first review per user
    )
    beers = _beers(reviews)
    by_id = {x["id"]: x for x in beers}
    users = reviews.select("review_profilename").unique().sort("review_profilename").with_row_index("uid")
    sub = (
        reviews.filter(pl.col("beer_beerid").is_in(list(by_id)))
        .join(users, on="review_profilename")
        .sort("beer_beerid", "uid")
    )
    arrays = {bid: (g["uid"].to_numpy(), g["review_overall"].to_numpy())
              for (bid,), g in sub.group_by("beer_beerid", maintain_order=True)}

    pairs = [
        (a, b)
        for a, b in itertools.combinations(sorted(beers, key=lambda x: x["id"]), 2)
        if a["family"] == b["family"]
    ]
    uses: dict[int, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]['id']}-{p[1]['id']}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a["id"], 0) >= MAX_PER_BEER or uses.get(b["id"], 0) >= MAX_PER_BEER:
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
        if ka == kb:  # e.g. two breweries' "Oatmeal Stout"
            ka, kb = _slug(f"{a['brewery'].split()[0]} {a['name']}"), _slug(f"{b['brewery'].split()[0]} {b['name']}")
        if ka == kb:
            continue
        uses[a["id"]] = uses.get(a["id"], 0) + 1
        uses[b["id"]] = uses.get(b["id"], 0) + 1
        taken += 1
        opts = sorted([(ka, f"{a['name']} by {a['brewery']} ({a['style']})"),
                       (kb, f"{b['name']} by {b['brewery']} ({b['style']})")])
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=dict(opts),
            node_hint="self.lifestyle.food_preferences",
            source_item_id=f"{a['id']}-{b['id']}",
            license=LICENSE,
            template_id="beer_pairs.drink",
            human=[
                HumanDist(
                    population="BeerAdvocate reviewers who rated both beers",
                    distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                    n=n,
                    source="BeerAdvocate reviews (1998-2012): share giving each beer the higher overall score, ties split",
                )
            ],
            meta={
                "beer_ids": [a["id"], b["id"]],
                "family": a["family"],
                "styles": [a["style"], b["style"]],
                "abv": [a["abv"], b["abv"]],
                "reviews_n": [a["n"], b["n"]],
            },
        )
