"""Schema-Guided Dialogue (Rastogi et al., AAAI 2020; DSTC8): crowd-paraphrased task-oriented dialogues
between a user and a virtual assistant across 20 domains, with per-turn dialogue acts and the active
service intent. Dev + test splits (6,683 dialogues, including services unseen in training).

Templates:
- "sgd.intent" (Choice, route -> machine.ai_systems.function_calling): a user turn that states a new goal; which API intent (e.g. find_restaurants vs reserve_restaurant) does it call for? Options = every
  goal in the dev+test schemas (same-goal intents of different services merged, descriptions hand-written). Only
  user turns whose acts include INFORM_INTENT for the active intent (the user actually stated the goal), with a
  single frame, at least five words, and not a retry right after a failure notice. Truth = intent.
- "sgd.user_act" (Choice, classify -> machine.support.intent_topic): given the assistant's previous turn,
  what is the user's reply doing (give details, confirm, choose an offered option, ask for alternatives...)?
  Only user turns whose acts reduce to one act type (GOODBYE never occurs alone, so it is not an option).
  Truth = that act.
Both stratified round-robin over labels, seeded; user-text dedup within each template.
"""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int

NAME = "sgd_dialogue"
BASE = "https://raw.githubusercontent.com/google-research-datasets/dstc8-schema-guided-dialogue/master/{split}/{file}"
FILES = {"dev": 20, "test": 34}
LICENSE = "CC-BY-SA-4.0"
TARGET_INTENT = env_int("TARGET_SGD_INTENT", 2500)
TARGET_ACT = env_int("TARGET_SGD_ACT", 2000)
SEED = 8

INTENT_TEXT = "Which API intent should handle the user's request in `message`?"
ACT_TEXT = "What is the user doing in `user_reply`, their answer to the assistant's `assistant_turn`?"
# Intents that different services name differently for the same user goal are merged, so the choice is
# about the goal, not the service's naming (e.g. Music_1 PlaySong vs Music_3 PlayMedia).
MERGE = {
    "play_media": "play_song",
    "lookup_song": "lookup_music",
    "find_apartment": "find_home_by_area",
    "rent_movie": "play_movie",
}
# Hand-written descriptions (the schema's own are service-specific and sometimes misleading once merged).
INTENTS = {
    "add_alarm": "Set a new alarm",
    "book_appointment": "Book an appointment with a doctor, dentist, therapist or stylist",
    "book_house": "Book a vacation rental house for given dates",
    "buy_bus_ticket": "Buy tickets for a bus journey",
    "buy_event_tickets": "Buy tickets for a concert, game or other event",
    "buy_movie_tickets": "Buy cinema tickets for a particular showing",
    "check_balance": "Check the balance of a bank or payment account",
    "find_attractions": "Find tourist attractions to visit in a city",
    "find_bus": "Find a bus journey between two cities",
    "find_events": "Find concerts, games or other events in a city",
    "find_home_by_area": "Find an apartment or house to rent or buy in an area",
    "find_movies": "Find movies showing in cinemas, by genre, director or actor",
    "find_provider": "Find a doctor, dentist, therapist or stylist",
    "find_restaurants": "Find restaurants by location and cuisine",
    "find_trains": "Find train journeys to a city",
    "get_alarms": "List the alarms already set",
    "get_cars_available": "Search for rental cars available in a city on given dates",
    "get_ride": "Call a taxi or ride-share to a destination",
    "get_times_for_movie": "Get cinema show times for a movie",
    "get_train_tickets": "Book train tickets",
    "get_weather": "Get the weather for a place and date",
    "lookup_music": "Find songs, albums or artists matching a taste",
    "make_payment": "Send a payment to a friend or contact with a payment app",
    "play_movie": "Watch or rent a movie to stream online",
    "play_song": "Play a song or music on a device",
    "request_payment": "Request money from a friend or contact",
    "reserve_car": "Reserve a rental car",
    "reserve_hotel": "Book a hotel room",
    "reserve_restaurant": "Book a table at a restaurant",
    "schedule_visit": "Schedule a viewing of a property for rent or sale",
    "search_hotel": "Find a hotel in a place",
    "search_house": "Find a vacation rental house to stay in",
    "search_oneway_flight": "Search for one-way flights",
    "search_roundtrip_flights": "Search for round-trip flights",
    "share_location": "Send the user's location to a contact",
    "transfer_money": "Transfer money from a bank account to another account or person",
}

