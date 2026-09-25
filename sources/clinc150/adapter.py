"""CLINC150 (Larson et al. 2019): queries to a task-oriented virtual assistant, 150 intents in 10 domains plus
out-of-scope queries that match none of them.

Template "clinc150.domain": Choice over the 10 domains + out_of_scope, truth = the domain of the labelled intent
(from the dataset's own domains.json), ~10% out-of-scope.
Template "clinc150.in_scope": Noul "is this a request the assistant supports", truth = not out-of-scope, ~40% OOS.
The two templates use disjoint messages. Source: HF clinc/clinc_oos, config "plus", test split.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "clinc150"
PARQUET = "https://huggingface.co/api/datasets/clinc/clinc_oos/parquet/plus/test/0.parquet"
INFO = "https://datasets-server.huggingface.co/info?dataset=clinc/clinc_oos&config=plus"
DOMAINS_URL = "https://raw.githubusercontent.com/clinc/oos-eval/master/data/domains.json"
LICENSE = "CC-BY-3.0"
TARGET_DOMAIN = env_int("TARGET_CLINC150", 2500)
TARGET_SCOPE = env_int("TARGET_CLINC150_SCOPE", 1000)
OOS_SHARE_DOMAIN = 0.10
OOS_SHARE_SCOPE = 0.40

DOMAIN_TEXT = "Which domain of this virtual assistant does `message` belong to?"
DOMAINS: dict[str, str] = {
    "banking": "Bank accounts: balances, transfers, bills, transactions, routing numbers, frozen accounts, fraud",
    "credit_cards": "Credit cards: limits, rewards, APR, new, lost, damaged or declined cards, credit score",
    "kitchen_and_dining": "Cooking and restaurants: recipes, ingredients, nutrition, cooking times, restaurant "
    "suggestions, reviews and reservations",
    "home": "Household organising: playing music and playlists, shopping and to-do lists, reminders, calendar, "
    "online orders, smart-home devices",
    "auto_and_commute": "Car and getting around: maintenance, oil, tires, gas and mileage, traffic, directions, "
    "distance, rides",
    "travel": "Trips: flights, hotels, car rental, visas, vaccines, luggage, plug types, exchange rates, "
    "translation, time zones, travel alerts",
    "utility": "Everyday tools: weather, time and date, alarms, timers, calls and texts, calculator, definitions, "
    "spelling, unit conversion, coin flips and dice, finding the phone",
    "work": "The user's job: paid time off, payday, income, taxes and W-2, 401k, insurance benefits, meetings, "
    "holidays",
    "small_talk": "Chatting with the assistant itself: greetings, thanks, goodbyes, jokes, fun facts, questions "
    "about who the assistant is",
    "meta": "Controlling the conversation or the assistant: yes/no/maybe replies, repeat, cancel, volume, speed, "
    "language, accent, whisper mode, names, settings, syncing a device",
    "out_of_scope": "None of these: a request outside every area above",
}

SCOPE_TEXT = "Is `message` a request this virtual assistant supports?"
SCOPE = {
    "true": "It falls within one of the assistant's supported areas: banking; credit cards; cooking and "
    "restaurants; music, lists, reminders, calendar, orders and smart-home devices; car maintenance and "
    "commuting; travel; everyday tools (weather, time, alarms, timers, calls, texts, calculator, definitions, "
    "unit conversion); the user's job (time off, pay, taxes, benefits, meetings); small talk with the "
    "assistant; or controlling the assistant (repeat, cancel, volume, language, settings, yes/no replies)",
    "false": "It asks for something outside all of those areas",
}


def _get(url: str) -> bytes:
    r = httpx.get(url, follow_redirects=True, timeout=120)
    r.raise_for_status()
    return r.content


def fetch(raw_dir: Path) -> None:
    for fname, url in (("test.parquet", PARQUET), ("info.json", INFO), ("domains.json", DOMAINS_URL)):
        out = raw_dir / fname
        if not out.exists():
            out.write_bytes(_get(url))


def _round_robin(pools: dict[str, list], n: int) -> list:
    """Take items one label at a time (labels sorted) until n; each pool already in hash order."""
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
    names = json.loads((raw_dir / "info.json").read_text())["dataset_info"]["features"]["intent"]["names"]
    domains = json.loads((raw_dir / "domains.json").read_text())
    intent_domain = {i: d for d, intents in domains.items() for i in intents}
    intent_domain["oos"] = "out_of_scope"
    assert set(intent_domain.values()) == set(DOMAINS), set(intent_domain.values()) ^ set(DOMAINS)

    df = pl.read_parquet(raw_dir / "test.parquet").with_row_index("row")
    seen: set[str] = set()
    items = []  # (row, text, intent, domain)
    for row, text, intent in df.select("row", "text", "intent").iter_rows():
        t = " ".join(text.split())
        if not t or t.lower() in seen:
            continue
        seen.add(t.lower())
        name = names[intent]
        items.append((row, t, name, intent_domain[name]))

    oos = hash_order([x for x in items if x[3] == "out_of_scope"], lambda x: x[0], "clinc150.oos")
    ins = [x for x in items if x[3] != "out_of_scope"]

    # Domain template: out-of-scope first slice; in-scope round-robin over domains, each domain's pool
    # round-robin over its intents so every intent is represented.
    def domain_pools(pool, salt):
        by_dom: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for x in hash_order(pool, lambda x: x[0], salt):
            by_dom[x[3]][x[2]].append(x)
        return {d: _round_robin(dict(by_int), 10**9) for d, by_int in by_dom.items()}

    n_oos_a = round(TARGET_DOMAIN * OOS_SHARE_DOMAIN)
    oos_a = oos[:n_oos_a]
    ins_a = _round_robin(domain_pools(ins, "clinc150.domain"), TARGET_DOMAIN - n_oos_a)
    used = {x[0] for x in ins_a} | {x[0] for x in oos_a}

    n_oos_b = round(TARGET_SCOPE * OOS_SHARE_SCOPE)
    oos_b = oos[n_oos_a : n_oos_a + n_oos_b]
    ins_b = _round_robin(
        domain_pools([x for x in ins if x[0] not in used], "clinc150.in_scope"), TARGET_SCOPE - len(oos_b)
    )

    for row, text, intent, dom in sorted(ins_a + oos_a):
        yield Question(
            text=DOMAIN_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=DOMAINS,
            state={"message": text[:1500]},
            shape="route",
            node_hint="machine.support.routing",
            template_id="clinc150.domain",
            source_item_id=f"plus/test:{row}",
            license=LICENSE,
            truth=dom,
            meta={"split": "test", "intent": intent},
        )
    for row, text, intent, dom in sorted(ins_b + oos_b):
        yield Question(
            text=SCOPE_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SCOPE,
            state={"message": text[:1500]},
            shape="route",
            node_hint="machine.support.routing",
            template_id="clinc150.in_scope",
            source_item_id=f"plus/test:{row}",
            license=LICENSE,
            truth=dom != "out_of_scope",
            meta={"split": "test", "intent": intent, "domain": dom},
        )
