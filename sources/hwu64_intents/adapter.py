"""HWU64 (Liu et al., IWSDS 2019, "Benchmarking Natural Language Understanding Services for building
Conversational Agents"): ~25k crowd-written commands to a home assistant, annotated with scenario + intent.

Template "hwu64.intent" (Choice, route): which of 64 fine-grained intents the command is. Keys =
"<scenario>_<intent>" from the dataset. Truth = the annotated intent.

Overlap: Amazon MASSIVE (source `massive_en`, scenario template) was built from these utterances, so every
utterance whose normalized text appears anywhere in MASSIVE en (train/validation/test) is excluded; what is
left (~11.7k) never appears in massive_en. Rows the authors marked irrelevant (status IRR*) are dropped, as are
the catch-all general_quirky the tiny cooking_query / audio_volume_other classes, general_greet (every usable greeting is also in MASSIVE), and commands of fewer
than three words (too ambiguous to label).
"""

from __future__ import annotations

import csv
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int

NAME = "hwu64_intents"
URL = ("https://raw.githubusercontent.com/xliuhw/NLU-Evaluation-Data/master/AnnotatedData/"
       "NLU-Data-Home-Domain-Annotated-All.csv")
MASSIVE = "https://huggingface.co/api/datasets/mteb/amazon_massive_intent/parquet/en/{split}/0.parquet"
LICENSE = "CC-BY-4.0"
TARGET = env_int("TARGET_HWU64_INTENTS", 2500)
SEED = 64
TEXT = "What does the user want the home assistant to do in `command`?"
DROP = {"general_quirky", "cooking_query", "audio_volume_other", "general_greet"}

INTENTS: dict[str, str] = {
    "alarm_query": "Ask which alarms are set",
    "alarm_remove": "Cancel or delete an alarm",
    "alarm_set": "Set an alarm or wake-up call",
    "audio_volume_down": "Turn the volume down",
    "audio_volume_mute": "Mute or silence the assistant",
    "audio_volume_up": "Turn the volume up",
    "calendar_query": "Ask about calendar events or appointments",
    "calendar_remove": "Delete a calendar event or reminder",
    "calendar_set": "Add a calendar event or set a reminder",
    "cooking_recipe": "Ask for a recipe or cooking advice",
    "datetime_convert": "Convert a time between time zones",
    "datetime_query": "Ask the current time or date",
    "email_addcontact": "Add a contact or an email address to contacts",
    "email_query": "Check or read emails or messages",
    "email_querycontact": "Ask for a contact's details",
    "email_sendemail": "Write or send an email or message",
    "general_affirm": "Tell the assistant it is right",
    "general_commandstop": "Tell the assistant to stop or shut down",
    "general_confirm": "Ask the assistant to confirm it understood",
    "general_dontcare": "Say it does not matter which option",
    "general_explain": "Ask the assistant to explain or rephrase",
    "general_joke": "Ask for a joke",
    "general_negate": "Tell the assistant it got something wrong",
    "general_praise": "Thank or praise the assistant",
    "general_repeat": "Ask the assistant to say it again",
    "iot_cleaning": "Start the robot vacuum or cleaning",
    "iot_coffee": "Make coffee with the coffee machine",
    "iot_hue_lightchange": "Change the light colour or mood",
    "iot_hue_lightdim": "Dim the lights",
    "iot_hue_lightoff": "Turn the lights off",
    "iot_hue_lighton": "Turn the lights on",
    "iot_hue_lightup": "Make the lights brighter",
    "iot_wemo_off": "Switch off a smart plug",
    "iot_wemo_on": "Switch on a smart plug",
    "lists_createoradd": "Create a list or add an item to one",
    "lists_query": "Ask what is on a list",
    "lists_remove": "Remove an item from a list or delete a list",
    "music_dislikeness": "Say they dislike the music playing",
    "music_likeness": "Say what music they like",
    "music_query": "Ask about the music playing",
    "music_settings": "Change playback settings like shuffle or repeat",
    "news_query": "Ask for news",
    "play_audiobook": "Play or control an audiobook",
    "play_game": "Play a game",
    "play_music": "Play music",
    "play_podcasts": "Play or control a podcast",
    "play_radio": "Play a radio station",
    "qa_currency": "Ask about a currency or exchange rate",
    "qa_definition": "Ask what a word or thing means",
    "qa_factoid": "Ask a general-knowledge question",
    "qa_maths": "Ask a maths or unit-conversion question",
    "qa_stock": "Ask about stock prices or the stock market",
    "recommendation_events": "Ask for events happening nearby",
    "recommendation_locations": "Ask for places to go, like restaurants or shops",
    "recommendation_movies": "Ask for a movie recommendation",
    "social_post": "Post or send something on social media",
    "social_query": "Ask what is happening on social media",
    "takeaway_order": "Order takeaway food",
    "takeaway_query": "Ask about takeaway options or an order's status",
    "transport_query": "Ask for directions or travel information",
    "transport_taxi": "Book a taxi or ride",
    "transport_ticket": "Book or check a train, bus or plane ticket",
    "transport_traffic": "Ask about traffic",
    "weather_query": "Ask about the weather",
}


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).split())


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "hwu64.csv"
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)
    for split in ("train", "validation", "test"):
        out = raw_dir / f"massive_en_{split}.parquet"
        if not out.exists():
            r = httpx.get(MASSIVE.format(split=split), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    massive = set()
    for split in ("train", "validation", "test"):
        massive.update(_norm(t) for t in pl.read_parquet(raw_dir / f"massive_en_{split}.parquet")["text"])
    by_label: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen: set[str] = set()
    with open(raw_dir / "hwu64.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            if (r["status"] or "").startswith("IRR"):
                continue
            lab = f"{r['scenario']}_{r['intent']}"
            if lab in DROP:
                continue
            text = (r["answer"] or "").strip()
            n = _norm(text)
            if len(n.split()) < 3 or n in seen or n in massive or _norm(r["answer_normalised"]) in massive:
                continue
            seen.add(n)
            by_label[lab].append((f"{r['userid']}:{r['answerid']}", text))
    assert set(by_label) == set(INTENTS), set(by_label) ^ set(INTENTS)
    rng = random.Random(SEED)
    labels = sorted(by_label)
    for lab in labels:
        rng.shuffle(by_label[lab])
    picked, cursor = [], {lab: 0 for lab in labels}
    while len(picked) < TARGET:
        progressed = False
        for lab in labels:
            if len(picked) >= TARGET:
                break
            if cursor[lab] < len(by_label[lab]):
                picked.append((lab, *by_label[lab][cursor[lab]]))
                cursor[lab] += 1
                progressed = True
        if not progressed:
            break
    for lab, sid, text in picked:
        yield Question(
            text=TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME, options=INTENTS,
            state={"command": text[:1500]}, shape="route", node_hint="machine.support.commands",
            template_id="hwu64.intent", source_item_id=sid, license=LICENSE, truth=lab, meta={"intent": lab},
        )
