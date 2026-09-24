"""Jester jokes: "How funny is this joke?" with the -10..+10 user ratings binned into 5 levels."""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import pyarrow.parquet as pq

from askjev.model import HumanDist, Question

NAME = "jester"
# The official host (eigentaste.berkeley.edu) was unreachable on 2026-09-24 and its mirror
# (goldberg.berkeley.edu/jester-data) has ratings only, no joke texts. This public HF mirror has the
# 140 Jester jokes with their texts and every per-user rating. Its llama-70b column is not used.
URL = "https://huggingface.co/datasets/SeppeV/jester_jokes_extracted/resolve/main/data/train-00000-of-00001.parquet"
FILE = "jester_jokes_extracted.parquet"
LICENSE = "Jester dataset: free for research use with citation (Goldberg et al. 2001); HF mirror SeppeV/jester_jokes_extracted"
TARGET = 100
SEED = "jester-20260924"
MIN_RATINGS = 1000
EDGES = (-6.0, -2.0, 2.0, 6.0)  # equal-width bins over -10..+10

LEVELS = [
    "Not funny at all: it falls flat or annoys me",
    "Barely funny: I get it, but there's no real reaction",
    "Mildly amusing: a faint smile",
    "Funny: a genuine laugh",
    "Hilarious: laughing out loud, one of the funniest jokes I know",
]

SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spic|chink|kike|gook|wetback|towelhead|raghead)\b", re.I)
MINORS = re.compile(r"\b(child|children|kids?|little (boy|girl)|\d{1,2}[- ]?year[- ]?old (boy|girl)|schoolgirl|teen\w*)\b", re.I)
SEXUAL = re.compile(
    r"\b(sex\w*|made love|make love|making love|porn\w*|nude|naked|orgasm\w*|virgin\w*|penis\w*|vagina\w*|"
    r"boobs?|breasts?|tits|condoms?|viagra|erect\w*|hooker|prostitut\w*|blow ?job|screw\w*|horny|in bed|"
    r"bedroom|dick|cock|pussy|balls|testicles?|masturbat\w*|sperm|pregnan\w*|brothel)\b",
    re.I,
)
OFFENSIVE = re.compile(
    r"\b(rednecks?|blondes?|polish|polack|mexicans?|jews?|jewish|irish\w*|chukcha|eskimos?|italians?|chinese|black guy|"
    r"lesbians?|gays?|homosexual\w*|arabs?|muslims?|nuns?|priests?|rabbi|hell|damn|shit\w*|fuck\w*|bitch\w*|"
    r"bastard|ass|asshole|crap|dead|die[sd]?|kill\w*|suicid\w*|funeral|cancer|aids|drunk)\b",
    re.I,
)
POLITICAL = re.compile(r"\b(bush|clinton|gore|congress|senat\w*|president|democrat\w*|republican\w*|politician\w*|monica|elections?|government|parliament)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(s: str) -> str:
    s = s.replace("\r", "")
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", s)]
    return "\n\n".join(p for p in paras if p)


def _bin(x: float) -> int:
    return sum(x >= e for e in EDGES)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = []
    for r in pq.read_table(raw_dir / FILE, columns=["jokeId", "jokeText", "ratings", "mean_score"]).to_pylist():
        text = _clean(r["jokeText"])
        ratings = [x for x in r["ratings"] if x is not None and -10 <= x <= 10]
        if not text or len(ratings) < MIN_RATINGS or SLURS.search(text):
            continue
        sexual = bool(SEXUAL.search(text))
        if sexual and MINORS.search(text):
            continue
        rows.append((r["jokeId"], text, ratings, r["mean_score"], sexual))

    rng = random.Random(SEED)
    picked = sorted(rng.sample(rows, min(TARGET, len(rows))), key=lambda r: int(r[0].split("_")[1]))
    for jid, text, ratings, mean, sexual in picked:
        counts = [0] * 5
        for x in ratings:
            counts[_bin(x)] += 1
        n = len(ratings)
        flags = []
        if sexual or OFFENSIVE.search(text):
            flags.append("sensitive")
        if POLITICAL.search(text):
            flags.append("political")
        yield Question(
            text="How funny is this joke?",
            primitive="score",
            hemisphere="self",
            kind="taste",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            state={"joke": text},
            node_hint="self.personality.humor_style",
            human_text="How funny do most people find this joke?",
            source_item_id=jid,
            license=LICENSE,
            human=[
                HumanDist(
                    population="Jester users",
                    distribution={str(i): c / n for i, c in enumerate(counts)},
                    n=n,
                    source="Jester online joke recommender (Berkeley), via HF SeppeV/jester_jokes_extracted",
                )
            ],
            meta={
                "mean_rating": round(mean, 3),
                "dist_method": "ratings -10..+10 binned at -6, -2, 2, 6 (equal width)",
                **({"flags": flags} if flags else {}),
            },
        )
