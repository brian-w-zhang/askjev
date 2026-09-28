"""How big, how far, how many: Jev's estimates against 500 people's and the truth (docs/15 E29/44, "wisdom of the
crowd").

Human data: Simoiu, Sumanth, Mysore & Goel 2019, "Studying the 'Wisdom of Crowds' at Scale" (HCOMP;
github.com/stanford-policylab/wisdom-of-crowds, MIT): about 500 people answered each of 20 questions in 50 domains in
February 2017. The eight text-only numeric domains are used (celebrity ages, calories, city distances, country
populations, GDP per person, appliance wattage, dates in US history, how many countries fit in the continental US);
the image, audio and video domains are left out. Each person's number goes into the same ordered bins Jev answers
in; the bins are fixed per domain, not built around each answer. Time-bound questions are pinned to early 2017, when
people answered. Obvious typos in the original prompts are fixed (listed in FIXES).
"""

from __future__ import annotations

import csv
import io
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "crowd_estimates"
LICENSE = "MIT (stanford-policylab/wisdom-of-crowds, Simoiu et al. 2019)"
BASE = "https://raw.githubusercontent.com/stanford-policylab/wisdom-of-crowds/master/data/original/"


def _b(edges: list[float], fmt) -> list[tuple[str, str, float, float]]:
    """Bins from inner edges: [lo, hi) each; first open below, last open above."""
    out = [("b00", f"Under {fmt(edges[0])}", float("-inf"), edges[0])]
    for i in range(1, len(edges)):
        out.append((f"b{i:02d}", f"{fmt(edges[i - 1])} to {fmt(edges[i])}", edges[i - 1], edges[i]))
    out.append((f"b{len(edges):02d}", f"{fmt(edges[-1])} or more", edges[-1], float("inf")))
    return out


num = lambda x: f"{x:,.0f}"  # noqa: E731
DOMAINS = {  # domain id: (key, tree node, bins, how to phrase the question)
    "5": ("celebrity_age", "world.arts.celebrities", _b([20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75], num),
          lambda p: re.sub(r"^How old is (.+)\?$", r"How old was \1 in February 2017?", p)),
    "19": ("calories", "world.health.nutrition", _b([25, 50, 100, 150, 200, 300, 400, 600, 900, 1500], num), None),
    "22": ("city_distance", "world.places.cities",
           _b([100, 200, 300, 400, 500, 600, 700, 900, 1200, 1600, 2200, 3000], lambda x: f"{x:,.0f} miles"), None),
    "51": ("country_population", "world.places.countries",
           _b([5e6, 10e6, 15e6, 20e6, 30e6, 40e6, 60e6, 80e6, 120e6, 200e6, 300e6, 500e6, 1e9],
              lambda x: f"{x / 1e9:g} billion" if x >= 1e9 else f"{x / 1e6:g} million"),
           lambda p: re.sub(r"^What is the population of (.+)\?$", r"What was the population of \1 in 2016?", p)),
    "72": ("gdp_per_person", "world.places.countries",
           _b([1000, 2000, 4000, 7000, 10000, 15000, 20000, 30000, 40000, 55000, 75000], lambda x: f"${x:,.0f}"),
           lambda p: p.replace("What is the per-capita GDP", "Around 2016, what was the per-capita GDP")),
    "81": ("appliance_watts", "world.tech.engineering_inventions.energy_power",
           _b([5, 10, 25, 50, 100, 200, 500, 1000, 1500, 2000, 3000], lambda x: f"{x:,.0f} watts"), None),
    "95": ("history_year", "world.history", _b(list(range(1575, 2000, 25)), lambda x: f"{x:.0f}"), None),
    "97": ("country_size_ratio", "world.places.countries",
           _b([1.5, 3, 5, 8, 12, 20, 30, 50, 80, 150, 300], lambda x: f"{x:g}"), None),
}
FIXES = {"+AC0-": "-", "+ACQ-": "$", "Malayesias": "Malaysias", "Mauritianias": "Mauritanias", "Pear Harbor": "Pearl Harbor",
         "Nepal n US": "Nepal in US", "tablespoon of olive contain": "tablespoon of olive oil contain"}


def fetch(raw_dir: Path) -> None:
    for f in ("tasks", "answers", "domains"):
        if not (raw_dir / f"{f}.csv").exists():
            data = urllib.request.urlopen(BASE + f"{f}.csv.zip").read()
            (raw_dir / f"{f}.csv").write_bytes(zipfile.ZipFile(io.BytesIO(data)).read(f"{f}.csv"))


def _num(s: str) -> float | None:
    s = s.replace(",", "").replace("$", "").strip()
    try:
        v = float(s)
    except ValueError:
        return None
    return v if v == v else None


def _bin(v: float, bins) -> str:
    return next(k for k, _, lo, hi in bins if lo <= v < hi)


def normalize(raw_dir: Path) -> Iterator[Question]:
    tasks = [t for t in csv.DictReader(open(raw_dir / "tasks.csv")) if t["domain_id"] in DOMAINS]
    ids = {t["task_id"] for t in tasks}
    answers: dict[str, list[float]] = {}
    for a in csv.DictReader(open(raw_dir / "answers.csv")):
        if a["task_id"] in ids and (v := _num(a["answer"])) is not None:
            answers.setdefault(a["task_id"], []).append(v)
    for t in tasks:
        key, node, bins, phrase = DOMAINS[t["domain_id"]]
        text = t["prompt"]
        for a, b in FIXES.items():
            text = text.replace(a, b)
        text = phrase(text) if phrase else text
        vals = answers.get(t["task_id"], [])
        truth = float(t["correct_answer"])
        dist = {k: 0.0 for k, *_ in bins}
        for v in vals:
            dist[_bin(v, bins)] += 1 / len(vals)
        yield Question(
            text=text, primitive="choice", hemisphere="world", kind="factual", origin="dataset", source=NAME,
            options={k: d for k, d, _, _ in bins}, node_hint=node, license=LICENSE, truth=_bin(truth, bins),
            source_item_id=f"{key}:{t['task_id']}",
            human=[HumanDist(population="US online participants (Simoiu et al. 2019, February 2017)", distribution=dist,
                             n=len(vals), source="stanford-policylab/wisdom-of-crowds answers.csv, numeric answers binned")],
            meta={"experiment": "crowd_estimates", "domain": key, "truth_value": truth, "ordered": True,
                  "crowd_median": sorted(vals)[len(vals) // 2] if vals else None, "crowd_n": len(vals)})
