"""What things cost, and what year Jev's prices come from (docs/15 E50 and E37).

Truth: US Bureau of Labor Statistics average retail prices, U.S. city average (series APU...), 1980-2026, public
domain; fetched from FRED (Federal Reserve Bank of St. Louis), which mirrors the BLS series, because the BLS file
server rejects scripted downloads. For 29 everyday items: the price "right now" (truth: the latest month, August
2026) and the price in 1985, 1995, 2005 and 2015 (truth: that year's average; only years the series fully covers).
Answers are 12 ordered price bins per item, log-spaced across the item's whole 1980-2026 range, so the bins don't
point at the answer. One more question asks what year it is. No human answers: this is Jev against the record.
"""

from __future__ import annotations

import csv
import math
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "bls_prices"
NODE = "world.money.economics.everyday_prices"
LICENSE = "Public domain (US Bureau of Labor Statistics average price data, via FRED)"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
ITEMS = {  # series id: what it is, as a person would say it
    "APU0000708111": "a dozen grade A large eggs", "APU0000709112": "a gallon of fresh whole milk",
    "APU0000702111": "a pound of white bread", "APU0000703112": "a pound of ground beef (100% beef)",
    "APU0000704111": "a pound of sliced bacon", "APU0000706111": "a pound of whole fresh chicken",
    "APU0000710212": "a pound of cheddar cheese", "APU0000711211": "a pound of bananas",
    "APU0000711311": "a pound of navel oranges", "APU0000712311": "a pound of field-grown tomatoes",
    "APU0000712112": "a pound of white potatoes", "APU0000715211": "a pound of white sugar",
    "APU0000717311": "a pound of ground roast coffee", "APU000074714": "a gallon of regular unleaded gasoline",
    "APU000072610": "a kilowatt-hour of electricity", "APU0000FF1101": "a pound of boneless chicken breast",
    "APU0000701111": "a pound of all-purpose white flour", "APU0000701312": "a pound of uncooked long-grain white rice",
    "APU0000702421": "a pound of chocolate chip cookies", "APU0000710411": "a half gallon of ice cream",
    "APU0000711412": "a pound of lemons", "APU0000712211": "a pound of iceberg lettuce",
    "APU000072511": "a gallon of heating oil", "APU000072620": "a therm of piped natural gas",
    "APU0000720111": "16 ounces of beer", "APU0000720311": "a liter of table wine",
    "APU0000714233": "a pound of dried beans", "APU0000704312": "a pound of boneless ham",
    "APU0000718311": "16 ounces of potato chips",
}
YEARS = [1985, 1995, 2005, 2015]
NOW = "2026-08"
NBINS = 12
YEAR_OPTIONS = {f"y{y}": str(y) for y in range(2016, 2031)}


def fetch(raw_dir: Path) -> None:
    for s in ITEMS:
        if not (raw_dir / f"{s}.csv").exists():
            urllib.request.urlretrieve(URL.format(s), raw_dir / f"{s}.csv")


def monthly(path: Path) -> dict[str, float]:
    out = {}
    for r in csv.reader(open(path)):
        if len(r) == 2 and r[1] not in ("", ".") and r[0][:1].isdigit():
            out[r[0][:7]] = float(r[1])
    return out


def annual(m: dict[str, float]) -> dict[int, float]:
    by: dict[int, list[float]] = {}
    for k, v in m.items():
        by.setdefault(int(k[:4]), []).append(v)
    return {y: sum(v) / len(v) for y, v in by.items() if len(v) == 12}


def nice(x: float) -> float:
    step = 0.01 if x < 1 else 0.05 if x < 5 else 0.1 if x < 20 else 0.5
    return round(round(x / step) * step, 2)


def bins(lo: float, hi: float) -> list[float]:
    """NBINS - 1 inner edges, log-spaced between 0.7 x the lowest and 1.4 x the highest yearly price."""
    a, b = math.log(lo * 0.7), math.log(hi * 1.4)
    edges = sorted({nice(math.exp(a + (b - a) * i / NBINS)) for i in range(1, NBINS)})
    return edges


def money(x: float) -> str:
    return f"${x:,.2f}"


def options(edges: list[float]) -> dict[str, str]:
    o = {"p00": f"Under {money(edges[0])}"}
    for i in range(1, len(edges)):
        o[f"p{i:02d}"] = f"{money(edges[i - 1])} to {money(edges[i] - 0.01)}"
    o[f"p{len(edges):02d}"] = f"{money(edges[-1])} or more"
    return o


def bin_of(v: float, edges: list[float]) -> str:
    return f"p{sum(v >= e for e in edges):02d}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    for s, what in ITEMS.items():
        m = monthly(raw_dir / f"{s}.csv")
        yr = annual(m)
        edges = bins(min(yr.values()), max(yr.values()))
        opts = options(edges)
        meta = {"experiment": "prices", "series": s, "item": what, "edges": edges, "ordered": True,
                "annual": {str(y): round(v, 3) for y, v in sorted(yr.items())}, "now_month": NOW, "now": m.get(NOW)}
        if m.get(NOW) is not None:
            yield Question(text=f"What is the average retail price of {what} in US cities right now?", primitive="choice",
                           hemisphere="world", kind="factual", origin="dataset", source=NAME, options=opts, node_hint=NODE,
                           license=LICENSE, truth=bin_of(m[NOW], edges), source_item_id=f"{s}:now",
                           meta={**meta, "when": "now"})
        for y in YEARS:
            if y in yr:
                yield Question(text=f"What was the average retail price of {what} in US cities in {y}?", primitive="choice",
                               hemisphere="world", kind="factual", origin="dataset", source=NAME, options=opts,
                               node_hint=NODE, license=LICENSE, truth=bin_of(yr[y], edges), source_item_id=f"{s}:{y}",
                               meta={**meta, "when": y})
    yield Question(text="What year is it right now?", primitive="choice", hemisphere="world", kind="factual",
                   origin="dataset", source=NAME, options=YEAR_OPTIONS, node_hint=NODE, license=LICENSE, truth="y2026",
                   source_item_id="current_year", meta={"experiment": "prices", "when": "year", "ordered": True})
