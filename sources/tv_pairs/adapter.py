"""Netflix Prize (2006): pairwise "Which TV series would you rather watch?" between two TV series, with the human
split from Netflix customers who rated both.

Netflix listed TV series as season DVDs ("Friends: Season 3", "Red Dwarf: Series 2"). Only those season titles are
used: each season is mapped to its series, a customer's rating of a series is the mean of their ratings of its
seasons, and a pair's human distribution is the share of co-raters who rated each series higher (ties split).
`fetch` streams the 700 MB archive once and keeps only the season titles' ratings.
"""

from __future__ import annotations

import io
import itertools
import re
import tarfile
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "tv_pairs"
URL = "https://archive.org/download/nf_prize_dataset.tar/nf_prize_dataset.tar.gz"
TITLES = "movie_titles.txt"
RATINGS = "tv_season_ratings.parquet"
LICENSE = ("Netflix Prize dataset (2006): research use only, no redistribution, no commercial use, no Netflix "
           "endorsement; public mirror archive.org nf_prize_dataset.tar")
TARGET = env_int("TARGET_TV_PAIRS", 3000)
SALT = "tv_pairs-20260925"
MIN_RATERS = 1000  # distinct customers who rated any season of the series
MIN_CORATERS = 200
MAX_PER_SERIES = 40
TEXT = "Which TV series would you rather watch?"
HUMAN_TEXT = "Which TV series would most people rather watch?"

SEASON = re.compile(r"^(?P<series>.+?): (?:Season|Seasons|Series) (?P<num>\d+)\b(?P<rest>.*)$")
SKIP_REST = re.compile(r"bonus|special features|behind the scenes|extras", re.I)
# Seasons that are not the series itself, or reality/documentary adult programming.
SKIP_SERIES = {"Real Sex", "G-String Divas", "Taxicab Confessions", "Cathouse", "Girls Gone Wild"}
SENSITIVE_SERIES = {"Oz", "The Osbournes", "Queer as Folk", "The L Word", "Nip/Tuck", "Sex and the City",
                    "Red Shoe Diaries", "The Man Show", "Six Feet Under", "Deadwood", "Rome", "Carnivale", "South Park"}
POLITICAL_SERIES = {"The West Wing", "Michael Moore's The Awful Truth", "The Apprentice", "Real Time with Bill Maher",
                    "The Daily Show", "Politically Incorrect", "K Street", "Tanner '88", "Mr. Sterling", "Commander in Chief"}


