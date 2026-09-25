"""Music & Mental Health survey (MxMH, Rasgaitis 2022): how often respondents listen to 16 genres, favorite genre,
and listening habits. Genre-frequency Scores, a favorite-genre Choice, habit Nouls/Choices, and within-genre pairs
("Which do you listen to more often: jazz or metal?") split by who reported the higher frequency (ties excluded)."""

from __future__ import annotations

import csv
import itertools
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "mxmh_music"
URL = "https://raw.githubusercontent.com/crasgaitis/mxmh/main/mxmh_survey_results.csv"  # the dataset author's repo
FILE = "mxmh_survey_results.csv"
LICENSE = "CC0 1.0 (MxMH survey results, Catherine Rasgaitis, Kaggle 2022); copy from the author's GitHub crasgaitis/mxmh"
POP = "MxMH survey respondents (2022 online form shared on Reddit, Discord, and social media; mostly teens and young adults)"
SRC = "MxMH survey (Rasgaitis 2022): share of respondents giving each answer"
PAIR_SRC = "MxMH survey (Rasgaitis 2022): among respondents who reported different listening frequencies, share listening more often to each"
TARGET_PAIRS = env_int("TARGET_MXMH_MUSIC_PAIRS", 5000)  # all 120 genre pairs by default
SALT = "mxmh_music.v1"
NODE = "self.lifestyle.leisure_hobbies"

GENRES = {  # column suffix -> (key, phrase)
    "Classical": ("classical", "classical music"),
    "Country": ("country", "country music"),
    "EDM": ("edm", "EDM (electronic dance music)"),
    "Folk": ("folk", "folk music"),
    "Gospel": ("gospel", "gospel music"),
    "Hip hop": ("hip_hop", "hip hop"),
    "Jazz": ("jazz", "jazz"),
    "K pop": ("k_pop", "K-pop"),
    "Latin": ("latin", "Latin music"),
    "Lofi": ("lofi", "lo-fi"),
    "Metal": ("metal", "metal"),
    "Pop": ("pop", "pop music"),
    "R&B": ("r_and_b", "R&B"),
    "Rap": ("rap", "rap"),
    "Rock": ("rock", "rock music"),
    "Video game music": ("video_game_music", "video game music"),
}
FREQ = ["Never", "Rarely", "Sometimes", "Very frequently"]

NOULS = {  # column -> (text, node) ; survey wording from the Kaggle column descriptions
    "While working": ("Do you listen to music while studying or working?", "self.lifestyle.work_study_life"),
    "Exploratory": ("Do you actively explore new artists and genres?", NODE),
    "Foreign languages": ("Do you regularly listen to music with lyrics in a language you are not fluent in?", NODE),
    "Instrumentalist": ("Do you play an instrument regularly?", NODE),
    "Composer": ("Do you compose music?", NODE),
}
STREAMING = {
    "Spotify": ("spotify", "Spotify"),
    "YouTube Music": ("youtube_music", "YouTube Music"),
    "Apple Music": ("apple_music", "Apple Music"),
    "Pandora": ("pandora", "Pandora"),
    "Other streaming service": ("another_service", "Another streaming service"),
    "I do not use a streaming service.": ("no_streaming", "I don't use a streaming service"),
}
EFFECTS = {
    "Improve": ("improves", "Listening to music improves my mental health"),
    "No effect": ("no_effect", "Listening to music has no effect on my mental health"),
    "Worsen": ("worsens", "Listening to music worsens my mental health"),
}


def fetch(raw_dir: Path) -> None:
    p = raw_dir / FILE
    if not p.exists():
        r = httpx.get(URL, timeout=120, follow_redirects=True)
        r.raise_for_status()
        p.write_bytes(r.content)


def _levels(x: str) -> list[str]:
    return [f"I never listen to {x}", f"I rarely listen to {x}", f"I sometimes listen to {x}",
            f"I listen to {x} very frequently"]


def _hd(dist: dict, n: int, source: str = SRC) -> list[HumanDist]:
    return [HumanDist(population=POP, distribution=dist, n=n, source=source, wave="2022")]


def _choice(rows, col, text, opts, node, kind="taste") -> Question:
    vals = [r[col] for r in rows if r[col] in opts]
    n = len(vals)
    return Question(
        text=text, primitive="choice", hemisphere="self", kind=kind, origin="dataset", source=NAME,
        options={k: d for k, d in opts.values()}, node_hint=node, source_item_id=col, license=LICENSE,
        template_id=f"mxmh_music.{col.lower().replace(' ', '_')}",
        human=_hd({k: round(vals.count(raw) / n, 4) for raw, (k, _) in opts.items()}, n), meta={"column": col},
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    with open(raw_dir / FILE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    for g, (_, x) in GENRES.items():
        vals = [r[f"Frequency [{g}]"] for r in rows if r[f"Frequency [{g}]"] in FREQ]
        n = len(vals)
        yield Question(
            text=f"How often do you listen to {x}?", primitive="score", hemisphere="self", kind="taste",
            origin="template", source=NAME, options=_levels(x), node_hint=NODE, source_item_id=f"Frequency [{g}]",
            license=LICENSE, template_id="mxmh_music.frequency",
            human=_hd({str(i): round(vals.count(f) / n, 4) for i, f in enumerate(FREQ)}, n),
            meta={"column": f"Frequency [{g}]"},
        )

    yield _choice(rows, "Fav genre", "Which of these music genres is your favorite?",
                  {g: v for g, v in GENRES.items()}, NODE)
    yield _choice(rows, "Primary streaming service", "Which streaming service do you mainly use to listen to music?",
                  STREAMING, "self.lifestyle.screens_media", kind="personality")
    yield _choice(rows, "Music effects", "How does listening to music affect your mental health?", EFFECTS,
                  "self.personality.emotions_stress.coping_expressing", kind="personality")

    for col, (text, node) in NOULS.items():
        vals = [r[col] for r in rows if r[col] in ("Yes", "No")]
        n = len(vals)
        yes = vals.count("Yes") / n
        yield Question(
            text=text, primitive="noul", hemisphere="self", kind="personality", origin="dataset", source=NAME,
            node_hint=node, source_item_id=col, license=LICENSE, template_id=f"mxmh_music.{col.lower().replace(' ', '_')}",
            human=_hd({"true": round(yes, 4), "false": round(1 - yes, 4)}, n), meta={"column": col},
        )

    rank = {f: i for i, f in enumerate(FREQ)}
    pairs = list(itertools.combinations(GENRES, 2))
    for a, b in hash_order(pairs, lambda p: f"{p[0]}|{p[1]}", SALT)[:TARGET_PAIRS]:
        (ka, xa), (kb, xb) = GENRES[a], GENRES[b]
        wa = wb = ties = 0
        for r in rows:
            va, vb = rank.get(r[f"Frequency [{a}]"]), rank.get(r[f"Frequency [{b}]"])
            if va is None or vb is None:
                continue
            wa += va > vb
            wb += vb > va
            ties += va == vb
        n = wa + wb
        if n == 0:
            continue
        yield Question(
            text=f"Which do you listen to more often: {xa} or {xb}?", primitive="choice", hemisphere="self",
            kind="taste", origin="template", source=NAME, options=dict(sorted([(ka, xa), (kb, xb)])), node_hint=NODE,
            source_item_id=f"{a}|{b}", license=LICENSE, template_id="mxmh_music.pair",
            human=_hd({ka: round(wa / n, 4), kb: round(wb / n, 4)}, n, PAIR_SRC),
            meta={"columns": [f"Frequency [{a}]", f"Frequency [{b}]"], "ties": ties},
        )
