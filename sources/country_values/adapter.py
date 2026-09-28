"""How much do people trust each other, and how many say they're happy, country by country.

Human data: the Integrated Values Surveys (World Values Survey + European Values Study), as processed and published by
Our World in Data (CC BY 4.0): per country and survey year, the share answering "Most people can be trusted" to
"Generally speaking, would you say that most people can be trusted or that you need to be very careful in dealing
with people?", and the share answering "very happy" or "quite happy" to "Taking all things together, would you say
you are very happy, quite happy, not very happy or not at all happy?". One question per country and indicator, for its
latest survey since 2010, naming the survey year; the answer is the published share in 5% bins.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "country_values"
NODE = "world.places.countries.values_surveys"
LICENSE = "CC BY 4.0 (Our World in Data, from the Integrated Values Surveys: WVS and EVS)"
BASE = "https://ourworldindata.org/grapher/{}.csv?v=1&csvType=full&useColumnShortNames=false"
SERIES = {
    "trust": ("self-reported-trust-attitudes", "Trust in others",
              'In the {year} World Values Survey or European Values Study in {c}, what share of people answered "most '
              'people can be trusted" (rather than "you need to be very careful in dealing with people")?'),
    "happy": ("share-of-people-who-say-they-are-happy", "Happiness: Happy",
              'In the {year} World Values Survey or European Values Study in {c}, what share of people said they were '
              '"very happy" or "quite happy"?'),
}
PCT = {f"p{v:03d}": f"{v}%" for v in range(0, 101, 5)}
THE = {"United States", "United Kingdom", "Netherlands", "Philippines", "Czechia", "Dominican Republic",
       "United Arab Emirates", "Central African Republic", "Democratic Republic of Congo", "Gambia"}


def fetch(raw_dir: Path) -> None:
    for slug, _, _ in SERIES.values():
        if not (raw_dir / f"{slug}.csv").exists():
            req = urllib.request.Request(BASE.format(slug), headers={"User-Agent": "Mozilla/5.0"})
            (raw_dir / f"{slug}.csv").write_bytes(urllib.request.urlopen(req).read())


def _key(v: float) -> str:
    return f"p{min(100, max(0, int(5 * round(v / 5)))):03d}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    for ind, (slug, col, tpl) in SERIES.items():
        last = {}
        for r in csv.DictReader(open(raw_dir / f"{slug}.csv")):
            if not r["Code"] or r["Code"].startswith("OWID") or int(r["Year"]) < 2010 or not r[col]:
                continue
            if r["Entity"] not in last or int(r["Year"]) > int(last[r["Entity"]]["Year"]):
                last[r["Entity"]] = r
        for c, r in sorted(last.items()):
            v = float(r[col])
            name = f"the {c}" if c in THE else c
            yield Question(
                text=tpl.format(year=r["Year"], c=name), primitive="choice", hemisphere="world", kind="factual",
                origin="dataset", source=NAME, options=PCT, node_hint=NODE, license=LICENSE,
                source_item_id=f"{ind}:{r['Code']}:{r['Year']}", truth=_key(v),
                meta={"experiment": "country_values", "set": ind, "country": c, "iso3": r["Code"], "year": int(r["Year"]),
                      "share": v, "ordered": True})
