"""Favorite colors from two public open-data surveys: Cohen's 2010 US online "Which of these colors do you most
prefer?" (7 named swatches + other) and Jonauskaite et al. 2021's Swiss favourite/least-favourite colour (open answer,
coded into 13 categories). One Choice per survey question with the answer shares, plus pairwise "Which color do you
like better: X or Y?" whose human split is, among respondents whose favorite was one of the two, the share for each."""

from __future__ import annotations

import csv
import itertools
from pathlib import Path
from typing import Iterator

import httpx
import openpyxl

from askjev.model import HumanDist, Question

NAME = "color_favorites"
COHEN_URL = "https://osf.io/download/pa75e/"  # OSF v6h48 "color preference survey 9-17-10.xlsx"
COHEN_FILE = "cohen_color_preference_survey.xlsx"
JON_URL = "https://osf.io/download/4frcn/"  # OSF ucrxq "Stage_2_DATA_personality_aggregated.csv"
JON_FILE = "jonauskaite_personality_aggregated.csv"
LICENSE = ("Public OSF open data, no license stated: Cohen (2013) 'Children's Gender and Parents' Color Preferences' "
           "osf.io/v6h48; Jonauskaite, Thalmayer, Müller et al. (2021, Psychological Science) osf.io/ucrxq")
COHEN_POP = "US online survey respondents (2010, Philip N. Cohen)"
COHEN_SRC = "Cohen 2010 color preference survey (osf.io/v6h48): share picking each swatch or writing in another color"
JON_POP = "French-speaking adults in Switzerland, mostly students (Jonauskaite et al. 2021)"
JON_SRC = "Jonauskaite et al. 2021 (osf.io/ucrxq): open answers coded into 13 colour categories"
NODE = "self.lifestyle.favorites"
MIN_PAIR_N = 20

COHEN_CODES = {1: "purple", 2: "blue", 3: "green", 4: "yellow", 5: "orange", 6: "red", 7: "pink"}
JON_CATS = {
    "Red": "red", "Orange": "orange", "Yellow": "yellow", "Yellow-Green": "yellow_green", "Green": "green",
    "Turquoise": "turquoise", "Blue": "blue", "Purple": "purple", "Pink": "pink", "Brown": "brown",
    "Black": "black", "Grey": "grey", "White": "white",
}
WORDS = {k: k.replace("_", "-") for k in list(JON_CATS.values()) + ["other"]}


def fetch(raw_dir: Path) -> None:
    for url, name in ((COHEN_URL, COHEN_FILE), (JON_URL, JON_FILE)):
        p = raw_dir / name
        if not p.exists():
            r = httpx.get(url, timeout=120, follow_redirects=True)
            r.raise_for_status()
            p.write_bytes(r.content)


def _cohen(raw_dir: Path) -> list[str]:
    wb = openpyxl.load_workbook(raw_dir / COHEN_FILE, read_only=True)
    rows = list(wb["raw"].iter_rows(values_only=True))[2:]  # 2 header rows
    out = []
    for r in rows:
        if r[0] is None:
            continue
        if r[4] in COHEN_CODES:
            out.append(COHEN_CODES[r[4]])
        elif r[5] and str(r[5]).strip():
            out.append("other")  # wrote in a color (or a comment) instead of picking a swatch
    return out


def _jon(raw_dir: Path) -> tuple[list[str], list[str]]:
    with open(raw_dir / JON_FILE, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    most = [JON_CATS[r["MostCat"]] for r in rows if r["MostCat"] in JON_CATS]
    least = [JON_CATS[r["LeastCat"]] for r in rows if r["LeastCat"] in JON_CATS]
    return most, least


def _share(vals: list[str], keys: list[str]) -> dict[str, float]:
    return {k: round(vals.count(k) / len(vals), 4) for k in keys}


def normalize(raw_dir: Path) -> Iterator[Question]:
    cohen = _cohen(raw_dir)
    most, least = _jon(raw_dir)
    cohen_keys = list(COHEN_CODES.values()) + ["other"]
    jon_keys = list(JON_CATS.values())

    yield Question(
        text="Which of these colors do you like most?", primitive="choice", hemisphere="self", kind="taste",
        origin="dataset", source=NAME,
        options={k: ("another color" if k == "other" else None) for k in cohen_keys},
        node_hint=NODE, source_item_id="cohen2010|favorite", license=LICENSE, template_id="color_favorites.cohen",
        human=[HumanDist(population=COHEN_POP, distribution=_share(cohen, cohen_keys), n=len(cohen), source=COHEN_SRC,
                         wave="2010")],
        meta={"note": "respondents saw 7 named color swatches plus an 'other (please specify)' box"},
    )
    for which, vals, text in (("favorite", most, "What is your favorite color?"),
                              ("least_favorite", least, "What is your least favorite color?")):
        yield Question(
            text=text, primitive="choice", hemisphere="self", kind="taste", origin="dataset", source=NAME,
            options={k: None for k in jon_keys}, node_hint=NODE, source_item_id=f"jonauskaite2021|{which}",
            license=LICENSE, template_id=f"color_favorites.jonauskaite_{which}",
            human=[HumanDist(population=JON_POP, distribution=_share(vals, jon_keys), n=len(vals), source=JON_SRC,
                             wave="2019-2020")],
            meta={"note": "open answer in French, coded by the authors into 13 categories"},
        )

    # Pairs: among respondents whose favorite is one of the two colors, the share for each.
    colors = sorted(set(COHEN_CODES.values()) | set(jon_keys))
    for a, b in itertools.combinations(colors, 2):
        human = []
        for vals, keys, pop, src, wave in ((cohen, cohen_keys, COHEN_POP, COHEN_SRC, "2010"),
                                           (most, jon_keys, JON_POP, JON_SRC, "2019-2020")):
            if a not in keys or b not in keys:
                continue  # that survey did not offer both colors
            na, nb = vals.count(a), vals.count(b)
            if na + nb >= MIN_PAIR_N:
                human.append(HumanDist(
                    population=pop, distribution={a: round(na / (na + nb), 4), b: round(nb / (na + nb), 4)},
                    n=na + nb, wave=wave,
                    source=src.split(":")[0] + ": among respondents whose favorite was one of the two, share for each"))
        if not human:
            continue
        yield Question(
            text=f"Which color do you like better: {WORDS[a]} or {WORDS[b]}?", primitive="choice", hemisphere="self",
            kind="taste", origin="template", source=NAME, options={a: None, b: None}, node_hint=NODE,
            source_item_id=f"pair|{a}|{b}", license=LICENSE, template_id="color_favorites.pair", human=human,
            meta={"derived_from": "favorite-color shares (conditional on the favorite being one of the two)"},
        )
