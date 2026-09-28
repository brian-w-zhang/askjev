"""Which kills more? Yearly US deaths by cause, as Jev judges them, against people in 1978 and the real counts
(docs/15 E8).

Human data: Lichtenstein, Slovic, Fischhoff, Layman & Combs 1978, "Judged frequency of lethal events" (J. Exp.
Psych.: Human Learning and Memory 4:551-578): for 41 causes, US adults' estimates of yearly US deaths (geometric
means, 1970s) and the actual yearly deaths from vital statistics of the time. Taken from the machine-readable table
Pachur compiled for "The perception of dramatic risks" (Cognition 2024; OSF u4d7g, file Lichtenstein1978.xlsx).
Only group means are published, so people's estimates are kept in meta, not as a distribution.

Two versions per cause: as the 1978 study asked (with a reference cause: about 50,000 motor-vehicle deaths a year;
motor-vehicle accidents itself is left out of that version), and without the reference. Answers are 13 ordered bins
on a log scale, roughly half an order of magnitude each.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "lethal_events"
NODE = "world.health.causes_of_death"
LICENSE = ("Published research data (Lichtenstein et al. 1978, compiled by Pachur 2024, OSF u4d7g, open access); "
           "used for non-commercial research")
URL = "https://osf.io/download/7zs5g/"
BINS = [("d0", "None", 0, 0), ("d1", "1 to 9", 1, 9), ("d10", "10 to 29", 10, 29), ("d30", "30 to 99", 30, 99),
        ("d100", "100 to 299", 100, 299), ("d300", "300 to 999", 300, 999), ("d1k", "1,000 to 2,999", 1000, 2999),
        ("d3k", "3,000 to 9,999", 3000, 9999), ("d10k", "10,000 to 29,999", 10_000, 29_999),
        ("d30k", "30,000 to 99,999", 30_000, 99_999), ("d100k", "100,000 to 299,999", 100_000, 299_999),
        ("d300k", "300,000 to 999,999", 300_000, 999_999), ("d1m", "1 million or more", 1_000_000, float("inf"))]
OPTIONS = {k: d for k, d, _, _ in BINS}
# the table's labels, as a person would say them
PHRASE = {
    "Accidental falls": "accidental falls", "All accidents": "accidents of all kinds", "All cancer": "cancer (all kinds)",
    "All disease": "disease (all kinds)", "Appendicitis": "appendicitis", "Asthma": "asthma", "Botulism": "botulism",
    "Breast cancer": "breast cancer", "Diabetes": "diabetes", "Drowning": "drowning", "Electrocution": "electrocution",
    "Emphysema": "emphysema", "Excess cold": "excessive cold", "Fire and flames": "fire and flames",
    "Firearm accident": "firearm accidents", "Fireworks": "fireworks", "Flood": "floods", "Heart disease": "heart disease",
    "Homicide": "homicide", "Infectious hepatitis": "infectious hepatitis", "Leukemia": "leukemia", "Lightning": "lightning",
    "Lung cancer": "lung cancer", "Measles": "measles", "Motor vehicle accident": "motor vehicle accidents",
    "Motor-train collision": "collisions between trains and motor vehicles",
    "Nonvenomous animal": "attacks by non-venomous animals", "Poisoning by vitamins": "vitamin poisoning",
    "Poisoning solid/liquid": "accidental poisoning by solids or liquids", "Polio": "polio",
    "Pregnancy, abortion, and childbirth": "pregnancy, childbirth and abortion", "Smallpox": "smallpox",
    "Smallpox vaccination": "smallpox vaccination", "Stomach cancer": "stomach cancer", "Stroke": "stroke",
    "Suicide": "suicide", "Syphilis": "syphilis", "Tornado": "tornadoes", "Tuberculosis": "tuberculosis",
    "Venoumous bite or sting": "venomous bites or stings", "Whooping cough": "whooping cough",
}
ANCHOR = "For reference, about 50,000 people a year died in motor vehicle accidents. "


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "Lichtenstein1978.xlsx").exists():
        urllib.request.urlretrieve(URL, raw_dir / "Lichtenstein1978.xlsx")


def bin_of(v: float) -> str:
    v = round(v)
    return next(k for k, _, lo, hi in BINS if lo <= v <= hi)


def normalize(raw_dir: Path) -> Iterator[Question]:
    import openpyxl
    ws = openpyxl.load_workbook(raw_dir / "Lichtenstein1978.xlsx", data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    head = rows[0]
    for r in rows[1:]:
        d = dict(zip(head, r))
        if not d.get("Risk") or d["Risk"] not in PHRASE or d.get("ActualFrequencies") is None:
            continue
        cause, actual, est = d["Risk"], float(d["ActualFrequencies"]), float(d["Estimates"])
        base = f"In the United States in the mid-1970s, about how many people died each year from {PHRASE[cause]}?"
        meta = {"experiment": "lethal_events", "cause": cause, "actual_1970s": actual, "people_1978": round(est, 1),
                "people_bin": bin_of(est), "dramatic": d.get("Category_checked") == 1, "news_frequency": d.get("NewsFrequency")}  # dramatic: Pachur 2024 coding
        for version, text in (("anchored", ANCHOR + base), ("plain", base)):
            if version == "anchored" and cause == "Motor vehicle accident":
                continue
            yield Question(text=text, primitive="choice", hemisphere="world", kind="factual", origin="dataset", source=NAME,
                           options=OPTIONS, node_hint=NODE, license=LICENSE, truth=bin_of(actual),
                           source_item_id=f"{version}:{cause}", meta={**meta, "version": version, "ordered": True})
