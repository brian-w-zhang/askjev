"""NBA GOAT pairs (top 25 players by Wikidata sitelinks) + categorical team-membership facts."""

from __future__ import annotations

import itertools
import json
import random
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "nba"
SPARQL = "https://query.wikidata.org/sparql"
UA = "askjev/0.1 (github.com/brian-w-zhang/askjev)"
LICENSE = "CC0"
TOP = 25
FACTS_PER_PLAYER = (2, 2)  # (true, false)
SEED = 20260924

API = "https://www.wikidata.org/w/api.php"
QLEVER = "https://qlever.dev/api/wikidata"
PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
"""
NBA = "Q155223"

# Kept light: the label service / multi-OPTIONAL variants time out on WDQS, so labels and P54
# come from the entity API instead.
QUERIES = {
    "players": """SELECT ?item ?sitelinks WHERE {
  ?item wdt:P106 wd:Q3665646 ; wdt:P118 wd:Q155223 ; wikibase:sitelinks ?sitelinks .
} ORDER BY DESC(?sitelinks) LIMIT 60""",
    "teams": """SELECT ?team ?end WHERE {
  ?team wdt:P31 wd:Q13393265 ; wdt:P118 wd:Q155223 .
  OPTIONAL { ?team wdt:P576 ?end }
}""",
}

RECENT = 2025
AS_OF = "2026-09-24"
# Year each franchise took its current name/city.
NAMED_SINCE = {
    "Oklahoma City Thunder": 2008, "Brooklyn Nets": 2012, "New Orleans Pelicans": 2013, "Charlotte Hornets": 2014,
    "Memphis Grizzlies": 2001, "Sacramento Kings": 1985, "Los Angeles Clippers": 1984, "Washington Wizards": 1997,
    "Utah Jazz": 1979, "Los Angeles Lakers": 1960, "Golden State Warriors": 1971, "Houston Rockets": 1971,
    "Atlanta Hawks": 1968, "Detroit Pistons": 1957, "San Antonio Spurs": 1973,
}

# Relocated/renamed franchises: current team -> earlier identities (never used as a false answer
# for a player who played for any of these).
FRANCHISE = {
    "Oklahoma City Thunder": ["SuperSonics"],
    "Brooklyn Nets": ["New Jersey Nets", "New York Nets"],
    "New Orleans Pelicans": ["Hornets"],
    "Charlotte Hornets": ["Bobcats", "Hornets", "Pelicans"],
    "Memphis Grizzlies": ["Vancouver Grizzlies"],
    "Sacramento Kings": ["Royals", "Kansas City Kings"],
    "Los Angeles Clippers": ["Braves", "San Diego Clippers"],
    "Washington Wizards": ["Bullets", "Zephyrs", "Chicago Packers"],
    "Utah Jazz": ["New Orleans Jazz"],
    "Los Angeles Lakers": ["Minneapolis Lakers"],
    "Golden State Warriors": ["Philadelphia Warriors", "San Francisco Warriors"],
    "Houston Rockets": ["San Diego Rockets"],
    "Atlanta Hawks": ["St. Louis Hawks", "Milwaukee Hawks", "Tri-Cities Blackhawks"],
    "Detroit Pistons": ["Fort Wayne Pistons"],
    "San Antonio Spurs": ["Chaparrals"],
}


def _sparql(query: str) -> list[dict]:
    """WDQS first; on timeout/5xx/429 fall back to the public QLever Wikidata mirror (same data model)."""
    query = PREFIXES + query
    for endpoint, timeout in ((SPARQL, 45), (QLEVER, 90), (SPARQL, 60), (QLEVER, 90)):
        try:
            r = httpx.get(endpoint, params={"query": query}, timeout=timeout, follow_redirects=True,
                          headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
        except httpx.TimeoutException:
            continue
        if r.status_code != 200:
            time.sleep(5)
            continue
        return [{k: v["value"].rsplit("/", 1)[-1] if v.get("type") == "uri" else v["value"] for k, v in b.items()}
                for b in r.json()["results"]["bindings"]]
    raise RuntimeError("wikidata sparql failed on WDQS and QLever")


def _entities(ids: list[str], props: str) -> dict:
    out = {}
    for i in range(0, len(ids), 50):
        for attempt in range(5):
            try:
                r = httpx.get(API, params={"action": "wbgetentities", "ids": "|".join(ids[i : i + 50]), "props": props,
                                           "languages": "en|mul", "format": "json"}, headers={"User-Agent": UA}, timeout=60)
                r.raise_for_status()
                out.update(r.json()["entities"])
                break
            except (httpx.TimeoutException, httpx.HTTPStatusError):
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError("wikidata entity API failed")
        time.sleep(1)
    return out


def _label(ent: dict) -> str | None:
    labels = ent.get("labels", {})
    return (labels.get("en") or labels.get("mul") or {}).get("value")


def _year(q: dict, prop: str) -> int | None:
    for v in q.get(prop, []):
        t = (v.get("datavalue") or {}).get("value", {})
        if isinstance(t, dict) and t.get("time"):
            return int(t["time"][1:5])
    return None


def _tenures(ent: dict) -> list[dict]:
    """P54 memberships with start/end years (P580/P582 qualifiers), deprecated statements dropped."""
    out = []
    for c in ent.get("claims", {}).get("P54", []):
        if c.get("rank") == "deprecated" or not c["mainsnak"].get("datavalue"):
            continue
        q = c.get("qualifiers", {})
        out.append({"team": c["mainsnak"]["datavalue"]["value"]["id"], "start": _year(q, "P580"), "end": _year(q, "P582")})
    return out


def _claim_ids(ent: dict, prop: str) -> list[str]:
    return [c["mainsnak"]["datavalue"]["value"]["id"] for c in ent.get("claims", {}).get(prop, [])
            if c["mainsnak"].get("datavalue")]


def fetch(raw_dir: Path) -> None:
    for name, q in QUERIES.items():
        out = raw_dir / f"{name}.json"
        if not out.exists():
            out.write_text(json.dumps(_sparql(q), ensure_ascii=False, indent=1))
            time.sleep(2)
    out = raw_dir / "entities.json"
    if out.exists():
        return
    rows = json.loads((raw_dir / "players.json").read_text())
    players = _entities(list(dict.fromkeys(r["item"] for r in rows)), "labels|claims")
    team_ids = {t["team"] for e in players.values() for t in _tenures(e)}
    team_ids |= {r["team"] for r in json.loads((raw_dir / "teams.json").read_text())}
    teams = _entities(sorted(team_ids), "labels|claims")
    slim = {
        "players": {q: {"label": _label(e), "P54": _tenures(e)} for q, e in players.items()},
        "teams": {q: {"label": _label(e), "P118": _claim_ids(e, "P118"), "ended": bool(e.get("claims", {}).get("P576"))}
                  for q, e in teams.items()},
    }
    out.write_text(json.dumps(slim, ensure_ascii=False, indent=1))


def _players(raw_dir: Path) -> list[dict]:
    ents = json.loads((raw_dir / "entities.json").read_text())["players"]
    seen, out = set(), []
    for r in json.loads((raw_dir / "players.json").read_text()):
        label = (ents.get(r["item"]) or {}).get("label")
        if r["item"] in seen or not label:
            continue
        seen.add(r["item"])
        out.append({"qid": r["item"], "name": label, "sitelinks": int(r["sitelinks"])})
    return out[:TOP]


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _pairs(players: list[dict]) -> Iterator[Question]:
    for a, b in itertools.combinations(sorted(players, key=lambda p: p["name"]), 2):
        yield Question(
            text="Who is the greater basketball player?",
            primitive="choice",
            hemisphere="world",
            kind="taste",
            origin="dataset",
            source=NAME,
            options={_slug(a["name"]): a["name"], _slug(b["name"]): b["name"]},
            node_hint="world.sports.basketball.nba",
            source_item_id=f"{a['qid']}-{b['qid']}",
            license=LICENSE,
            meta={"qid_a": a["qid"], "qid_b": b["qid"], "sitelinks_a": a["sitelinks"], "sitelinks_b": b["sitelinks"], "pair": True},
        )


def _related(team: str, played: set[str]) -> bool:
    """True if `team` is (or descends from) a franchise the player played for."""
    names = [team, *FRANCHISE.get(team, [])]
    nick = team.split()[-1]
    return any(n.lower() in p.lower() or p.lower() in n.lower() for n in names for p in played) or any(
        p.split()[-1] == nick for p in played
    )


def _facts(raw_dir: Path, players: list[dict]) -> Iterator[Question]:
    ents = json.loads((raw_dir / "entities.json").read_text())
    teams = ents["teams"]
    current_ids = {r["team"] for r in json.loads((raw_dir / "teams.json").read_text()) if not r.get("end")}
    current = sorted({teams[t]["label"] for t in current_ids
                      if t in teams and teams[t]["label"] and not re.search(r"\d", teams[t]["label"])})
    played: dict[str, set[str]] = {}  # every NBA team label (used to exclude false answers)
    safe_true: dict[str, set[str]] = {}  # teams usable as a true answer
    for pq, p in ents["players"].items():
        for t in p["P54"]:
            info = teams.get(t["team"]) or {}
            label = info.get("label")
            if NBA not in info.get("P118", []) or not label:
                continue
            played.setdefault(pq, set()).add(label)
            # Skip moves too recent to be settled knowledge, and franchise-level links where the
            # player's whole stint predates the current name (Chamberlain -> "Golden State Warriors").
            if (t["start"] or 0) >= RECENT or (t["end"] and t["end"] <= NAMED_SINCE.get(label, 0)):
                continue
            safe_true.setdefault(pq, set()).add(label)
    n_true, n_false = FACTS_PER_PLAYER
    for p in players:
        rng = random.Random(f"{SEED}:{p['qid']}")
        teams = played.get(p["qid"], set())
        trues = sorted(t for t in safe_true.get(p["qid"], set()) if not re.search(r"\d", t))
        falses = [t for t in current if t not in teams and not _related(t, teams)]
        picks = [(t, True) for t in rng.sample(trues, min(n_true, len(trues)))]
        picks += [(t, False) for t in rng.sample(falses, min(n_false + (n_true - len(picks)), len(falses)))]
        for team, truth in sorted(picks):
            yield Question(
                text=f"Did {p['name']} play for the {team}?",
                primitive="noul",
                hemisphere="world",
                kind="factual",
                origin="wikidata-fact",
                source=NAME,
                truth=truth,
                node_hint="world.sports.basketball.nba",
                source_item_id=f"{p['qid']}:P54:{team}",
                license=LICENSE,
                meta={"qid": p["qid"], "property": "P54", "team": team, "as_of": AS_OF},
            )


def normalize(raw_dir: Path) -> Iterator[Question]:
    players = _players(raw_dir)
    yield from _pairs(players)
    yield from _facts(raw_dir, players)
