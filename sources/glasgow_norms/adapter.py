"""Glasgow Norms (Scott, Keitel, Becirspahic, Yao & Sereno 2019): 5,553 English words rated on nine dimensions.

One Score question per (word, dimension) for six dimensions, each with concrete levels and the raters' mean/SD mapped
onto them as a normal distribution (as in lancaster). Perception: valence, arousal, size, imageability; evaluative:
familiarity, age of acquisition. Unused: gender association (sensitive), dominance (no concrete wording survives
"describe situations, not degrees"), concreteness (the `concreteness` source asks it over a far larger word list).
Words with a sense in brackets ("aim (objective)") are asked with that sense spelled out.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

_spec = importlib.util.spec_from_file_location(
    "sources.concreteness", Path(__file__).parents[1] / "concreteness" / "adapter.py")
_c = importlib.util.module_from_spec(_spec)
sys.modules["sources.concreteness"] = _c
_spec.loader.exec_module(_c)

NAME = "glasgow_norms"
FILE = "glasgow_norms.csv"
URL = ("https://static-content.springer.com/esm/art%3A10.3758%2Fs13428-018-1099-3/MediaObjects/"
       "13428_2018_1099_MOESM2_ESM.csv")  # Behavior Research Methods supplementary file
LICENSE = "CC BY 4.0 (Scott, Keitel, Becirspahic, Yao & Sereno 2019, Behavior Research Methods)"
SALT = "glasgow_norms-20260925"
MIN_SD = 0.3
FIVE_OF_9 = [2.6, 4.2, 5.8, 7.4]  # 1-9 scale in five equal bands
FIVE_OF_7 = [2.2, 3.4, 4.6, 5.8]  # 1-7 scale in five equal bands
AOA_EDGES = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5]  # the 1-7 AoA scale's own seven age bands

# column -> spec. `text`/`human` take {w} = the quoted word (with its sense if any). `where` filters the words.
DIMS: dict[str, dict] = {
    "VAL": dict(
        dim="valence", kind="perception", target=env_int("GLASGOW_VALENCE", 2000), edges=FIVE_OF_9, scale="1-9",
        text="How pleasant or unpleasant does the word {w} feel to you?",
        human="How pleasant or unpleasant does the word {w} feel to most people?",
        levels=[
            "Very unpleasant: it brings to mind something distressing, like pain, loss or cruelty",
            "Somewhat unpleasant: it brings to mind something mildly bad, awkward or annoying",
            "Neutral: it brings to mind nothing especially good or bad",
            "Somewhat pleasant: it brings to mind something mildly nice or welcome",
            "Very pleasant: it brings to mind something delightful, like joy, love or a treat",
        ],
    ),
    "AROU": dict(
        dim="arousal", kind="perception", target=env_int("GLASGOW_AROUSAL", 1500), edges=FIVE_OF_9, scale="1-9",
        text="How calming or stirring does the word {w} feel to you?",
        human="How calming or stirring does the word {w} feel to most people?",
        levels=[
            "Calming: it feels sleepy or soothing, like a quiet evening",
            "Mostly calm: it stirs little, like an everyday object on a shelf",
            "Neither: it is no more calming than stirring",
            "Somewhat stirring: it raises interest or alertness, like good news or a warning sign",
            "Intensely stirring: it jolts you awake, like danger, a thrill or a scream",
        ],
    ),
    "SIZE": dict(
        dim="size", kind="perception", target=env_int("GLASGOW_SIZE", 1500), edges=FIVE_OF_7, scale="1-7",
        where=lambda r: float(r["CNC.M"]) >= 5.0,  # size only means something for concrete words
        text="How big is the thing the word {w} refers to?",
        human="How big do most people judge the thing the word {w} refers to?",
        levels=[
            "Tiny: smaller than a coin, like an ant, a seed or a grain of sand",
            "Small: it fits in one hand, like a cup, a key or a phone",
            "Medium: about the size of a person, a chair or a bicycle",
            "Large: about the size of a car, a room or a house",
            "Enormous: as big as a mountain, a city, an ocean or bigger",
        ],
    ),
    "IMAG": dict(
        dim="imageability", kind="perception", target=env_int("GLASGOW_IMAGEABILITY", 1000), edges=FIVE_OF_7,
        scale="1-7",
        text="How easily does the word {w} bring a mental picture to your mind?",
        human="How easily does the word {w} bring a mental picture to most people's minds?",
        levels=[
            "No picture comes to mind at all",
            "Only a vague or forced picture comes to mind, after some thought",
            "A picture comes to mind with a little effort",
            "A clear picture comes to mind quickly",
            "A vivid, detailed picture comes to mind instantly",
        ],
    ),
    "FAM": dict(
        dim="familiarity", kind="evaluative", target=env_int("GLASGOW_FAMILIARITY", 1500), edges=FIVE_OF_7,
        scale="1-7",
        text="How familiar is the word {w} to you?",
        human="How familiar is the word {w} to most people?",
        levels=[
            "Unknown: never seen or heard it before",
            "Rare: seen or heard it only a handful of times",
            "Occasional: come across it now and then, a few times a year",
            "Regular: come across it every week or two",
            "Everyday: come across it almost every day",
        ],
    ),
    "AOA": dict(
        dim="age_of_acquisition", kind="evaluative", target=env_int("GLASGOW_AOA", 1500), edges=AOA_EDGES,
        scale="1-7 (age bands 0-2, 2-4, 4-6, 6-8, 8-10, 10-12, 13+)",
        text="At what age do English speakers usually learn the word {w}?",
        human="At what age did most people learn the word {w}?",
        levels=[
            "As a baby or toddler, before age 2",
            "As a young child, between ages 2 and 4",
            "Around the start of school, between ages 4 and 6",
            "In the early school years, between ages 6 and 8",
            "In the middle school years, between ages 8 and 10",
            "In the late primary years, between ages 10 and 12",
            "As a teenager or adult, at 13 or older",
        ],
    ),
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _rows(raw_dir: Path) -> list[dict]:
    with open(raw_dir / FILE, newline="", encoding="utf-8-sig") as fh:
        rd = csv.reader(fh)
        top, sub = next(rd), next(rd)
        cols, cur = [], ""
        for t, s in zip(top, sub):
            cur = t or cur
            cols.append(f"{cur}.{s}" if s else cur)
        return [dict(zip(cols, r)) for r in rd if r and r[0].strip()]


def quoted(word: str) -> tuple[str, str, str | None]:
    """'aim (objective)' -> ('"aim" (in the sense "objective")', 'aim', 'objective')."""
    m = re.fullmatch(r"(.+?)\s*\((.+)\)", word.strip())
    if m:
        return f'"{m.group(1)}" (in the sense "{m.group(2)}")', m.group(1), m.group(2)
    return f'"{word.strip()}"', word.strip(), None


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = [r for r in _rows(raw_dir) if not _c.SLURS.match(quoted(r["Words"])[1])]
    for col, spec in DIMS.items():
        where = spec.get("where", lambda r: True)
        pool = [r for r in rows if r.get(f"{col}.M") and where(r)]
        picked = sorted(hash_order(pool, lambda r: r["Words"], f"{SALT}.{spec['dim']}")[: spec["target"]],
                        key=lambda r: r["Words"])
        print(f"glasgow_norms {spec['dim']}: pool {len(pool)}, picked {len(picked)}")
        for r in picked:
            w, head, sense = quoted(r["Words"])
            mean, sd, n = float(r[f"{col}.M"]), float(r[f"{col}.SD"]), int(float(r[f"{col}.N"]))
            meta = {"word": r["Words"], "dimension": spec["dim"], "mean": mean, "sd": sd, "scale": spec["scale"],
                    "dist_method": f"normal(mean, max(sd,{MIN_SD})) on the {spec['scale'].split(' ')[0]} scale, "
                                   f"cut at {', '.join(str(e) for e in spec['edges'])}"}
            flags = _c.word_flags(head)
            if flags:
                meta["flags"] = flags
            yield Question(
                text=spec["text"].format(w=w),
                primitive="score",
                hemisphere="world",
                kind=spec["kind"],
                origin="dataset",
                source=NAME,
                options=spec["levels"],
                node_hint=_c.word_node(head if sense is None else sense),  # "duck (crouch)" is not a bird
                human_text=spec["human"].format(w=w),
                source_item_id=f"{r['Words']}:{spec['dim']}",
                license=LICENSE,
                template_id=f"glasgow_norms.{spec['dim']}",
                human=[HumanDist(
                    population="Glasgow Norms raters (UK university students)",
                    distribution=_c.discretize(mean, sd, spec["edges"], MIN_SD),
                    n=n,
                    source="Glasgow Norms (Scott et al. 2019)",
                )],
                meta=meta,
            )
