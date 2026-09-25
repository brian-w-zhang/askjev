"""Hate Speech and Offensive Language (Davidson et al. 2017, ICWSM): 24,783 tweets, each labelled by 3+
CrowdFlower annotators as hate speech, offensive language, or neither. Source: HF tdavidson/hate_speech_offensive
(the authors' copy of github.com/t-davidson/hate-speech-and-offensive-language).

Template "hate_speech_offensive.class": Choice over hate_speech / offensive / neither, truth = the majority
class. HumanDist = the annotator shares (n = annotators for that tweet). Balanced ~700 hate / 650 / 650 in
salted-hash order (hate speech is 6% of the data).
Cleaning: HTML entities unescaped, @handles replaced by @user and URLs by [link] (the tweets are from private
people), near-empty tweets and exact duplicates dropped. Slurs are kept, because hate speech in this set is
mostly slur-based and dropping them would gut the class; every tweet with a slur, sexual words or an
offensive/hate majority is flagged `sensitive` (hidden from the displayed map). Political keywords -> `political`.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "hate_speech_offensive"
URL = "https://huggingface.co/api/datasets/tdavidson/hate_speech_offensive/parquet/default/train/0.parquet"
LICENSE = "MIT"
NODE = "machine.trust_safety.toxicity_harassment"
TARGET = env_int("TARGET_HATE_SPEECH_OFFENSIVE", 2000)
HATE_SHARE = 0.35
TEXT = "Is `post` hate speech, offensive but not hate speech, or neither?"
OPTIONS = {
    "hate_speech": "It expresses hatred toward a group, or aims to humiliate or insult people, because of race, "
    "ethnicity, religion, gender, sexual orientation or another group identity",
    "offensive": "It is vulgar, crude or insulting, but not hateful toward a group",
    "neither": "It is neither hateful nor offensive",
}
CLASSES = ["hate_speech", "offensive", "neither"]
SLUR = re.compile(r"\b(nigg\w*|fag\w*|kikes?|spics?|chinks?|retard\w*|trann(y|ies)|wetbacks?|dykes?|queers?|"
                  r"beaners?|coons?|towelheads?|raghead\w*|gooks?|crackers?)\b", re.I)
SEXUAL = re.compile(r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|horny|pussy|dick|cock|blowjob\w*|hoes?|thot\w*)\b", re.I)
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|romney|republican\w*|democrat\w*|gop|liberals?|conservatives?|"
    r"election\w*|abortion\w*|immigra\w*|illegals?|deport\w*|tea ?party|teabaggers?|isis|muslims?|israel\w*|"
    r"palestin\w*|feminis\w*|obamacare|gun\w*|nra|momsdemand)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = html.unescape(html.unescape(t or ""))
    t = re.sub(r"https?://\S+", "[link]", t)
    t = re.sub(r"@\w+", "@user", t)
    return " ".join(t.split())


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").with_row_index("row")
    seen: set[str] = set()
    pools: dict[str, list] = {k: [] for k in CLASSES}
    cols = ["row", "tweet", "count", "hate_speech_count", "offensive_language_count", "neither_count", "class"]
    for row, tweet, n, h, o, ne, cls in df.select(cols).iter_rows():
        t = _clean(tweet)
        core = re.sub(r"(@user|\[link\]|\bRT\b|[^\w])", "", t)
        if len(core) < 10 or t.lower() in seen or not n:
            continue
        seen.add(t.lower())
        pools[CLASSES[cls]].append((row, t, cls, n, (h, o, ne)))
    n_hate = min(len(pools["hate_speech"]), round(TARGET * HATE_SHARE))
    n_off = (TARGET - n_hate) // 2
    picked = [("hate_speech", x) for x in hash_order(pools["hate_speech"], lambda x: x[0], "davidson.hate")[:n_hate]]
    picked += [("offensive", x) for x in hash_order(pools["offensive"], lambda x: x[0], "davidson.off")[:n_off]]
    picked += [("neither", x) for x in
               hash_order(pools["neither"], lambda x: x[0], "davidson.neither")[: TARGET - n_hate - n_off]]
    for k, (row, t, cls, n, counts) in sorted(picked, key=lambda z: z[1][0]):
        flags = []
        if k != "neither" or SLUR.search(t) or SEXUAL.search(t):
            flags.append("sensitive")
        if POLITICAL.search(t):
            flags.append("political")
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"post": t[:1500]},
            shape="classify",
            node_hint=NODE,
            template_id="hate_speech_offensive.class",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=k,
            human=[
                HumanDist(
                    population="CrowdFlower annotators",
                    distribution={c: round(v / n, 4) for c, v in zip(CLASSES, counts)},
                    n=n,
                    source="Davidson et al. 2017 annotator counts",
                )
            ],
            meta={"counts": dict(zip(CLASSES, counts)), **({"flags": flags} if flags else {})},
        )
