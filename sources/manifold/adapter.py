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
from askjev.sampling import env_int, top_up

NAME = "manifold"
API = "https://api.manifold.markets/v0"
LICENSE = "Manifold public API (read access allowed; market text by Manifold users)"
TARGET_V1 = 100  # the original seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_MANIFOLD", TARGET_V1)  # Phase 6: 600
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
# Phase 6: a second pool (markets_v2.json) adds the next 1,000 markets of each capped topic above and these
# topics; a market already in the v1 pool keeps its v1 node, otherwise the first matching topic sets it.
EXTRA_TOPICS = {
    "spacex": "world.future.space",
    "energy": "world.future.climate_environment",
    "weather": "world.future.climate_environment",
    "physics": "world.future.technology",
    "medicine": "world.future.technology",
    "longevity": "world.future.technology",
    "internet": "world.future.technology",
    "apple": "world.future.technology",
    "tesla": "world.future.technology",
    "youtube": "world.future.technology",
    "health": "world.future.society",
    "culture-default": "world.future.sports_entertainment",  # Manifold "Culture" is mostly pop culture
    "stocks": "world.future.economy",
    "finance": "world.future.economy",
    "crypto-speculation": "world.future.economy",
    "bitcoin": "world.future.economy",
    "chess": "world.future.sports_entertainment",
    "formula-1": "world.future.sports_entertainment",
    "soccer": "world.future.sports_entertainment",
    "nfl": "world.future.sports_entertainment",
    "football": "world.future.sports_entertainment",
    "nba": "world.future.sports_entertainment",
    "music-f213cbf1eab5": "world.future.sports_entertainment",
    "books": "world.future.sports_entertainment",
}
QUOTA_V2 = {  # shares of TARGET for the Phase 6 top-up (v1 picks count toward their node)
    "world.future.ai": 0.18,
    "world.future.technology": 0.20,
    "world.future.space": 0.12,
    "world.future.climate_environment": 0.10,
    "world.future.economy": 0.14,
    "world.future.sports_entertainment": 0.20,
    "world.future.society": 0.06,
}
PAGE = 1000
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
# Phase 6 top-up only (adding these to the v1 filters would change the v1 sample): contested social policy,
# criminal cases, religion, and profanity.
DROP_V2 = re.compile(
    r"\b(lgbt\w*|homosexual\w*|transgender|drag show|polygamy|assange|extradit\w*|illegal|legaliz\w*|ban|bans|"
    r"banned|antitrust|arrest\w*|charged|plead\w*|guilty|crimes?|criminal|robber\w*|jesus|christ)\b|fuck|shit",
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


def _eligible_by_node(markets: list[dict]) -> dict[str, list[dict]]:
    by_node: dict[str, list[dict]] = {}
    seen = set()
    for m in markets:
        key = re.sub(r"\W+", " ", m.get("question", "").lower()).strip()
        if m["id"] in seen or key in seen or not _eligible(m):
            continue
        seen |= {m["id"], key}
        by_node.setdefault(m["_node"], []).append(m)
    return by_node


def _clean(m: dict) -> bool:
    return not re.search(r"\d", m["question"])


def _years_only(m: dict) -> bool:
    return bool(re.search(r"\d", m["question"])) and bool(YEAR_ONLY.match(m["question"]))


def select_v1(markets: list[dict]) -> list[dict]:
    """Seeded per-node quotas; within a node prefer questions with no digits, then ones whose only digits are years."""
    by_node = _eligible_by_node(markets)
    rng = random.Random(SEED)
    ranked = {}
    for node in QUOTA:
        ms = sorted(by_node.get(node, []), key=lambda m: m["id"])
        clean = [m for m in ms if _clean(m)]
        years = [m for m in ms if _years_only(m)]
        ranked[node] = rng.sample(clean, len(clean)) + rng.sample(years, len(years))
    picked = []
    for node, k in QUOTA.items():
        picked += ranked[node][:k]
        ranked[node] = ranked[node][k:]
    for node in QUOTA:  # fill shortfalls round-robin in QUOTA order
        while len(picked) < TARGET_V1 and ranked[node]:
            picked.append(ranked[node].pop(0))
    return sorted(picked[:TARGET_V1], key=lambda m: m["id"])


def select(raw_dir: Path) -> list[dict]:
    """The v1 sample, then (Phase 6) a prefix-stable top-up per node from the v1 + v2 pools: each node is filled to
    its QUOTA_V2 share, digit-free questions first, then year-only ones; shortfalls are filled from the other nodes."""
    v1 = json.loads((raw_dir / "markets.json").read_text())
    picked = select_v1(v1)
    if TARGET <= TARGET_V1:
        return picked[:TARGET]
    v1_ids = {m["id"] for m in v1}
    nodes = {**TOPICS, **EXTRA_TOPICS}
    v2 = [{**m, "_node": nodes[m["_topic"]]} for m in json.loads((raw_dir / "markets_v2.json").read_text())]
    pool = v1 + [m for m in v2 if m["id"] not in v1_ids]
    have_keys = {re.sub(r"\W+", " ", m["question"].lower()).strip() for m in picked}
    by_node = {
        node: [m for m in ms if re.sub(r"\W+", " ", m["question"].lower()).strip() not in have_keys
               and not DROP_V2.search(m["question"])]
        for node, ms in _eligible_by_node(pool).items()
    }
    key = lambda m: m["id"]  # noqa: E731
    rest: dict[str, list[dict]] = {}
    for node, share in QUOTA_V2.items():
        ms = by_node.get(node, [])
        want = round(share * TARGET) - sum(m["_node"] == node for m in picked)
        clean = top_up(picked, [m for m in ms if _clean(m)], len(ms), key, f"manifold.{node}")
        years = top_up(picked, [m for m in ms if _years_only(m)], len(ms), key, f"manifold.{node}.years")
        ranked = clean + years
        picked += ranked[: max(want, 0)]
        rest[node] = ranked[max(want, 0) :]
    while len(picked) < TARGET and any(rest.values()):  # fill shortfalls one market per node in turn
        for node in QUOTA_V2:
            if len(picked) < TARGET and rest[node]:
                picked.append(rest[node].pop(0))
    return sorted(picked[:TARGET], key=lambda m: m["id"])


def _window(m: dict) -> tuple[int, int]:
    end = min(t for t in (m.get("closeTime"), m.get("resolutionTime")) if t)
    return m["createdTime"], end


def _search(c: httpx.Client, topic: str, offset: int = 0) -> list[dict]:
    r = c.get(
        f"{API}/search-markets",
        params={"term": "", "filter": "resolved", "contractType": "BINARY", "sort": "most-popular",
                "limit": PAGE, "offset": offset, "topicSlug": topic},
    )
    r.raise_for_status()
    time.sleep(DELAY)
    return r.json()


def fetch(raw_dir: Path) -> None:
    pool_path = raw_dir / "markets.json"
    if not pool_path.exists():
        markets = []
        with httpx.Client(timeout=60) as c:
            for topic, node in TOPICS.items():
                for m in _search(c, topic):
                    markets.append({**m, "_topic": topic, "_node": node})
        pool_path.write_text(json.dumps(markets))
    v2_path = raw_dir / "markets_v2.json"
    if TARGET > TARGET_V1 and not v2_path.exists():
        v1_topics = json.loads(pool_path.read_text())
        counts = {t: sum(m["_topic"] == t for m in v1_topics) for t in TOPICS}
        markets = []
        with httpx.Client(timeout=60) as c:
            for topic, node in TOPICS.items():
                if counts[topic] >= PAGE:  # capped in v1: take the next page
                    markets += [{**m, "_topic": topic, "_node": node} for m in _search(c, topic, offset=PAGE)]
            for topic, node in EXTRA_TOPICS.items():
                markets += [{**m, "_topic": topic, "_node": node} for m in _search(c, topic)]
        v2_path.write_text(json.dumps(markets))

    # Market probability at the midpoint of each picked market's life (last bet before that time).
    bets_dir = raw_dir / "bets"
    bets_dir.mkdir(exist_ok=True)
    with httpx.Client(timeout=60) as c:
        for m in select(raw_dir):
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
    for m in select(raw_dir):
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
