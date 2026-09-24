"""Scruples Anecdotes (AllenAI, Apache-2.0): r/AmItheAsshole posts with the community's verdict counts
(AUTHOR / OTHER / EVERYBODY / NOBODY / INFO)."""

from __future__ import annotations

import importlib.util
import json
import random
import re
import tarfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "scruples_anecdotes"
URL = "https://storage.googleapis.com/ai2-mosaic-public/projects/scruples/v1.0/data/anecdotes.tar.gz"
LICENSE = "Apache-2.0 (allenai/scruples); post text from Reddit r/AmItheAsshole"
TARGET = 8000
SEED = 20260924
SPLITS = ("train", "dev", "test")
MAX_CHARS = 1500
MIN_VOTES = 5

# Content filters are shared with the scruples (dilemmas) adapter.
_spec = importlib.util.spec_from_file_location("sources.scruples", Path(__file__).parents[1] / "scruples" / "adapter.py")
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)

POLITICAL = re.compile(
    r"\b(abortion\w*|pro-?life|pro-?choice|trump\w*|biden|obama|hillary|republican\w*|democrat\w*|maga|"
    r"liberals?|conservatives?|gun control|immigration|illegal (aliens?|immigrants?)|black lives matter|blm|all lives matter|"
    r"feminis\w*|trans rights|same-sex marriage|gay marriage|death penalty|anti-?vax\w*|vaccines?|"
    r"election\w*|politic\w*|left-wing|right-wing|socialis\w*|communis\w*|brexit)\b",
    re.I,
)

FAMILY = re.compile(
    r"\b(mom|moms|mum|mums|mother|mothers|dad|dads|father|fathers|parents?|sisters?|brothers?|siblings?|sons?|"
    r"daughters?|kids?|children|child|grandma|grandpa|grandmother|grandfather|grandparents?|aunts?|uncles?|"
    r"cousins?|nieces?|nephews?|in-laws?|mil|fil|sil|bil|step-?(mom|dad|mother|father|son|daughter|sister|brother)s?|"
    r"family|families|husband|wife|spouse)\b",
    re.I,
)
SOCIAL = re.compile(
    r"\b(friends?|bff|best friend|bf|gf|boyfriend|girlfriend|dating|dated|first date|a date|exes|ex-?(bf|gf|boyfriend|girlfriend)|"
    r"my ex|roommates?|flatmates?|housemates?|classmates?|crush|tinder|hinge|bumble)\b",
    re.I,
)

OPTIONS = {
    "author": "The person telling the story",
    "other": "The other person or people",
    "everybody": "Everyone involved",
    "nobody": "Nobody is in the wrong",
    "info": "Not enough information to judge",
}
LABELS = {"AUTHOR": "author", "OTHER": "other", "EVERYBODY": "everybody", "NOBODY": "nobody", "INFO": "info"}


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / "anecdotes" / f"{s}.scruples-anecdotes.jsonl").exists() for s in SPLITS):
        return
    out = raw_dir / "anecdotes.tar.gz"
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)
    with tarfile.open(out) as tf:
        tf.extractall(raw_dir, filter="data")


def _trim(s: str) -> str:
    s = s.replace("\r", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def node_for(story: str) -> str:
    """Family vs friends/dating child when one side clearly dominates the keyword hits, else the L2 node."""
    f = len(FAMILY.findall(story))
    s = len(SOCIAL.findall(story))
    if f >= 2 and f >= 2 * s:
        return "self.values.everyday_ethics.family_conflicts"
    if s >= 2 and s >= 2 * f:
        return "self.values.everyday_ethics.friends_dating_social"
    return "self.values.everyday_ethics"


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = []
    seen = set()
    for split in SPLITS:
        with open(raw_dir / "anecdotes" / f"{split}.scruples-anecdotes.jsonl", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                title, text = _trim(r["title"]), _trim(r["text"])
                if not title or not text or len(text) > MAX_CHARS or text.lower() in ("[deleted]", "[removed]"):
                    continue
                if sum(r["label_scores"].values()) < MIN_VOTES:
                    continue
                story = f"{title}\n\n{text}"
                key = re.sub(r"\W+", " ", story.lower()).strip()
                if key in seen:
                    continue
                sexual = bool(F.SEXUAL.search(story))
                if F.SLURS.search(story) or F.SEXUAL_VIOLENCE.search(story) or (sexual and F.MINORS.search(story)):
                    continue
                seen.add(key)
                pool.append((split, r, story, sexual))

    rng = random.Random(SEED)
    pool.sort(key=lambda x: (x[0], x[1]["id"]))
    rng.shuffle(pool)
    picked = sorted(pool[:TARGET], key=lambda x: (x[0], x[1]["id"]))

    for split, r, story, sexual in picked:
        counts = {LABELS[k]: v for k, v in r["label_scores"].items()}
        n = sum(counts.values())
        flags = ["sensitive"] if (sexual or F.SELF_HARM.search(story) or F.VIOLENT.search(story)) else []
        if POLITICAL.search(story):
            flags.append("political")
        yield Question(
            text="Based on `story`, who is in the wrong?",
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"story": story},
            node_hint=node_for(story),
            human_text="Based on `story`, who would most people say is in the wrong?",
            source_item_id=f"{split}:{r['id']}",
            license=LICENSE,
            human=[
                HumanDist(
                    population="r/AmItheAsshole voters",
                    distribution={k: counts.get(k, 0) / n for k in OPTIONS},
                    n=n,
                    source="Scruples Anecdotes v1.0 label_scores (verdict counts from top-level comments)",
                )
            ],
            meta={
                "split": split,
                "post_id": r["post_id"],
                "post_type": r["post_type"],
                "label": LABELS[r["label"]],
                "label_scores": r["label_scores"],
                "action": (r.get("action") or {}).get("description"),
            }
            | ({"flags": flags} if flags else {}),
        )
