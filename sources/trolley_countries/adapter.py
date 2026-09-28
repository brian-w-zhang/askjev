"""Three trolley dilemmas in 42 countries (research pass 2, idea 13): Awad, Dsouza, Shariff, Rahwan & Bonnefon 2020,
"Universals and variations in moral decisions made in 42 countries by 70,000 participants", PNAS 117:2332-2337.

Human data: the paper's shared responses (OSF mxa6z, "Classic Trolley - Moral Machine website", public; no license
stated, used here for non-commercial research): 230,475 answers to the Switch, Loop and Footbridge dilemmas. Per
country with 200+ answers to each dilemma (42 countries, as in the paper), one question asks what share said they
would sacrifice the one (5% bins; truth = the observed share). Three more ask Jev the dilemmas themselves, with the
pooled answers of all 42 countries as the human distribution.
"""

from __future__ import annotations

import csv
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "trolley_countries"
NODE = "world.places.countries.trolley_by_country"
SELF_NODE = "self.values.moral_foundations"
LICENSE = "Public OSF data, no license stated (Awad et al. 2020, osf.io/mxa6z); non-commercial research use"
URL = "https://osf.io/download/c2qx5/"
PCT = {f"p{v:03d}": f"{v}%" for v in range(0, 101, 5)}
TROLLEY = "A runaway trolley is heading down the track toward five workers, who will be killed if it goes on. "
SCEN = {
    "Switch": (TROLLEY + "You can pull a lever to switch the trolley onto a side track, where it will kill one worker "
               "instead of the five.", "pull the lever"),
    "Loop": (TROLLEY + "You can pull a lever to switch the trolley onto a side track that loops back to the main track. "
             "One worker stands on the side track; his body will stop the trolley before it reaches the five, and he "
             "will be killed.", "pull the lever"),
    "Footbridge": (TROLLEY + "You are on a footbridge over the track, next to a large man. You can push him off the "
                   "bridge onto the track; his body will stop the trolley before it reaches the five, and he will be "
                   "killed.", "push the man"),
}
NAMES = {"Korea, Republic of": "South Korea", "Russian Federation": "Russia", "Taiwan, Province of China": "Taiwan",
         "Viet Nam": "Vietnam", "United States": "the United States", "United Kingdom": "the United Kingdom",
         "Czech Republic": "the Czech Republic", "Netherlands": "the Netherlands"}


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "allResponses.csv").exists():
        urllib.request.urlretrieve(URL, raw_dir / "allResponses.csv")


def normalize(raw_dir: Path) -> Iterator[Question]:
    got: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(raw_dir / "allResponses.csv")):
        if r["country_full"] not in ("", "NA"):
            got[r["country_full"]][r["Scenario"]].append(int(r["Outcome"]))
    keep = sorted(c for c, v in got.items() if min(len(v[s]) for s in SCEN) >= 200)
    for c in keep:
        for s, (story, act) in SCEN.items():
            v = got[c][s]
            share = sum(v) / len(v)
            yield Question(
                text=(f"An online survey asked visitors from {NAMES.get(c, c)} about this dilemma: {story} What share of "
                      f"them said they would {act}?"),
                primitive="choice", hemisphere="world", kind="social", origin="dataset", source=NAME, options=PCT,
                node_hint=NODE, license=LICENSE, source_item_id=f"{c}:{s}", truth=f"p{int(5 * round(100 * share / 5)):03d}",
                meta={"experiment": "trolley_countries", "country": c, "scenario": s, "share": round(share, 4),
                      "answers": len(v), "ordered": True})
    for s, (story, act) in SCEN.items():
        pooled = [x for c in keep for x in got[c][s]]
        yes = sum(pooled) / len(pooled)
        yield Question(
            text=f"{story} Would you {act}?", primitive="noul", hemisphere="self", kind="values", origin="dataset",
            source=NAME, options={"true": f"Yes, I would {act}", "false": f"No, I would not {act}"}, node_hint=SELF_NODE,
            license=LICENSE, source_item_id=f"self:{s}",
            human=[HumanDist(population=f"Moral Machine visitors from {len(keep)} countries (Awad et al. 2020)",
                             distribution={"true": yes, "false": 1 - yes}, n=len(pooled),
                             source="osf.io/mxa6z Shared_data_allResponses.csv, Outcome")],
            meta={"experiment": "trolley_countries", "scenario": s, "frame": "self"})
