"""What a first name says about someone, per US birth records (docs/13 experiment 7).

Truth: US Social Security Administration baby-name records, 1880-2017 (every name given to 5+ babies in a year, by
sex recorded at birth), via the R package `babynames` (Wickham, CC0; the SSA data are public domain). Two questions
per name: the share of babies with that name who were recorded as girls (11 bins), and the decade in which the most
babies got the name (1880s-2010s). Framed as birth records, never as anyone's identity.

Names: 60 whose records are mixed (10-90% girls, at least 20,000 babies), 40 clear ones for contrast, and for the
decade question about 10 popular names peaking in each decade (at least 30,000 babies, a clear peak).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question

NAME = "baby_names"
NODE = "world.society.languages.personal_name"
LICENSE = "Public domain (US Social Security Administration); packaged by the R babynames package, CC0"
URL = "https://raw.githubusercontent.com/hadley/babynames/master/data/babynames.rda"

SHARE = {"f00": "Under 5%", **{f"f{v:02d}": f"{v - 5}-{v + 5}%" for v in range(10, 91, 10)}, "f100": "Over 95%"}
DECADES = {f"d{d}": f"The {d}s" for d in range(1880, 2011, 10)}


def fetch(raw_dir: Path) -> None:
    """The .rda is converted once to parquet (pyreadr is not a project dependency):
    `uvx --from pyreadr --with pyarrow python -c "import pyreadr; list(pyreadr.read_r('babynames.rda').values())[0].to_parquet('babynames.parquet')"`."""
    if not (raw_dir / "babynames.parquet").exists() and not (raw_dir / "babynames.rda").exists():
        urllib.request.urlretrieve(URL, raw_dir / "babynames.rda")


def _share_key(f: float) -> str:
    if f < 0.05:
        return "f00"
    if f > 0.95:
        return "f100"
    return f"f{min(90, max(10, 10 * round(f * 10))):02d}"


def _pick(df: pl.DataFrame, n: int, seed: int) -> pl.DataFrame:
    return df.sample(n=min(n, df.height), seed=seed) if df.height else df


def _q(text, options, set_, name, truth, **meta) -> Question:
    return Question(text=text, primitive="choice", hemisphere="world", kind="factual", origin="dataset", source=NAME,
                    options=options, node_hint=NODE, source_item_id=f"{set_}:{name}", license=LICENSE, truth=truth,
                    meta={"experiment": "names", "set": set_, "name": name, "ordered": True, **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    b = pl.read_parquet(raw_dir / "babynames.parquet").with_columns(pl.col("year").cast(pl.Int32))
    tot = b.group_by("name").agg(pl.col("n").sum().alias("total"),
                                 pl.col("n").filter(pl.col("sex") == "F").sum().alias("girls"))
    tot = tot.with_columns((pl.col("girls") / pl.col("total")).alias("f"))
    big = tot.filter(pl.col("total") >= 20_000)
    mixed = _pick(big.filter(pl.col("f").is_between(0.10, 0.90)).sort("name"), 60, 7)
    clear = _pick(big.filter((pl.col("f") < 0.02) | (pl.col("f") > 0.98)).sort("name"), 40, 7)
    for r in pl.concat([mixed, clear]).iter_rows(named=True):
        yield _q(f'Of all the babies born in the US and named "{r["name"]}" since 1880, what share were recorded as girls?',
                 SHARE, "share_girls", r["name"], _share_key(r["f"]), girls_share=round(r["f"], 4), babies=int(r["total"]))
    dec = b.with_columns((pl.col("year") // 10 * 10).alias("decade")).group_by("name", "decade").agg(pl.col("n").sum())
    dt = dec.group_by("name").agg(pl.col("n").sum().alias("total"), pl.col("decade").sort_by("n").last().alias("peak"),
                                  (pl.col("n").max() / pl.col("n").sum()).alias("peak_share"))
    dt = dt.filter((pl.col("total") >= 30_000) & (pl.col("peak_share") >= 0.25))
    picks = pl.concat([_pick(dt.filter(pl.col("peak") == d).sort("name"), 10, d) for d in range(1880, 2011, 10)])
    for r in picks.iter_rows(named=True):
        by = dec.filter(pl.col("name") == r["name"]).sort("decade")
        dist = {f"d{d}": round(n / r["total"], 4) for d, n in zip(by["decade"], by["n"])}
        yield _q(f'In which decade were the most US babies named "{r["name"]}" born?', DECADES, "peak_decade", r["name"],
                 f"d{r['peak']}", births_by_decade=dist, babies=int(r["total"]))
