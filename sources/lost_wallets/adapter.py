"""Lost wallets in 40 countries (research pass 2, idea 16): Cohn, Maréchal, Tannenbaum & Zünd 2019, "Civic honesty
around the globe", Science 365:70-73.

Truth: the study's behavioral data (Harvard Dataverse doi:10.7910/DVN/YKBODN, CC0; read from the public GitHub copy
bonjwow/lost-wallet because Dataverse asks for a guestbook form). 17,303 wallets were handed to reception staff in 355
cities; a wallet was "returned" when the recipient emailed the owner. Conditions: no money, about US$13.45 in local
currency, and (US, UK, Poland) about US$94.15. Each country-condition becomes one question asking for the return
rate in 5% bins; one more asks whether money makes return more or less likely (the study's headline: more).
"""

from __future__ import annotations

import csv
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "lost_wallets"
NODE = "world.places.countries.lost_wallets"
LICENSE = "CC0 1.0 (Cohn et al. 2019 replication data, Harvard Dataverse doi:10.7910/DVN/YKBODN)"
URL = "https://raw.githubusercontent.com/bonjwow/lost-wallet/HEAD/inputs/data/behavioral-data.csv"
PCT = {f"p{v:03d}": f"{v}%" for v in range(0, 101, 5)}
COND = {"0": ("no_money", "no money"), "1": ("money", "about 13 US dollars in local currency"),
        "2": ("big_money", "about 94 US dollars in local currency")}  # cond 3 (big money, no key) is left out
NAMES = {"UAE": "the United Arab Emirates", "UK": "the United Kingdom", "USA": "the United States",
         "Czech Republic": "the Czech Republic", "Netherlands": "the Netherlands"}
SETUP = ("In a field experiment in large cities in {c}, researchers handed lost wallets to staff at reception desks of "
         "banks, hotels, post offices, museums and public offices, saying they had found it on the street and asking the "
         "staff to take care of it. Each wallet was a clear card case with business cards showing the owner's name and "
         "email address, a grocery list, a key, and {m}. What share of the staff emailed the owner to return it?")


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "behavioral-data.csv").exists():
        urllib.request.urlretrieve(URL, raw_dir / "behavioral-data.csv")


def normalize(raw_dir: Path) -> Iterator[Question]:
    got: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in csv.DictReader(open(raw_dir / "behavioral-data.csv")):
        if r["cond"] in COND and r["response"] != "":
            got[(r["Country"], r["cond"])].append(float(r["response"]))
    for (country, cond), v in sorted(got.items()):
        rate = sum(v) / len(v) / 100  # response is coded 0 or 100
        key, words = COND[cond]
        yield Question(
            text=SETUP.format(c=NAMES.get(country, country), m=words), primitive="choice", hemisphere="world",
            kind="social", origin="dataset", source=NAME, options=PCT, node_hint=NODE, license=LICENSE,
            source_item_id=f"{country}:{key}", truth=f"p{int(5 * round(100 * rate / 5)):03d}",
            meta={"experiment": "lost_wallets", "country": country, "condition": key, "rate": round(rate, 4),
                  "wallets": len(v), "ordered": True})
    yield Question(
        text=("In a field experiment in 40 countries, lost wallets were handed to strangers at reception desks. Some "
              "wallets held no money and some held about 13 US dollars. Which wallets were returned to their owners "
              "more often?"),
        primitive="choice", hemisphere="world", kind="social", origin="dataset", source=NAME, node_hint=NODE,
        options={"with_money": "The wallets with money", "without_money": "The wallets without money",
                 "no_difference": "About the same"}, license=LICENSE, source_item_id="direction", truth="with_money",
        meta={"experiment": "lost_wallets", "condition": "direction"})
