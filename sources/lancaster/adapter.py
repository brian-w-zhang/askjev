"""Lancaster Sensorimotor Norms: "How much do you experience X by <sense>?" for 60 concrete words x 5 senses."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "lancaster"
FILE = "Lancaster_sensorimotor_norms_for_39707_words.csv"
URL = "https://osf.io/download/48wsc/"  # OSF node rwhs6 (Data component of 7emr6)
LICENSE = "CC BY 4.0 (Lynott, Connell, Brysbaert, Brand & Carney 2020)"
MIN_SD = 0.3  # floor so a unanimous 0.0 mean still gives a proper (near point-mass) distribution

# 60 common concrete words, hand-picked to spread across senses and topics. word -> node_hint.
WORDS = {
    **dict.fromkeys(
        "lemon onion garlic cheese bread chocolate strawberry banana bacon pepper honey popcorn".split(),
        "world.food.dishes_ingredients",
    ),
    **dict.fromkeys("coffee tea milk".split(), "world.food.nonalcoholic_drinks"),
    **dict.fromkeys("beer wine".split(), "world.food.alcoholic_drinks"),
    **dict.fromkeys("dog cat horse cow elephant lion".split(), "world.nature.mammals"),
    **dict.fromkeys("owl parrot crow".split(), "world.nature.birds"),
    **dict.fromkeys("shark whale crab".split(), "world.nature.sea_life"),
    **dict.fromkeys("snake bee mosquito lizard".split(), "world.nature.reptiles_insects"),
    **dict.fromkeys("rose pine grass mushroom lavender cactus".split(), "world.nature.plants_fungi"),
    **dict.fromkeys("thunder rain snow wind".split(), "world.nature.weather_climate"),
    **dict.fromkeys("rock sand".split(), "world.nature.geology"),
    **dict.fromkeys("ocean volcano".split(), "world.places.physical_geography"),
    **dict.fromkeys("piano drum violin trumpet".split(), "world.arts.music"),
    **dict.fromkeys("hammer knife sandpaper".split(), "world.tech.engineering_inventions"),
    "siren": "world.tech.gadgets",
    **dict.fromkeys("soap perfume smoke".split(), "world.science.chemistry"),
    "ice": "world.science.physics",
    "velvet": "world.arts.fashion",
}

# dimension column -> (gerund used in the question, noun used in the levels)
SENSES = {
    "Visual": ("seeing", "sight"),
    "Auditory": ("hearing", "sound"),
    "Gustatory": ("tasting", "taste"),
    "Olfactory": ("smelling", "smell"),
    "Haptic": ("feeling through touch", "touch"),
}


def _levels(gerund: str, noun: str) -> list[str]:
    return [
        f"Not at all: {gerund} plays no part in experiencing it",
        f"Slightly: its {noun} comes up only now and then, as a minor detail",
        f"Moderately: its {noun} is one noticeable part of experiencing it, alongside others",
        f"Strongly: its {noun} is one of the main ways I experience it",
        f"Greatly: {gerund} is central to experiencing it; its {noun} is what it is mostly about",
    ]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def discretize(mean: float, sd: float) -> dict[str, float]:
    """Normal(mean, sd) on the 0-5 rating scale, cut into 5 unit bins: <1, 1-2, 2-3, 3-4, >=4 (tails folded in)."""
    sd = max(sd, MIN_SD)
    cdf = [0.0] + [_phi((edge - mean) / sd) for edge in (1, 2, 3, 4)] + [1.0]
    p = [cdf[i + 1] - cdf[i] for i in range(5)]
    s = sum(p)
    return {str(i): v / s for i, v in enumerate(p)}


def normalize(raw_dir: Path) -> Iterator[Question]:
    with open(raw_dir / FILE, newline="", encoding="utf-8") as fh:
        rows = {r["Word"]: r for r in csv.DictReader(fh)}
    for word, node in WORDS.items():
        r = rows[word.upper()]
        n = int(float(r["N_known.perceptual"]))
        for dim, (gerund, noun) in SENSES.items():
            mean, sd = float(r[f"{dim}.mean"]), float(r[f"{dim}.SD"])
            yield Question(
                text=f'How much do you experience "{word}" by {gerund}?',
                primitive="score",
                hemisphere="world",
                kind="perception",
                origin="dataset",
                source=NAME,
                options=_levels(gerund, noun),
                node_hint=node,
                human_text=f'How much do most people experience "{word}" by {gerund}?',
                source_item_id=f"{word.upper()}:{dim}",
                license=LICENSE,
                human=[
                    HumanDist(
                        population="Lancaster norms raters",
                        distribution=discretize(mean, sd),
                        n=n,
                        source="Lancaster Sensorimotor Norms (OSF 7emr6)",
                    )
                ],
                meta={
                    "word": word,
                    "dimension": dim.lower(),
                    "mean_0_5": mean,
                    "sd": sd,
                    "dominant_perceptual": r["Dominant.perceptual"],
                    "dist_method": f"normal(mean, max(sd,{MIN_SD})) on the 0-5 scale, binned <1,1-2,2-3,3-4,>=4",
                },
            )
