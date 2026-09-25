"""Stack Exchange closed questions: question titles from non-programming Stack Exchange sites that are one closed,
standalone question ("Is it safe to refreeze thawed chicken?", "Did Einstein fail math?", "Which is better for
touring, steel or aluminium frames?").

Source: flax-sentence-embeddings/stackexchange_title_best_voted_answer_jsonl (per-site configs; the `title_body`
column holds the question title only). Titles run through the quora_closed filter chain (closed opener, single
question, no typos, not about the asker, not a request, needs no unseen context, not dated) with its political
regex fixed (`elect\\w*` matched electricity). Yes/no -> Noul; "Which is better, A or B?" -> Choice with A/B as
keys. No truth. At most SITE_CAP_PCT of the output from any one site.

Wave 6 (TARGET above WAVE5_TARGET): the 30,000 wave 5 rows are unchanged (still no node_hint); the top-up takes
the sites that feed thin nodes first (PRIORITY: cooking, history, sports, money, diy, travel, gardening, pets,
parenting, ...), then the rest in hash order, and gives new world rows a node_hint where the site maps cleanly
(SITE_NODE).
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "stackexchange_closed"
BASE = ("https://huggingface.co/api/datasets/flax-sentence-embeddings/stackexchange_title_best_voted_answer_jsonl/"
        "parquet/{site}/train/0.parquet")
LICENSE = "CC BY-SA (Stack Exchange content; HF card lists CC BY-NC-SA 4.0)"
BASE_TARGET = 10000  # the original sample; a larger TARGET keeps it and tops up (prefix-stable)
WAVE5_TARGET = 30000  # the wave 5 sample; a larger TARGET keeps it and tops up with thin-node sites first
TARGET = env_int("TARGET_STACKEXCHANGE_CLOSED", 55000)
SITE_CAP = env_int("STACKEXCHANGE_CLOSED_SITE_CAP_PCT", 8) / 100
# Sites whose titles are mostly game/fiction/equipment minutiae get half the cap.
NICHE = {"gaming", "scifi", "aviation", "law", "mechanics", "anime", "photo", "boardgames", "homebrew"}
SALT = "stackexchange_closed-20260925"
# Non-programming sites. Religion and politics sites are left out (their titles are mostly doctrine or current
# politics); so are language-learning sites (grammar drills), worldbuilding (questions about the asker's world) and
# rpg (tabletop rules lawyering).
SITES = (
    "skeptics travel cooking english parenting fitness money diy gardening movies scifi bicycles outdoors pets "
    "philosophy history interpersonal workplace academia lifehacks coffee beer boardgames chess gaming music "
    "musicfans photo sports astronomy biology earthscience space aviation law linguistics literature mythology "
    "vegetarianism sustainability expatriates woodworking homebrew martialarts anime health hsm economics cogsci "
    "mechanics crafts genealogy poker puzzling writers"
).split()

_spec = importlib.util.spec_from_file_location("stackexchange_quora_filters",
                                               Path(__file__).parents[1] / "quora_closed" / "adapter.py")
Q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(Q)
_ELECT_FIX = r"elect(s|ed|ing|or\w*|oral|ion\w*)?"  # quora_closed's `elect\w*` also matches electricity
Q.POLITICAL = re.compile(Q.POLITICAL.pattern.replace(r"elect\w*", _ELECT_FIX), re.I)
Q.ELECTION = re.compile(Q.ELECTION.pattern.replace(r"elect\w*", _ELECT_FIX), re.I)
POLITICAL, SENSITIVE = Q.POLITICAL, Q.SENSITIVE

# Titles that only make sense on the site ("Is this a bug?", "Can a paladin cast ...", game-rule minutiae) or ask
# about identifying a work; plus site jargon that assumes the reader knows the site.
SITE_ONLY = re.compile(
    r"\b(identify|identification|this (story|book|movie|film|show|game|plant|bug|insect|spider|word|phrase|quote)|"
    r"story-identification|what is the name|name of the|ID)\b|\b(D&D|5e|3\.5e|pathfinder|dm|gm|npc|pc|"
    r"spell\w*|cantrip\w*|feat|feats)\b",
    re.I,
)
FUNNEL: Counter = Counter()

# Wave 6 top-up: sites that feed thin nodes (food, history, sports, money, everyday how-to, travel, nature) go first.
PRIORITY = (
    "cooking coffee beer homebrew vegetarianism history hsm sports bicycles outdoors fitness martialarts chess money "
    "economics workplace diy lifehacks woodworking crafts travel expatriates gardening pets parenting"
).split()
# node_hint for wave 6 rows (world hemisphere only), where a site's titles sit under one node.
SITE_NODE = {
    "cooking": "world.food.cooking",
    "coffee": "world.food.nonalcoholic_drinks",
    "beer": "world.food.alcoholic_drinks",
    "homebrew": "world.food.alcoholic_drinks",
    "vegetarianism": "world.food",
    "history": "world.history",
    "hsm": "world.science.scientists_discoveries",
    "sports": "world.sports",
    "fitness": "world.health.fitness",
    "martialarts": "world.sports.combat_sports",
    "chess": "world.sports.board_card_games",
    "boardgames": "world.sports.board_card_games",
    "poker": "world.sports.board_card_games",
    "gaming": "world.sports.video_games",
    "money": "world.money.personal_finance",
    "economics": "world.money.economics",
    "workplace": "world.money.careers",
    "diy": "world.society.everyday_how_to",
    "lifehacks": "world.society.everyday_how_to",
    "bicycles": "world.society.everyday_how_to",
    "mechanics": "world.society.everyday_how_to",
    "woodworking": "world.tech.engineering_inventions.materials",
    "crafts": "world.tech.engineering_inventions.materials",
    "travel": "world.places.travel",
    "expatriates": "world.places.moving_abroad",
    "gardening": "world.nature.plants_fungi",
    "pets": "world.nature.pets_breeds",
    "sustainability": "world.nature.ecosystems_conservation",
    "earthscience": "world.nature",
    "astronomy": "world.science.astronomy_space",
    "space": "world.science.astronomy_space",
    "biology": "world.science.biology_genetics",
    "cogsci": "world.science.psychology_neuroscience",
    "health": "world.health",
    "english": "world.society.languages",
    "linguistics": "world.society.languages",
    "mythology": "world.society.mythology_folklore",
    "literature": "world.arts.books",
    "movies": "world.arts.film",
    "music": "world.arts.music",
    "musicfans": "world.arts.music",
    "law": "world.society.crime_law",
    "academia": "world.society.education",
}


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for site in SITES:
        out = raw_dir / f"{site}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(site=site), follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _pool(raw_dir: Path) -> list[dict]:
    titles: list[tuple[str, str]] = []
    for site in SITES:
        df = pl.read_parquet(raw_dir / f"{site}.parquet", columns=["title_body"])
        titles += [(site, t) for t in df["title_body"].to_list() if t]
    FUNNEL["0_titles"] = len(titles)
    vocab = Q._vocab([t for _, t in titles])
    kept: dict[str, dict] = {}
    for site, raw in sorted(set(titles)):
        if SITE_ONLY.search(raw):
            continue
        it = Q._keep(raw, vocab)
        if not it:
            continue
        nk = Q._norm_key(it["q"])
        if nk in kept:
            FUNNEL["dupes"] += 1
            continue
        it["raw"], it["site"] = raw, site
        it["key"] = hashlib.sha1(f"{site}|{raw}".encode()).hexdigest()[:16]
        kept[nk] = it
    for k, v in Q.FUNNEL.items():
        FUNNEL["q_" + k] = v
    FUNNEL["kept"] = len(kept)
    return list(kept.values())


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = _pool(raw_dir)
    per_site: Counter = Counter()
    picked = []
    order = hash_order(pool, lambda x: x["key"], SALT)
    taken: set = set()
    # Pass 1 reproduces the original 10k sample (site cap from BASE_TARGET); pass 2 tops up to the wave 5 30k over the
    # remaining pool in the same hash order, with the site cap recomputed from its goal. Pass 3 (wave 6) tops up to
    # TARGET with PRIORITY sites first, then the rest, cap recomputed from TARGET. Each larger TARGET contains the
    # smaller ones.
    for goal in (min(TARGET, BASE_TARGET), min(TARGET, WAVE5_TARGET)):
        cap = int(max(goal, BASE_TARGET) * SITE_CAP)
        for it in order:
            if len(picked) >= goal:
                break
            if it["key"] in taken or per_site[it["site"]] >= (cap // 2 if it["site"] in NICHE else cap):
                continue
            per_site[it["site"]] += 1
            picked.append(it)
            taken.add(it["key"])
    wave6: set = set()
    if TARGET > WAVE5_TARGET:
        cap = int(TARGET * SITE_CAP)
        prio = set(PRIORITY)
        for it in [x for x in order if x["site"] in prio] + [x for x in order if x["site"] not in prio]:
            if len(picked) >= TARGET:
                break
            if it["key"] in taken or per_site[it["site"]] >= (cap // 2 if it["site"] in NICHE else cap):
                continue
            per_site[it["site"]] += 1
            picked.append(it)
            taken.add(it["key"])
            wave6.add(it["key"])
    FUNNEL["picked"] = len(picked)
    for it in sorted(picked, key=lambda x: x["key"]):
        q = it["q"]
        hemisphere, kind = Q.tag(q, it["primitive"] == "choice")
        flags = [f for f, rx in (("political", POLITICAL), ("sensitive", SENSITIVE)) if rx.search(q)]
        meta = {"site": it["site"], "title": it["raw"]}
        if flags:
            meta["flags"] = flags
        options = None
        if it["primitive"] == "choice":
            options = {Q.slug(o): o for o in it["opts"]}
            if len(options) != len(it["opts"]) or not all(options):
                continue
        node_hint = SITE_NODE.get(it["site"]) if it["key"] in wave6 and hemisphere == "world" else None
        if node_hint:
            FUNNEL["wave6_node_hint"] += 1
        yield Question(
            text=q,
            primitive=it["primitive"],
            hemisphere=hemisphere,
            kind=kind,
            origin="dataset",
            source=NAME,
            node_hint=node_hint,
            options=options,
            source_item_id=f"{it['site']}:{it['key']}",
            license=LICENSE,
            meta=meta,
        )
    print("stackexchange_closed funnel:", dict(sorted(FUNNEL.items())))
    print("per site:", dict(per_site.most_common()))
