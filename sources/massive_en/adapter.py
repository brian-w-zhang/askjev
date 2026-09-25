"""Amazon MASSIVE (FitzGerald et al. 2022), en-US: commands to a voice assistant labelled with 18 scenarios.

Template "massive_en.scenario": one Choice per command over the 18 scenarios, truth = the dataset scenario.
AmazonScience/massive is script-based (no parquet export), so the files come from the MTEB mirror
(mteb/amazon_massive_scenario + mteb/amazon_massive_intent, config "en", ids shared with MASSIVE).
Balanced round-robin across scenarios (and across intents within a scenario), all three splits pooled.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "massive_en"
BASE = "https://huggingface.co/api/datasets/mteb/amazon_massive_{kind}/parquet/en/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
LICENSE = "CC-BY-4.0"
TARGET = env_int("TARGET_MASSIVE_EN", 2500)
POLITICAL = re.compile(
    r"\b(elections?|presidential|campaign\w*|republican\w*|democrat\w*|trump|obama|clinton|biden|brexit|"
    r"abortion|gun control|immigra\w*|refugee\w*)\b",
    re.I,
)
TEXT = "Which smart-assistant scenario does `command` belong to?"

# Dataset scenario -> option key Jev sees (a few renamed for readability; meta.label_raw keeps the original).
KEYS = {"play": "play_media", "qa": "factual_question", "iot": "smart_home", "general": "chit_chat"}
SCENARIOS: dict[str, str] = {
    "alarm": "Setting, checking or removing alarms",
    "audio": "The device's own sound: volume up, down or mute",
    "calendar": "Calendar events and reminders: adding, checking or removing them",
    "cooking": "Recipes and how to cook something",
    "datetime": "The current time or date, or converting between time zones",
    "email": "Reading or sending email, and email contacts",
    "chit_chat": "Greetings, jokes, and casual or odd remarks to the assistant",
    "smart_home": "Controlling home devices: lights, plugs, robot vacuum, coffee machine",
    "lists": "Shopping and to-do lists: creating, adding to, checking or removing items",
    "music": "Information about or settings for music: what is playing, liking or disliking a song, shuffle or "
    "repeat (not starting playback)",
    "news": "News headlines and news on a topic",
    "play_media": "Starting playback: music, radio, podcasts, audiobooks or a game",
    "factual_question": "A factual question: definitions, facts, math, currency rates, stock prices",
    "recommendation": "Suggestions for events, places to go, or movies",
    "social": "Social media: posting or checking updates",
    "takeaway": "Ordering takeaway food or checking a takeaway order",
    "transport": "Travel and commuting: taxis, train or plane tickets, traffic, transport schedules",
    "weather": "Weather conditions and forecasts",
}


def fetch(raw_dir: Path) -> None:
    for kind in ("scenario", "intent"):
        for split in SPLITS:
            out = raw_dir / f"{kind}_{split}.parquet"
            if out.exists():
                continue
            r = httpx.get(BASE.format(kind=kind, split=split), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def _round_robin(pools: dict[str, list], n: int) -> list:
    out, cur = [], {k: 0 for k in pools}
    labels = sorted(pools)
    while len(out) < n:
        progressed = False
        for lab in labels:
            if len(out) >= n:
                break
            if cur[lab] < len(pools[lab]):
                out.append(pools[lab][cur[lab]])
                cur[lab] += 1
                progressed = True
        if not progressed:
            break
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    items = []  # (split, id, text, scenario, intent)
    seen: set[str] = set()
    for split in SPLITS:
        sc = pl.read_parquet(raw_dir / f"scenario_{split}.parquet")
        it = pl.read_parquet(raw_dir / f"intent_{split}.parquet").select("id", pl.col("label").alias("intent"))
        df = sc.join(it, on="id", how="left")
        assert df["intent"].null_count() == 0
        for mid, text, scen, intent in df.select("id", "text", "label", "intent").iter_rows():
            t = " ".join(text.split())
            if not t or t.lower() in seen:
                continue
            seen.add(t.lower())
            items.append((split, mid, t, scen, intent))
    assert {KEYS.get(x[3], x[3]) for x in items} == set(SCENARIOS)

    by_scen: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for x in hash_order(items, lambda x: f"{x[0]}:{x[1]}", "massive_en.scenario"):
        by_scen[x[3]][x[4]].append(x)
    pools = {s: _round_robin(dict(by_int), 10**9) for s, by_int in by_scen.items()}
    picked = _round_robin(pools, TARGET)

    for split, mid, text, scen, intent in sorted(picked, key=lambda x: (SPLITS.index(x[0]), int(x[1]))):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SCENARIOS,
            state={"command": text[:1500]},
            shape="classify",
            node_hint="machine.support.commands",
            template_id="massive_en.scenario",
            source_item_id=f"en/{split}:{mid}",
            license=LICENSE,
            truth=KEYS.get(scen, scen),
            meta={
                "split": split,
                "label_raw": scen,
                "intent": intent,
                **({"flags": ["political"]} if POLITICAL.search(text) else {}),
            },
        )
