"""Mental maps: which of two cities is farther north (or west)? Truth only, from coordinates.

Truth: GeoNames cities15000 (CC BY 4.0): latitude and longitude of every city over 15,000 people; well-known cities
only (over 1.5 million people, or a national capital over 300,000). People are known to misplace whole regions
(Friedman & Brown 2000: Europe is imagined farther south of North America than it is, so Rome "south of" New York;
Stevens & Coupe 1978: Reno is imagined east of Los Angeles because Nevada is east of California). No item-level
human data for these pairs was found, so the sets are built to test the same effects on Jev, and say so.

Sets (seeded samples, spread over the latitude or longitude gap):
- ns_eu_na: a European and a North American city, 0.5-6 degrees of latitude apart.
- ns_other: pairs across other regions (Asia-Europe, Africa-South America, Asia-North America).
- ns_us: two US cities (control: one country, one mental map).
- ew_us: two US cities 0.3-5 degrees of longitude apart: every pair (up to 80) where the city in the state that lies
  farther west (by the state's average longitude) is actually the eastern one, and as many ordinary pairs.
"""

from __future__ import annotations

import io
import random
import urllib.request
import zipfile
from itertools import combinations
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "mental_maps"
NODE = "world.places.continents_regions.mental_maps"
LICENSE = "CC BY 4.0 (GeoNames, geonames.org)"
BASE = "https://download.geonames.org/export/dump/"


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "cities15000.txt").exists():
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(BASE + "cities15000.zip").read()))
        z.extract("cities15000.txt", raw_dir)
    for f in ("countryInfo.txt", "admin1CodesASCII.txt"):
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(BASE + f, raw_dir / f)


def _cities(raw_dir: Path) -> list[dict]:
    countries = {}
    for line in open(raw_dir / "countryInfo.txt", encoding="utf-8"):
        if not line.startswith("#"):
            f = line.rstrip("\n").split("\t")
            countries[f[0]] = (f[4], f[8])  # name, continent
    states = {}
    for line in open(raw_dir / "admin1CodesASCII.txt", encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        states[f[0]] = f[1]
    out, seen = [], set()
    for line in open(raw_dir / "cities15000.txt", encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        name, lat, lon, code, cc, adm, pop = f[2], float(f[4]), float(f[5]), f[7], f[8], f[10], int(f[14] or 0)
        if not (pop >= 1_500_000 or (code == "PPLC" and pop >= 300_000)) or cc not in countries:
            continue
        country, cont = countries[cc]
        label = f"{name}, {states.get(f'{cc}.{adm}', country)}" if cc == "US" else f"{name}, {country}"
        if label in seen:
            continue
        seen.add(label)
        out.append({"label": label, "lat": lat, "lon": lon, "cc": cc, "cont": cont, "state": f"{cc}.{adm}", "pop": pop})
    # US cities over 1.5M are few: add US cities over 150,000 for the within-US sets
    for line in open(raw_dir / "cities15000.txt", encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if f[8] == "US" and int(f[14] or 0) >= 150_000 and f[7].startswith("PPL"):
            label = f"{f[2]}, {states.get(f'US.{f[10]}', 'US')}"
            if label not in seen:
                seen.add(label)
                out.append({"label": label, "lat": float(f[4]), "lon": float(f[5]), "cc": "US", "cont": "NA",
                            "state": f"US.{f[10]}", "pop": int(f[14])})
    return out


def _key(label: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in label.lower()).strip("_")


def _sample(pairs: list, n: int, gap, edges: list[float], seed: str) -> list:
    """n pairs spread evenly over the gap bands."""
    rng = random.Random(seed)
    bands = [[p for p in pairs if lo <= gap(p) < hi] for lo, hi in zip(edges, edges[1:])]
    out = []
    for b in bands:
        rng.shuffle(b)
        out += b[: n // len(bands)]
    return out


def _q(a: dict, b: dict, set_: str, direction: str, **meta) -> Question:
    far = (a if a["lat"] > b["lat"] else b) if direction == "north" else (a if a["lon"] < b["lon"] else b)
    ka, kb = _key(a["label"]), _key(b["label"])
    return Question(text=f"Which city is farther {direction}: {a['label']} or {b['label']}?", primitive="choice",
                    hemisphere="world", kind="factual", origin="dataset", source=NAME, options={ka: a["label"], kb: b["label"]},
                    node_hint=NODE, license=LICENSE, truth=_key(far["label"]), source_item_id=f"{set_}:{ka}|{kb}",
                    meta={"experiment": "mental_maps", "set": set_, "direction": direction, "a": a["label"], "b": b["label"],
                          "lat_gap": round(abs(a["lat"] - b["lat"]), 3), "lon_gap": round(abs(a["lon"] - b["lon"]), 3), **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    cs = _cities(raw_dir)
    big = [c for c in cs if c["pop"] >= 1_500_000 or c["cc"] != "US"]
    lat = lambda p: abs(p[0]["lat"] - p[1]["lat"])  # noqa: E731
    lon = lambda p: abs(p[0]["lon"] - p[1]["lon"])  # noqa: E731
    eu_na = [(a, b) for a, b in combinations(big, 2) if {a["cont"], b["cont"]} == {"EU", "NA"} and 0.5 <= lat((a, b)) < 6]
    for a, b in _sample(eu_na, 240, lat, [0.5, 2, 4, 6], "eu_na"):
        eu = a if a["cont"] == "EU" else b
        other = b if eu is a else a
        yield _q(a, b, "ns_eu_na", "north", europe_north=eu["lat"] > other["lat"], europe=eu["label"])
    other = [(a, b) for a, b in combinations(big, 2)
             if {a["cont"], b["cont"]} in ({"AS", "EU"}, {"AF", "SA"}, {"AS", "NA"}) and 0.5 <= lat((a, b)) < 6]
    for a, b in _sample(other, 150, lat, [0.5, 2, 4, 6], "other"):
        yield _q(a, b, "ns_other", "north", regions="-".join(sorted({a["cont"], b["cont"]})))
    us = [c for c in cs if c["cc"] == "US"]
    ns_us = [(a, b) for a, b in combinations(us, 2) if a["state"] != b["state"] and 0.5 <= lat((a, b)) < 6]
    for a, b in _sample(ns_us, 90, lat, [0.5, 2, 4, 6], "ns_us"):
        yield _q(a, b, "ns_us", "north")
    st_lon = {}
    for c in us:
        st_lon.setdefault(c["state"], []).append(c["lon"])
    st_lon = {k: sum(v) / len(v) for k, v in st_lon.items()}
    ew = [(a, b) for a, b in combinations(us, 2) if a["state"] != b["state"] and 0.3 <= lon((a, b)) < 5]

    def misleads(p):
        a, b = p
        return (a["lon"] < b["lon"]) != (st_lon[a["state"]] < st_lon[b["state"]])

    tricky = [p for p in ew if misleads(p)]
    random.Random("ew_tricky").shuffle(tricky)
    tricky = tricky[:80]
    plain = _sample([p for p in ew if not misleads(p)], len(tricky), lon, [0.3, 2, 5], "ew_us")
    for a, b in tricky + plain:
        yield _q(a, b, "ew_us", "west", state_misleads=misleads((a, b)))
