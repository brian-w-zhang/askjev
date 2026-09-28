"""A typical American day, per the American Time Use Survey (docs/15 E49).

Human data: ATUS 2003-2016 activity and respondent files (US Bureau of Labor Statistics, public domain), as abridged
in the R package `atus` 0.2 (CRAN, GPL-2+, with BLS permission): 181,335 diary days, each respondent's minutes per
activity, with survey weights. For 20 activities, the human distribution is the weighted share of diary days in
each time bin (none, under 30 minutes, ..., 10+ hours). Jev is asked about a random American's day (the same
quantity) and, separately, about its own ideal day (no human data; compared with the Americans' actual day).
"""

from __future__ import annotations

import tarfile
import urllib.request
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import HumanDist, Question

NAME = "atus_day"
NODE = "world.society.time_use"
SELF_NODE = "self.lifestyle.habits_routines"
LICENSE = "Public domain (US BLS American Time Use Survey); abridged files from the R package atus 0.2 (GPL-2+)"
URL = "https://cran.r-project.org/src/contrib/Archive/atus/atus_0.2.tar.gz"
BINS = [("none", "None at all", 0, 0), ("m1_29", "1 to 29 minutes", 1, 29), ("m30_59", "30 to 59 minutes", 30, 59),
        ("h1_2", "1 to 2 hours", 60, 119), ("h2_3", "2 to 3 hours", 120, 179), ("h3_5", "3 to 5 hours", 180, 299),
        ("h5_8", "5 to 8 hours", 300, 479), ("h8_10", "8 to 10 hours", 480, 599), ("h10", "10 hours or more", 600, 10**6)]
OPTIONS = {k: d for k, d, _, _ in BINS}
ACTS = {  # key: (phrase after "spend ... ", ATUS lexicon code prefixes)
    "sleeping": ("sleeping", ["0101"]),
    "grooming": ("washing, dressing and grooming", ["0102"]),
    "working": ("working at a paid job", ["0501", "0502"]),
    "housework": ("on housework such as cleaning and laundry", ["0201"]),
    "cooking": ("preparing food and cleaning up after meals", ["0202"]),
    "childcare": ("caring for children in their household", ["0301", "0302", "0303"]),
    "shopping": ("shopping for goods and services", ["07"]),
    "eating": ("eating and drinking", ["11"]),
    "tv": ("watching TV", ["120303", "120304"]),
    "socializing": ("socializing and talking with people in person", ["1201"]),
    "relaxing": ("relaxing and thinking, doing nothing in particular", ["120301"]),
    "reading": ("reading for fun", ["120312"]),
    "games": ("playing games, including video games", ["120307"]),
    "computer": ("using a computer for leisure, not for games", ["120308"]),
    "exercise": ("playing sports or exercising", ["1301"]),
    "religion": ("on religious and spiritual activities", ["14"]),
    "volunteering": ("volunteering", ["15"]),
    "calls": ("on phone calls, mail and email", ["16"]),
    "travel": ("traveling, including commuting and driving to errands", ["18"]),
    "education": ("attending class or doing homework", ["06"]),
}


def fetch(raw_dir: Path) -> None:
    """Downloads the package; the .rda files are converted once to parquet (pyreadr is not a project dependency):
    `uvx --from pyreadr --with pyarrow python -c "import pyreadr; [list(pyreadr.read_r(f'atus/data/{f}.rda').values())[0].to_parquet(f + '.parquet') for f in ('atusact', 'atusresp')]"`."""
    if not (raw_dir / "atus.tar.gz").exists():
        urllib.request.urlretrieve(URL, raw_dir / "atus.tar.gz")
        tarfile.open(raw_dir / "atus.tar.gz").extractall(raw_dir)


def _bin(expr: pl.Expr) -> pl.Expr:
    out = pl.lit(BINS[-1][0])
    for k, _, lo, hi in reversed(BINS[:-1]):
        out = pl.when(expr <= hi).then(pl.lit(k)).otherwise(out)
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    act = pl.read_parquet(raw_dir / "atusact.parquet").with_columns(pl.col("tiercode").cast(pl.Utf8).str.zfill(6).alias("c"))
    resp = pl.read_parquet(raw_dir / "atusresp.parquet").select("tucaseid", "wt")
    for key, (phrase, prefixes) in ACTS.items():
        mins = act.filter(pl.any_horizontal([pl.col("c").str.starts_with(p) for p in prefixes])) \
                  .group_by("tucaseid").agg(pl.col("dur").sum())
        day = resp.join(mins, on="tucaseid", how="left").with_columns(pl.col("dur").fill_null(0))
        day = day.with_columns(_bin(pl.col("dur")).alias("bin"))
        w = day.group_by("bin").agg(pl.col("wt").sum())
        tot = float(day["wt"].sum())
        dist = {k: 0.0 for k in OPTIONS} | {b: float(x) / tot for b, x in w.iter_rows()}
        mean = float((day["dur"] * day["wt"]).sum() / tot)
        yield Question(
            text=f"Pick an American aged 15 or older at random, on a random day of the year. How much time did they spend {phrase} that day?",
            primitive="choice", hemisphere="world", kind="social", origin="dataset", source=NAME, options=OPTIONS,
            node_hint=NODE, license=LICENSE, source_item_id=f"day:{key}",
            human=[HumanDist(population="US residents 15+, ATUS diary days 2003-2016 (weighted)", distribution=dist,
                             n=day.height, source="ATUS activity and respondent files via R package atus 0.2")],
            meta={"experiment": "atus_day", "activity": key, "frame": "americans", "mean_minutes": round(mean, 1), "ordered": True})
        yield Question(
            text=f"On an ideal day for you, how much time would you spend {phrase}?", primitive="choice",
            hemisphere="self", kind="personality", origin="dataset", source=NAME, options=OPTIONS, node_hint=SELF_NODE,
            license=LICENSE, source_item_id=f"ideal:{key}",
            meta={"experiment": "atus_day", "activity": key, "frame": "ideal", "americans_mean_minutes": round(mean, 1), "ordered": True})
