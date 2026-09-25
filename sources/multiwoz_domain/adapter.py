"""MultiWOZ 2.2 (Budzianowski et al. 2018; Zang et al. 2020): 10k human-human Wizard-of-Oz dialogues between a
tourist and a Cambridge information desk, with the active service annotated on every user turn.

Template "multiwoz_domain.service": Choice "Which service does the user want in `message`?" over the services
(restaurant, hotel, attraction, train, taxi, hospital, police), truth = the service whose intent becomes active
on that user turn. Only turns that open a new service (exactly one service active, and it was not active on
the user's previous turn), so the message itself carries the request. Balanced across services.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "multiwoz_domain"
URL = "https://raw.githubusercontent.com/budzianowski/multiwoz/master/data/MultiWOZ_2.2/{split}/dialogues_{n}.json"
FILES = [(s, n) for s in ("train", "dev", "test") for n in ("001", "002")]
TARGET = env_int("TARGET_MULTIWOZ_DOMAIN", 2000)
LICENSE = "MIT"
TEXT = "Which service does the user want in `message`?"
SERVICES = {
    "restaurant": "Finding or booking a restaurant",
    "hotel": "Finding or booking a hotel or guesthouse",
    "attraction": "Finding a place to visit: museums, colleges, parks, theatres, nightlife",
    "train": "Finding or booking a train",
    "taxi": "Booking a taxi",
    "hospital": "Finding a hospital or hospital department",
    "police": "Contacting the police",
}


def fetch(raw_dir: Path) -> None:
    for s, n in FILES:
        out = raw_dir / f"{s}_{n}.json"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=s, n=n), follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_service: dict[str, list] = defaultdict(list)
    seen: set[str] = set()
    for s, n in FILES:
        for dlg in json.loads((raw_dir / f"{s}_{n}.json").read_text()):
            prev: set[str] = set()
            for t in dlg["turns"]:
                if t["speaker"] != "USER":
                    continue
                active = {f["service"] for f in t["frames"] if f.get("state", {}).get("active_intent", "NONE") != "NONE"}
                new = active - prev
                prev = active
                if len(active) != 1 or len(new) != 1:
                    continue
                svc = next(iter(new))
                msg = " ".join(t["utterance"].split())
                if svc not in SERVICES or len(msg.split()) < 4 or msg.lower() in seen:
                    continue
                seen.add(msg.lower())
                by_service[svc].append((f"{s}:{dlg['dialogue_id']}:{t['turn_id']}", msg, svc))
    # Round-robin over services in hash order (hospital and police are small and run out first).
    pools = {k: hash_order(v, lambda x: x[0], f"multiwoz.{k}") for k, v in by_service.items()}
    picked = []
    depth = 0
    while len(picked) < TARGET and any(depth < len(v) for v in pools.values()):
        for k in SERVICES:
            if k in pools and depth < len(pools[k]) and len(picked) < TARGET:
                picked.append(pools[k][depth])
        depth += 1
    for sid, msg, svc in sorted(picked):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SERVICES,
            state={"message": msg[:1500]},
            shape="route",
            node_hint="machine.support.routing",
            template_id="multiwoz_domain.service",
            source_item_id=sid,
            license=LICENSE,
            truth=svc,
            meta={},
        )
