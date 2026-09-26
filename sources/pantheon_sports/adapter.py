"""Pantheon (pantheon.world) athletes: which of two athletes from the same sport is better known around the world
today, truth from Wikipedia reach (language editions and non-English pageviews) in Pantheon's 2025 update."""

from __future__ import annotations

import bz2
import io
import itertools
import re
import unicodedata
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pantheon_sports"
URL = "https://storage.googleapis.com/pantheon-public-data/person_2025_update.csv.bz2"
FILE = "person_2025_update.csv.bz2"
LICENSE = "CC BY-SA 4.0 (Pantheon, pantheon.world; Yu, Macé, Hidalgo et al. 2016, Scientific Data)"
SALT = "pantheon_sports.v1"
TARGET = env_int("TARGET_PANTHEON_SPORTS", 3000)
TOP_PER_SPORT = 250  # most-linked athletes per sport
MAX_PAIRS_PER_PERSON = 6
MIN_LANG_RATIO = 1.3
MIN_VIEW_RATIO = 2.0

# Pantheon occupation -> (noun in the question, node, share of TARGET)
SPORTS = {
    "SOCCER PLAYER": ("soccer player", "world.sports.soccer.clubs_players", 0.20),
    "BASKETBALL PLAYER": ("basketball player", "world.sports.basketball", 0.09),
    "TENNIS PLAYER": ("tennis player", "world.sports.individual_sports", 0.08),
    "ATHLETE": ("track and field athlete", "world.sports.individual_sports.sport_of_athletics", 0.07),
    "RACING DRIVER": ("racing driver", "world.sports.motorsport", 0.07),
    "SWIMMER": ("swimmer", "world.sports.individual_sports.swimming", 0.05),
    "BOXER": ("boxer", "world.sports.combat_sports", 0.06),
    "WRESTLER": ("wrestler", "world.sports.combat_sports", 0.04),
    "MARTIAL ARTS": ("martial artist", "world.sports.combat_sports.martial_arts", 0.03),
    "CYCLIST": ("cyclist", "world.sports.individual_sports", 0.04),
    "HOCKEY PLAYER": ("ice hockey player", "world.sports.other_team_sports", 0.04),
    "CHESS PLAYER": ("chess player", "world.sports.board_card_games", 0.04),
    "GYMNAST": ("gymnast", "world.sports.individual_sports", 0.03),
    "SKIER": ("skier", "world.sports.individual_sports", 0.02),
    "SKATER": ("figure or speed skater", "world.sports.individual_sports", 0.02),
    "GOLFER": ("golfer", "world.sports.individual_sports", 0.02),
    "CRICKETER": ("cricketer", "world.sports.other_team_sports", 0.02),
    "BASEBALL PLAYER": ("baseball player", "world.sports.baseball", 0.02),
    "AMERICAN FOOTBALL PLAYER": ("American football player", "world.sports.american_football", 0.02),
    "RUGBY PLAYER": ("rugby player", "world.sports.other_team_sports", 0.01),
    "SNOOKER": ("snooker player", "world.sports.individual_sports", 0.01),
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    r = httpx.get(URL, timeout=300, follow_redirects=True)
    r.raise_for_status()
    out.write_bytes(r.content)


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _latin(name: str) -> bool:
    return all(ord(c) < 0x250 or c in "’‘" for c in name)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_csv(io.BytesIO(bz2.open(raw_dir / FILE).read()), infer_schema_length=200000)
    df = df.filter(
        (pl.col("is_group") == False) & pl.col("occupation").is_in(list(SPORTS))  # noqa: E712
        & (pl.col("birthyear") >= 1930) & pl.col("l").is_not_null() & pl.col("non_en_page_views").is_not_null()
    )
    dup = set(df.group_by("name").len().filter(pl.col("len") > 1)["name"])
    for occ, (noun, node, share) in SPORTS.items():
        pool = []
        for p in df.filter(pl.col("occupation") == occ).sort("l", "wd_id", descending=[True, False]).iter_rows(named=True):
            n = p["name"]
            if n in dup or not _latin(n) or "(" in n or re.search(r"\d", n) or not _slug(n):
                continue
            pool.append(p)
            if len(pool) >= TOP_PER_SPORT:
                break
        k = round(TARGET * share)
        uses: dict[str, int] = {}
        taken = 0
        pairs = list(itertools.combinations(pool, 2))
        for a, b in hash_order(pairs, lambda x: f"{x[0]['wd_id']}|{x[1]['wd_id']}", f"{SALT}.{occ}"):
            if taken >= k:
                break
            if uses.get(a["wd_id"], 0) >= MAX_PAIRS_PER_PERSON or uses.get(b["wd_id"], 0) >= MAX_PAIRS_PER_PERSON:
                continue
            hi, lo = (a, b) if a["non_en_page_views"] > b["non_en_page_views"] else (b, a)
            # Better known on both measures by a clear margin.
            if hi["non_en_page_views"] < MIN_VIEW_RATIO * lo["non_en_page_views"] or hi["l"] < MIN_LANG_RATIO * lo["l"]:
                continue
            ka, kb = _slug(a["name"]), _slug(b["name"])
            if ka == kb:
                continue
            uses[a["wd_id"]] = uses.get(a["wd_id"], 0) + 1
            uses[b["wd_id"]] = uses.get(b["wd_id"], 0) + 1
            taken += 1
            first, second = hash_order([a, b], lambda x: x["wd_id"], f"{SALT}.order")
            yield Question(
                text=f"Which {noun} is better known around the world today: {first['name']} or {second['name']}?",
                primitive="choice", hemisphere="world", kind="evaluative", origin="template", source=NAME,
                options={_slug(x["name"]): f"{x['name']} ({noun}, born {x['birthyear']}"
                         f"{', ' + x['bplace_country'] if x['bplace_country'] else ''})" for x in (first, second)},
                node_hint=node, source_item_id=f"{a['wd_id']}-{b['wd_id']}", license=LICENSE,
                truth=_slug(hi["name"]), template_id=f"pantheon_sports.{_slug(noun)}",
                meta={"wd_ids": [a["wd_id"], b["wd_id"]], "languages": [a["l"], b["l"]],
                      "non_en_page_views": [a["non_en_page_views"], b["non_en_page_views"]],
                      "hpi": [a["hpi"], b["hpi"]]},
            )
