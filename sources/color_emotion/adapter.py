"""Colors of feelings (docs/15 E41): which color goes with which emotion, against 7,387 people in 31 countries.

Human data: Jonauskaite et al., "Colour-emotion associations across adulthood" dataset (OSF 873df, CC BY 4.0), from
the International Colour-Emotion Association Survey (Jonauskaite et al. 2020, Psychological Science): each participant
saw 12 color terms and ticked any of 20 emotion concepts they associate with each. For an emotion, people's
distribution over colors is the share of all that emotion's color associations falling on each color (pooled, and
per country of origin); for a color, the same over emotions. People could tick several emotions per color, so these
are shares of associations, not single picks; Jev picks one.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import HumanDist, Question

NAME = "color_emotion"
NODE = "world.science.psychology_neuroscience.emotion.colors_of_emotions"
LICENSE = "CC BY 4.0 (Jonauskaite et al., Colour-emotion associations across adulthood, OSF 873df)"
URL = "https://osf.io/download/ndjws/"
COLORS = ["red", "orange", "yellow", "green", "turquoise", "blue", "purple", "pink", "brown", "black", "grey", "white"]
EMOTIONS = ["admiration", "amusement", "anger", "compassion", "contempt", "contentment", "disappointment", "disgust",
            "fear", "guilt", "hate", "interest", "joy", "love", "pleasure", "pride", "regret", "relief", "sadness", "shame"]
POP = "International Colour-Emotion Association Survey participants"


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "DATA.csv").exists():
        urllib.request.urlretrieve(URL, raw_dir / "DATA.csv")


def _dist(counts: dict[str, float]) -> dict[str, float]:
    t = sum(counts.values()) or 1
    return {k: v / t for k, v in counts.items()}


def normalize(raw_dir: Path) -> Iterator[Question]:
    d = pl.read_csv(raw_dir / "DATA.csv", infer_schema_length=20000)
    n_all = d["user"].n_unique()
    by_c = d.group_by("origincountry_full").agg(pl.col("user").n_unique().alias("n"), *[pl.col(e).sum() for e in EMOTIONS])
    tot = d.group_by("colour").agg(*[pl.col(e).sum() for e in EMOTIONS])
    tot_cc = d.group_by("origincountry_full", "colour").agg(*[pl.col(e).sum() for e in EMOTIONS])
    src = "OSF 873df DATA.csv; share of the emotion's color associations on each color"
    for e in EMOTIONS:
        pooled = _dist({r["colour"]: float(r[e]) for r in tot.iter_rows(named=True)})
        humans = [HumanDist(population=f"{POP}, 31 countries", distribution=pooled, n=n_all, source=src)]
        for c in by_c.iter_rows(named=True):
            sub = tot_cc.filter(pl.col("origincountry_full") == c["origincountry_full"])
            humans.append(HumanDist(population=f"{POP}, {c['origincountry_full']}", n=c["n"], source=src,
                                    distribution=_dist({r["colour"]: float(r[e]) for r in sub.iter_rows(named=True)})))
        yield Question(text=f'Which color do you associate most with the feeling "{e}"?', primitive="choice",
                       hemisphere="world", kind="perception", origin="dataset", source=NAME,
                       options={c: None for c in COLORS}, node_hint=NODE, license=LICENSE, source_item_id=f"emotion:{e}",
                       human=humans, meta={"experiment": "colors_of_feelings", "set": "emotion_to_color", "item": e})
    for col in COLORS:
        row = tot.filter(pl.col("colour") == col).row(0, named=True)
        pooled = _dist({e: float(row[e]) for e in EMOTIONS})
        yield Question(text=f"Which feeling do you associate most with the color {col}?", primitive="choice",
                       hemisphere="world", kind="perception", origin="dataset", source=NAME,
                       options={e: None for e in EMOTIONS}, node_hint=NODE, license=LICENSE, source_item_id=f"color:{col}",
                       human=[HumanDist(population=f"{POP}, 31 countries", distribution=pooled, n=n_all,
                                        source="OSF 873df DATA.csv; share of the color's emotion associations on each emotion")],
                       meta={"experiment": "colors_of_feelings", "set": "color_to_emotion", "item": col})
