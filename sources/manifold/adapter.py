"""Resolved non-political Manifold binary markets: the market question as a Noul forecast, truth = resolution."""

from __future__ import annotations

import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "manifold"
API = "https://api.manifold.markets/v0"
LICENSE = "Manifold public API (read access allowed; market text by Manifold users)"
TARGET = 100
SEED = "manifold-20260924"
MIN_BETTORS = 50
# Resolved binary markets, 1,000 most popular per non-political topic. Order matters: a market listed
# under several topics takes the node of the first one.
TOPICS = {
    "ai": "world.future.ai",
    "space": "world.future.space",
    "climate": "world.future.climate_environment",
    "economics-default": "world.future.economy",
    "technology-default": "world.future.technology",
    "science-default": "world.future.technology",
    "sports-default": "world.future.sports_entertainment",
    "entertainment": "world.future.sports_entertainment",
    "movies": "world.future.sports_entertainment",
    "gaming": "world.future.sports_entertainment",
}
QUOTA = {  # per node, sums to TARGET; shortfalls are filled from the other nodes
    "world.future.ai": 20,
    "world.future.technology": 20,
    "world.future.space": 12,
    "world.future.climate_environment": 12,
    "world.future.economy": 12,
    "world.future.sports_entertainment": 24,
}
DELAY = 0.25  # <= 4 requests/s

POLITICAL = re.compile(
    r"\b(trump\w*|biden|harris|kamala|obama|clinton|desantis|haley|ramaswamy|rfk|kennedy|vance|walz|pelosi|"
    r"sanders|newsom|musk'?s? doge|doge|election\w*|elect\w*|vote\w*|voting|ballot|primar(y|ies)|caucus\w*|"
    r"nominee|nominat\w*|president\w*|presidential|senat\w*|congress\w*|house of representatives|speaker|"
    r"republican\w*|democrat\w*|gop|dnc|rnc|parliament\w*|prime minister|pm|minister|chancellor|governor|mayor|"
    r"government|shutdown|supreme court|scotus|impeach\w*|indict\w*|convict\w*|trial|pardon\w*|tariff\w*|"
    r"sanction\w*|legislat\w*|bill|law|policy|politic\w*|putin|zelensk\w*|ukrain\w*|russia\w*|kremlin|israel\w*|"
    r"hamas|gaza|hezbollah|iran\w*|netanyahu|palestin\w*|intifada|china|chinese|xi|taiwan\w*|north korea\w*|"
    r"kim jong|syria\w*|yemen|houthi\w*|venezuela\w*|maduro|nato|war|wars|warfare|military|army|troops|invade\w*|"
    r"invasion|missile\w*|nuclear|ceasefire|hostage\w*|coup|terror\w*|attack\w*|strike|strikes|bomb\w*|"
    r"assassinat\w*|shoot\w*|killed|deport\w*|immigra\w*|border|abortion|roe|gun|guns|protest\w*|riot\w*|"
    r"court|debat\w*|far.?right|far.?left|right-wing|left-wing|woke|brexit|eu|un|geopolit\w*|diplomatic|treaty|annex\w*|referendum|milei|modi|macron|starmer|sunak|trudeau|"
    r"erdogan|orban|lula|bolsonaro|poll|polls|polling|538|fed|federal|fbi|cia|doj|epstein)\b",
    re.I,
)
# Markets about Manifold itself, personal/self-referential markets, and unclear ones.
META = re.compile(
    r"(\(personal\)|@|\bmanifold\b|\bmana\b|\bthis (question|market)\b|\bi\b|\bi'll\b|\bi'm\b|\bmy\b|\bme\b|"
    r"\bwe\b|\bour\b|\bresolve\w*\b|\bmarkets? (say|will)\b|\[.*\]|\bvs\.?\b|\bor\b)",
    re.I,
)
DROP = re.compile(  # deaths, streamer drama, sexual content, and questions that need unseen context
    r"\b(die|dies|died|dead|death\w*|alive|surviv\w*|kill\w*|live until|centenarian|assassin\w*|suicide|"
    r"destiny|mr\.? ?girl|keffals|drama|stream\w*|podcast|porn\w*|sex\w*|nsfw|onlyfans|"
    r"this (tweet|video|post|paper|claim|story|thread|image|picture|photo|clip|result)|these|below|above|"
    r"described|description|linked|rumou?r\w*|leak\w*|crazy|something|which|claude|violen\w*|collapse\w*|straight people|gay\w*|"
    r"this (?!year|season|week|month|summer|winter|fall|spring|weekend)\w+)\b",
    re.I,
)
NUMBERY = re.compile(r"[$%<>]|\b\d+(\.\d+)?\s*(k|m|b|million|billion|trillion|percent|points?|views|followers)\b", re.I)
YEAR_ONLY = re.compile(r"^\D*((19|20)\d\d\D*)*$")  # digits only as 4-digit years