ACTS = {
    "INFORM": ("give_details", "Gives details the assistant needs, such as a date, place, time or preference"),
    "REQUEST": ("ask_for_information", "Asks the assistant a question about an option or booking"),
    "AFFIRM": ("confirm_details", "Says yes to the details the assistant read back for confirmation"),
    "NEGATE": ("reject_details", "Says no to the details the assistant read back, or to a question it asked"),
    "SELECT": ("choose_offered_option", "Picks or accepts an option the assistant offered"),
    "REQUEST_ALTS": ("ask_for_alternatives", "Asks to see other options than the one offered"),
    "INFORM_INTENT": ("start_new_task", "Starts a new request, such as finding or booking something"),
    "AFFIRM_INTENT": ("accept_suggested_task", "Accepts the assistant's offer to do a follow-up task, such as booking"),
    "NEGATE_INTENT": ("decline_suggested_task", "Turns down the assistant's offer to do a follow-up task"),
    "THANK_YOU": ("thank_assistant", "Thanks the assistant, possibly saying that is all they need"),
}
ACT_OPTIONS = {k: d for k, d in ACTS.values()}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", "", s.lower()).split())


def fetch(raw_dir: Path) -> None:
    for split, n in FILES.items():
        (raw_dir / split).mkdir(exist_ok=True)
        for f in ["schema.json"] + [f"dialogues_{i:03d}.json" for i in range(1, n + 1)]:
            out = raw_dir / split / f
            if out.exists():
                continue
            r = httpx.get(BASE.format(split=split, file=f), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def _round_robin(by_label: dict, target: int) -> list:
    rng = random.Random(SEED)
    labels = sorted(by_label)
    for lab in labels:
        rng.shuffle(by_label[lab])
    picked, cursor = [], {lab: 0 for lab in labels}
    while len(picked) < target:
        progressed = False
        for lab in labels:
            if len(picked) >= target:
                break
            if cursor[lab] < len(by_label[lab]):
                picked.append((lab, by_label[lab][cursor[lab]]))
                cursor[lab] += 1
                progressed = True
        if not progressed:
            break
    return picked


def normalize(raw_dir: Path) -> Iterator[Question]:
    schema_intents = {MERGE.get(_snake(it["name"]), _snake(it["name"]))
                      for split in FILES for svc in json.loads((raw_dir / split / "schema.json").read_text())
                      for it in svc["intents"]}
    assert schema_intents == set(INTENTS), schema_intents ^ set(INTENTS)
    intents = INTENTS

    by_intent: dict[str, list] = defaultdict(list)
    by_act: dict[str, list] = defaultdict(list)
    seen_i, seen_a = set(), set()
    for split, n in FILES.items():
        for i in range(1, n + 1):
            for dlg in json.loads((raw_dir / split / f"dialogues_{i:03d}.json").read_text()):
                turns = dlg["turns"]
                for t, turn in enumerate(turns):
                    if turn["speaker"] != "USER":
                        continue
                    utt = turn["utterance"].strip()
                    sid = f"{split}:{dlg['dialogue_id']}:{t}"
                    frames = turn["frames"]
                    acts = {a["act"] for f in frames for a in f["actions"]}
                    # intent: a single frame whose user acts state the active intent
                    prev_acts = {a["act"] for f in turns[t - 1]["frames"] for a in f["actions"]} if t else set()
                    if len(frames) == 1 and "NOTIFY_FAILURE" not in prev_acts:
                        f = frames[0]
                        active = f["state"]["active_intent"]
                        stated = any(a["act"] == "INFORM_INTENT" and active in a["values"] for a in f["actions"])
                        n_utt = _norm(utt)
                        if stated and active != "NONE" and n_utt not in seen_i and len(n_utt.split()) >= 5:
                            seen_i.add(n_utt)
                            by_intent[MERGE.get(_snake(active), _snake(active))].append((sid, utt, f["service"]))
                    # user act: one act type, mid-dialogue (there is a previous assistant turn)
                    if t > 0 and len(acts) == 1:
                        act = next(iter(acts))
                        prev = turns[t - 1]["utterance"].strip()
                        key = (_norm(prev)[:80], _norm(utt))
                        if act in ACTS and key not in seen_a and _norm(utt):
                            seen_a.add(key)
                            by_act[ACTS[act][0]].append((sid, utt, prev))
    assert set(by_intent) <= set(intents), set(by_intent) - set(intents)

    for lab, (sid, utt, svc) in _round_robin(by_intent, TARGET_INTENT):
        yield Question(
            text=INTENT_TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME,
            options=intents, state={"message": utt[:1500]}, shape="route",
            node_hint="machine.ai_systems.function_calling", template_id="sgd.intent", source_item_id=sid,
            license=LICENSE, truth=lab, meta={"service": svc},
        )
    # cap each act so near-duplicate "yes"/"thanks" replies do not dominate
    for lab in by_act:
        seen_u, keep = set(), []
        for x in by_act[lab]:
            u = _norm(x[1])
            if u not in seen_u:
                seen_u.add(u)
                keep.append(x)
        by_act[lab] = keep
    for lab, (sid, utt, prev) in _round_robin(by_act, TARGET_ACT):
        yield Question(
            text=ACT_TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME,
            options=ACT_OPTIONS, state={"assistant_turn": prev[:1000], "user_reply": utt[:1000]},
            shape="classify", node_hint="machine.support.intent_topic", template_id="sgd.user_act",
            source_item_id=sid, license=LICENSE, truth=lab,
        )
