"""How much standing does a job have? Two classic prestige studies (research pass 2, idea 23).

Human data (both via the R package carData, GPL-2, from Rdatasets):
- Duncan (1961): 45 US occupations from the 1947 NORC North-Hatt survey; `prestige` is the percentage of raters who
  gave the job "excellent" or "good" standing (also the share of incumbents with high income and education, from
  the 1950 census). Jev gets the survey's own five answers.
- Pineo & Porter (1967), as in Fox's carData `Prestige`: 102 Canadian occupations with mean prestige scores from a
  1965 national survey, plus 1971 census income, education and share of women.
Only aggregates are published, so the human side stays in meta (no distributions). The 2012 GSS prestige ratings
(Hout, Smith & Marsden 2015) were the first choice; their score file is no longer downloadable from NORC.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "occupation_prestige"
NODE = "world.money.careers.occupation_prestige"
LICENSE = "GPL-2 (R package carData: Duncan 1961 and Pineo & Porter 1967 prestige data), via Rdatasets"
URL = "https://vincentarelbundock.github.io/Rdatasets/csv/carData/{}.csv"
LEVELS = ["Poor standing: most people look down on this job",
          "Somewhat below average standing",
          "Average standing: an ordinary, respectable job",
          "Good standing: people think well of someone who does it",
          "Excellent standing: one of the most respected jobs there is"]
DUNCAN_NAMES = {"RR.engineer": "railroad engineer", "gas.stn.attendant": "gas station attendant", "soda.clerk": "soda fountain clerk",
                "streetcar.motorman": "streetcar motorman", "welfare.worker": "welfare worker", "shoe.shiner": "shoe shiner",
                "auto.repairman": "auto repairman", "factory.owner": "factory owner", "store.manager": "store manager",
                "mail.carrier": "mail carrier", "insurance.agent": "insurance agent", "store.clerk": "store clerk",
                "coal.miner": "coal miner", "taxi.driver": "taxi driver", "truck.driver": "truck driver",
                "machine.operator": "machine operator", "professor": "college professor", "minister": "minister",
                "conductor": "railroad conductor"}
PRESTIGE_NAMES = {"gov.administrators": "government administrators", "physio.therapsts": "physiotherapists",
                  "receptionsts": "receptionists", "computer.programers": "computer programmers",
                  "osteopaths.chiropractors": "osteopaths and chiropractors", "sewing.mach.operators": "sewing machine operators",
                  "slaughterers.1": "slaughterers", "tool.die.makers": "tool and die makers", "radio.tv.repairmen": "radio and TV repairmen",
                  "radio.tv.announcers": "radio and TV announcers", "tellers.cashiers": "bank tellers and cashiers",
                  "service.station.attendant": "service station attendants", "real.estate.salesmen": "real estate salesmen",
                  "commercial.travellers": "commercial travellers (traveling salesmen)", "rotary.well.drillers": "rotary well drillers",
                  "vocational.counsellors": "vocational counsellors", "newsboys": "newsboys (newspaper sellers)"}


def fetch(raw_dir: Path) -> None:
    for f in ("Duncan", "Prestige"):
        if not (raw_dir / f"{f}.csv").exists():
            urllib.request.urlretrieve(URL.format(f), raw_dir / f"{f}.csv")


def _a(noun: str) -> str:
    return ("an " if noun[0] in "aeiou" else "a ") + noun


def normalize(raw_dir: Path) -> Iterator[Question]:
    for r in csv.DictReader(open(raw_dir / "Duncan.csv")):
        noun = DUNCAN_NAMES.get(r["rownames"], r["rownames"].replace(".", " "))
        yield Question(
            text=f"How would you rate the general standing of {_a(noun)} as a job?", primitive="score",
            hemisphere="world", kind="evaluative", origin="dataset", source=NAME, options=LEVELS, node_hint=NODE,
            license=LICENSE, source_item_id=f"duncan:{r['rownames']}",
            meta={"experiment": "occupation_prestige", "set": "duncan_1947", "occupation": noun,
                  "good_or_excellent": float(r["prestige"]), "income_high": float(r["income"]),
                  "education_high": float(r["education"]), "type": r["type"]})
    for r in csv.DictReader(open(raw_dir / "Prestige.csv")):
        if r["rownames"] == "slaughterers.2":  # a second census code for the same title
            continue
        noun = PRESTIGE_NAMES.get(r["rownames"], r["rownames"].replace(".", " "))
        yield Question(
            text=f"How would you rate the general standing of {noun} as a job?", primitive="score",
            hemisphere="world", kind="evaluative", origin="dataset", source=NAME, options=LEVELS, node_hint=NODE,
            license=LICENSE, source_item_id=f"pineo_porter:{r['rownames']}",
            meta={"experiment": "occupation_prestige", "set": "pineo_porter_1965", "occupation": noun,
                  "prestige_mean": float(r["prestige"]), "income_1971": float(r["income"]),
                  "education_years": float(r["education"]), "women_pct": float(r["women"]), "type": r["type"]})