def fetch(raw_dir: Path) -> None:
    if (raw_dir / RATINGS).exists() and (raw_dir / TITLES).exists():
        return
    raw_dir.mkdir(parents=True, exist_ok=True)
    tv: dict[int, str] | None = None
    frames = []
    with httpx.stream("GET", URL, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        stream = _Reader(r.iter_bytes(1 << 20))
        with tarfile.open(fileobj=stream, mode="r|gz") as outer:
            for m in outer:
                if m.name.endswith(TITLES):
                    data = outer.extractfile(m).read()
                    (raw_dir / TITLES).write_bytes(data)
                    tv = {mid: t for mid, t in _titles(data.decode("latin-1")).items() if _season(t)}
                elif m.name.endswith("training_set.tar"):
                    if tv is None:
                        raise RuntimeError("tv_pairs: training_set.tar came before movie_titles.txt")
                    with tarfile.open(fileobj=outer.extractfile(m), mode="r|") as inner:
                        for f in inner:
                            mm = re.search(r"mv_(\d+)\.txt$", f.name)
                            if not mm or int(mm.group(1)) not in tv:
                                continue
                            df = pl.read_csv(io.BytesIO(inner.extractfile(f).read()), skip_rows=1, has_header=False,
                                             new_columns=["user", "rating", "date"], schema_overrides={
                                                 "user": pl.Int32, "rating": pl.Int8, "date": pl.Utf8})
                            frames.append(df.select("user", "rating", movie=pl.lit(int(mm.group(1)), pl.Int16)))
                    break
    if tv is None or not frames:
        raise RuntimeError("tv_pairs: archive incomplete")
    pl.concat(frames).write_parquet(raw_dir / RATINGS)


class _Reader(io.RawIOBase):
    """File-like wrapper over an iterator of byte chunks (for tarfile stream mode)."""

    def __init__(self, it):
        self.it, self.buf = it, b""

    def readable(self) -> bool:
        return True

    def readinto(self, b) -> int:
        while not self.buf:
            try:
                self.buf = next(self.it)
            except StopIteration:
                return 0
        n = min(len(b), len(self.buf))
        b[:n], self.buf = self.buf[:n], self.buf[n:]
        return n


def _titles(text: str) -> dict[int, str]:
    out = {}
    for line in text.splitlines():
        mid, _, rest = line.partition(",")
        _, _, title = rest.partition(",")
        if mid.strip().isdigit():
            out[int(mid)] = title.strip()
    return out


def _season(title: str) -> str | None:
    m = SEASON.match(title)
    if not m or SKIP_REST.search(m.group("rest")):
        return None
    series = m.group("series").strip()
    series = re.sub(r"\s*\((?:Uncensored|Uncut)\)$", "", series)
    series = re.sub(r":\s*(?:Vol\.|Volume)\s*\d+$", "", series)  # "Family Guy: Vol. 1: Season 1"
    if series in SKIP_SERIES or series.startswith("The Best of "):  # compilations of another series
        return None
    return series


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if len(s) > 40:
        s = s[:40].rsplit("_", 1)[0]
    return s


def _franchise(series: str) -> str:
    """First distinctive word, so Star Trek: Voyager and Star Trek: The Next Generation never meet."""
    words = [w for w in re.findall(r"[a-z0-9]+", series.lower()) if w not in {"the", "a", "an"}]
    return " ".join(words[:2]) if words and words[0] == "star" else (words[0] if words else series)


def normalize(raw_dir: Path) -> Iterator[Question]:
    titles = _titles((raw_dir / TITLES).read_text(encoding="latin-1"))
    years: dict[str, list[int]] = {}
    for line in (raw_dir / TITLES).read_text(encoding="latin-1").splitlines():
        parts = line.split(",", 2)
        if len(parts) == 3 and parts[1].isdigit():
            s = _season(parts[2].strip())
            if s:
                years.setdefault(s, []).append(int(parts[1]))
    series_of = {mid: _season(t) for mid, t in titles.items() if _season(t)}
    r = pl.read_parquet(raw_dir / RATINGS).with_columns(
        series=pl.col("movie").replace_strict(series_of, default=None, return_dtype=pl.Utf8))
    per = (r.drop_nulls("series").group_by("series", "user").agg(score=pl.col("rating").cast(pl.Float32).mean())
           .sort("series", "user"))
    counts = per.group_by("series").len().filter(pl.col("len") >= MIN_RATERS)
    keep = sorted(counts["series"].to_list())
    slugs = {s: _slug(s) for s in keep}
    arrays = {s: (g["user"].to_numpy(), g["score"].to_numpy())
              for (s,), g in per.filter(pl.col("series").is_in(keep)).group_by("series", maintain_order=True)}
    n_raters = dict(counts.iter_rows())

    pairs = [(a, b) for a, b in itertools.combinations(keep, 2)
             if _franchise(a) != _franchise(b) and slugs[a] and slugs[b] and slugs[a] != slugs[b]]
    uses: dict[str, int] = {}
    taken = 0
    for a, b in hash_order(pairs, lambda p: f"{p[0]}|{p[1]}", SALT):
        if taken >= TARGET:
            break
        if uses.get(a, 0) >= MAX_PER_SERIES or uses.get(b, 0) >= MAX_PER_SERIES:
            continue
        ua, ra = arrays[a]
        ub, rb = arrays[b]
        _, ia, ib = np.intersect1d(ua, ub, assume_unique=True, return_indices=True)
        n = len(ia)
        if n < MIN_CORATERS:
            continue
        xa, xb = ra[ia], rb[ib]
        wins_a = float((xa > xb).sum()) + 0.5 * float((xa == xb).sum())
        uses[a] = uses.get(a, 0) + 1
        uses[b] = uses.get(b, 0) + 1
        taken += 1
        ka, kb = slugs[a], slugs[b]
        flags = sorted({"sensitive" for s in (a, b) if s in SENSITIVE_SERIES}
                       | {"political" for s in (a, b) if s in POLITICAL_SERIES})
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="taste",
            origin="template",
            source=NAME,
            options=dict(sorted([(ka, f"{a} (TV series)"), (kb, f"{b} (TV series)")])),
            node_hint="self.lifestyle.screens_media",
            human_text=HUMAN_TEXT,
            source_item_id=f"{a}|{b}",
            license=LICENSE,
            template_id="tv_pairs.watch",
            human=[HumanDist(
                population="Netflix customers who rated both series (1998-2005)",
                distribution={ka: round(wins_a / n, 4), kb: round(1 - wins_a / n, 4)},
                n=n,
                source="Netflix Prize training set: per customer, mean star rating over the series' season DVDs; "
                       "share rating each series higher, ties split",
            )],
            meta={"series": [a, b], "raters": [n_raters[a], n_raters[b]],
                  "season_years": [[min(years[a]), max(years[a])], [min(years[b]), max(years[b])]],
                  **({"flags": flags} if flags else {})},
        )
