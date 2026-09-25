"""Stack Exchange closed questions: question titles from non-programming Stack Exchange sites that are one closed,
standalone question ("Is it safe to refreeze thawed chicken?", "Did Einstein fail math?", "Which is better for
touring, steel or aluminium frames?").

Source: flax-sentence-embeddings/stackexchange_title_best_voted_answer_jsonl (per-site configs; the `title_body`
column holds the question title only). Titles run through the quora_closed filter chain (closed opener, single
question, no typos, not about the asker, not a request, needs no unseen context, not dated) with its political
regex fixed (`elect\\w*` matched electricity). Yes/no -> Noul; "Which is better, A or B?" -> Choice with A/B as
keys. No truth, no node_hint (beam walk). At most SITE_CAP_PCT of the output from any one site.
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
TARGET = env_int("TARGET_STACKEXCHANGE_CLOSED", 10000)
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
    cap = int(TARGET * SITE_CAP)
    per_site: Counter = Counter()
    picked = []
    for it in hash_order(pool, lambda x: x["key"], SALT):
        if per_site[it["site"]] >= (cap // 2 if it["site"] in NICHE else cap):
            continue
        per_site[it["site"]] += 1
        picked.append(it)
        if len(picked) == TARGET:
            break
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
        yield Question(
            text=q,
            primitive=it["primitive"],
            hemisphere=hemisphere,
            kind=kind,
            origin="dataset",
            source=NAME,
            options=options,
            source_item_id=f"{it['site']}:{it['key']}",
            license=LICENSE,
            meta=meta,
        )
    print("stackexchange_closed funnel:", dict(sorted(FUNNEL.items())))
    print("per site:", dict(per_site.most_common()))