def _eligible(m: dict) -> bool:
    q = m.get("question", "").strip()
    return (
        m.get("outcomeType") == "BINARY"
        and m.get("isResolved")
        and m.get("resolution") in ("YES", "NO")
        and (m.get("uniqueBettorCount") or 0) >= MIN_BETTORS
        and q.endswith("?")
        and not re.match(r"(which|what|who|how|when|where|why)\b", q, re.I)
        and 20 <= len(q) <= 160
        and not POLITICAL.search(q)
        and not META.search(q)
        and not DROP.search(q)
        and not NUMBERY.search(q)
        and m.get("createdTime")
        and (m.get("closeTime") or m.get("resolutionTime"))
    )


def select(markets: list[dict]) -> list[dict]:
    """Seeded per-node quotas; within a node prefer questions with no digits, then ones whose only digits are years."""
    by_node: dict[str, list[dict]] = {}
    seen = set()
    for m in markets:
        key = re.sub(r"\W+", " ", m.get("question", "").lower()).strip()
        if m["id"] in seen or key in seen or not _eligible(m):
            continue
        seen |= {m["id"], key}
        by_node.setdefault(m["_node"], []).append(m)
    rng = random.Random(SEED)
    ranked = {}
    for node in QUOTA:
        ms = sorted(by_node.get(node, []), key=lambda m: m["id"])
        clean = [m for m in ms if not re.search(r"\d", m["question"])]
        years = [m for m in ms if re.search(r"\d", m["question"]) and YEAR_ONLY.match(m["question"])]
        ranked[node] = rng.sample(clean, len(clean)) + rng.sample(years, len(years))
    picked = []
    for node, k in QUOTA.items():
        picked += ranked[node][:k]
        ranked[node] = ranked[node][k:]
    for node in QUOTA:  # fill shortfalls round-robin in QUOTA order
        while len(picked) < TARGET and ranked[node]:
            picked.append(ranked[node].pop(0))
    return sorted(picked[:TARGET], key=lambda m: m["id"])


def _window(m: dict) -> tuple[int, int]:
    end = min(t for t in (m.get("closeTime"), m.get("resolutionTime")) if t)
    return m["createdTime"], end


def fetch(raw_dir: Path) -> None:
    pool_path = raw_dir / "markets.json"
    if not pool_path.exists():
        markets = []
        with httpx.Client(timeout=60) as c:
            for topic, node in TOPICS.items():
                r = c.get(
                    f"{API}/search-markets",
                    params={"term": "", "filter": "resolved", "contractType": "BINARY", "sort": "most-popular",
                            "limit": 1000, "topicSlug": topic},
                )
                r.raise_for_status()
                for m in r.json():
                    markets.append({**m, "_topic": topic, "_node": node})
                time.sleep(DELAY)
        pool_path.write_text(json.dumps(markets))
    markets = json.loads(pool_path.read_text())

    # Market probability at the midpoint of each picked market's life (last bet before that time).
    bets_dir = raw_dir / "bets"
    bets_dir.mkdir(exist_ok=True)
    with httpx.Client(timeout=60) as c:
        for m in select(markets):
            out = bets_dir / f"{m['id']}.json"
            if out.exists():
                continue
            start, end = _window(m)
            r = c.get(f"{API}/bets", params={"contractId": m["id"], "beforeTime": (start + end) // 2, "limit": 5})
            r.raise_for_status()
            out.write_text(r.text)
            time.sleep(DELAY)


def _iso(ms: int | None) -> str | None:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if ms else None


def normalize(raw_dir: Path) -> Iterator[Question]:
    markets = json.loads((raw_dir / "markets.json").read_text())
    for m in select(markets):
        q = re.sub(r"\s+", " ", m["question"]).strip()
        n = m.get("uniqueBettorCount")
        p_final = m.get("resolutionProbability")
        if p_final is None:
            p_final = m.get("probability")
        human = []
        # The at-close price is nearly the outcome (Brier ~0.03), so it is kept only as metadata;
        # the midlife price is the real forecast signal and is the human distribution.
        bets = json.loads((raw_dir / "bets" / f"{m['id']}.json").read_text())
        p_mid = next((b["probAfter"] for b in bets if b.get("probAfter") is not None), None)
        if p_mid is not None:
            human.append(HumanDist(population="Manifold market (midlife)", distribution={"true": p_mid, "false": 1 - p_mid},
                                   n=n, source="Manifold API bets: last probAfter before the market's midpoint",
                                   wave="midlife"))
        yield Question(
            text=q,
            primitive="noul",
            hemisphere="world",
            kind="forecast",
            origin="dataset",
            source=NAME,
            node_hint=m["_node"],
            source_item_id=m["id"],
            license=LICENSE,
            truth=m["resolution"] == "YES",
            human=human,
            meta={
                "url": m.get("url"),
                "closeTime": m.get("closeTime"),
                "created": _iso(m.get("createdTime")),
                "closed": _iso(_window(m)[1]),
                "resolution": m["resolution"],
                "topic": m["_topic"],
                "volume": m.get("volume"),
                "p_at_close": p_final,
            },
        )
