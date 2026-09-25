"""ATIS (Airline Travel Information System; Hemphill et al. 1990, Price 1990): transcribed spoken requests to an
airline travel information system, each labelled with the kind of information requested. HF mirror
`tuetschek/atis` (train + test, 5,871 utterances, lowercased).

Template "atis_intents.request": Choice "What travel information does `request` ask for?" over 15 request
types, truth = the dataset intent. Multi-intent labels ("flight+airfare") and types with fewer than 10
utterances are skipped. "flight" is 73% of ATIS, so it is capped at 700 and the other types are taken in
full (they sum to ~1,500).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "atis_intents"
URL = "https://huggingface.co/api/datasets/tuetschek/atis/parquet/default/{split}/0.parquet"
SPLITS = ("train", "test")
TARGET_FLIGHT = env_int("TARGET_ATIS_FLIGHT", 700)
LICENSE = "Unspecified on the HF mirror (ATIS corpus originally distributed by LDC)"
TEXT = "What travel information does `request` ask for?"
OPTIONS = {
    "flight": "Flights matching some criteria (route, dates, times, stops)",
    "airfare": "Ticket prices or fares",
    "ground_service": "Ground transportation (taxi, limousine, rental car, bus) at a city or airport",
    "ground_fare": "The price of ground transportation",
    "airline": "Which airlines fly somewhere, or information about an airline",
    "abbreviation": "What a code or abbreviation (fare code, airline code, meal code) means",
    "aircraft": "The type of aircraft used on a flight",
    "capacity": "How many passengers an aircraft or flight seats",
    "flight_time": "Departure or arrival times of a flight",
    "flight_no": "The flight number of a flight",
    "quantity": "How many flights, fares or other things there are",
    "airport": "Which airports serve a place, or information about an airport",
    "distance": "The distance between an airport and a city",
    "city": "Which city an airport or flight is in or serves",
    "meal": "Meals served on a flight",
}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list[tuple]] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for split in SPLITS:
        for rid, intent, text in pl.read_parquet(raw_dir / f"{split}.parquet").select("id", "intent", "text").iter_rows():
            t = re.sub(r" '(d|s|m|ll|re|ve)\b", r"'\1", " ".join(text.split()))
            if intent not in OPTIONS or len(t) < 8 or t in seen:
                continue
            seen.add(t)
            pools[intent].append((split, rid, t))

    picked = []
    for lab, items in pools.items():
        k = TARGET_FLIGHT if lab == "flight" else len(items)
        picked += [(lab, *x) for x in hash_order(items, lambda x: (x[0], x[1]), f"atis|{lab}")[:k]]
    picked.sort(key=lambda x: (x[1], x[2]))

    for lab, split, rid, t in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"request": t},
            shape="route",
            node_hint="machine.support.intent_topic",
            template_id="atis_intents.request",
            source_item_id=f"{split}:{rid}",
            license=LICENSE,
            truth=lab,
            meta={"split": split},
        )
