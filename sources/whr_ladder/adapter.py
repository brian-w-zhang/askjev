"""How each country rates its life: the World Happiness Report ladder (docs/15 E15).

Truth: the Cantril ladder averages published in the World Happiness Report 2025 (Gallup World Poll, 2022-2024
averages), via Our World in Data (CC BY 4.0). Each country's question asks for its average on the 0-10 ladder,
answered in half-step bins; GDP per head (World Bank via OWID) and OWID region go in meta for the analysis only.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "whr_ladder"
NODE = "world.places.countries.life_ladder"
LICENSE = "CC BY 4.0 (Our World in Data; World Happiness Report 2025, Gallup World Poll)"
OWID = "https://ourworldindata.org/grapher/{g}.csv?v=1&csvType=full&useColumnShortNames=true"
FILES = {"ladder.csv": "happiness-cantril-ladder", "gdp-per-capita-worldbank.csv": "gdp-per-capita-worldbank",
         "continents-according-to-our-world-in-data.csv": "continents-according-to-our-world-in-data"}
YEAR = "2025"  # the WHR 2025 report: 2022-2024 averages
BINS = [("b00", "Below 3.0", -1, 3.0)] + [(f"b{int(lo * 10)}", f"{lo:.1f} to {lo + 0.5:.1f}", lo, lo + 0.5)
                                         for lo in [3.0 + 0.5 * i for i in range(10)]] + [("b80", "8.0 or above", 8.0, 99)]
OPTIONS = {k: d for k, d, _, _ in BINS}
NAMES = {"Congo": "the Republic of the Congo", "Democratic Republic of Congo": "the Democratic Republic of the Congo",
         "United States": "the United States", "United Kingdom": "the United Kingdom", "Netherlands": "the Netherlands",
         "Philippines": "the Philippines", "United Arab Emirates": "the United Arab Emirates", "Czechia": "Czechia",
         "Dominican Republic": "the Dominican Republic", "Gambia": "the Gambia", "Central African Republic": "the Central African Republic"}


def fetch(raw_dir: Path) -> None:
    for f, g in FILES.items():
        if not (raw_dir / f).exists():
            req = urllib.request.Request(OWID.format(g=g), headers={"User-Agent": "Mozilla/5.0"})
            (raw_dir / f).write_bytes(urllib.request.urlopen(req).read())


def _bin(v: float) -> str:
    return next(k for k, _, lo, hi in BINS if lo <= v < hi)


def normalize(raw_dir: Path) -> Iterator[Question]:
    gdp, region = {}, {}
    for r in csv.DictReader(open(raw_dir / "gdp-per-capita-worldbank.csv")):
        if r["code"] and r["ny_gdp_pcap_pp_kd"]:
            gdp[r["code"]] = float(r["ny_gdp_pcap_pp_kd"])  # rows are in year order: the last year wins
    for r in csv.DictReader(open(raw_dir / "continents-according-to-our-world-in-data.csv")):
        region[r["code"]] = r["owid_region"]
    for r in csv.DictReader(open(raw_dir / "ladder.csv")):
        if r["year"] != YEAR or not r["code"] or r["code"].startswith("OWID_") or not r["cantril_ladder_score"]:
            continue
        v, name = float(r["cantril_ladder_score"]), r["entity"]
        yield Question(
            text=("The Gallup World Poll asks people to imagine a ladder with steps numbered from 0 at the bottom, the "
                  "worst possible life for them, to 10 at the top, the best possible life, and to say which step they "
                  f"stand on now. What was the average answer in {NAMES.get(name, name)} in 2022-2024?"),
            primitive="choice", hemisphere="world", kind="factual", origin="dataset", source=NAME, options=OPTIONS,
            node_hint=NODE, license=LICENSE, source_item_id=r["code"], truth=_bin(v),
            meta={"experiment": "world_ladder", "country": name, "code": r["code"], "score": v, "gdp": gdp.get(r["code"]),
                  "region": region.get(r["code"]), "ordered": True})
