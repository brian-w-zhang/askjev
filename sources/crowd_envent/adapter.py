"""Whose reading of an event does Jev share: the writer's own, or other readers'? (research pass 2, idea 11)

Human data: crowd-enVent (Troiano, Oberländer & Klinger 2023, Computational Linguistics 49(1)): people described an
event from their own life that made them feel a given emotion, then rated their own appraisals of it (1 not at all -
5 extremely). 1,200 of those texts were later read by 5 other people each, shown with the emotion words hidden
(`hidden_emo_text`), who guessed the writer's emotion and appraisals. So each text has two answers: the writer's own
(truth) and the readers' split (the human distribution).

Two sets, both on the validated texts: the emotion the writer felt (13 options, as in the study) for 600 texts,
about 46 per writer emotion; and four appraisals (how pleasant, how sudden, how responsible the writer was, how
responsible someone else was) for 150 of those texts.
"""

from __future__ import annotations

import csv
import random
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "crowd_envent"
NODE_EMO = "world.science.psychology_neuroscience.emotion.reading_emotions"
NODE_APP = "world.science.psychology_neuroscience.emotion.event_appraisals"
LICENSE = "Research use with citation (crowd-enVent, Troiano, Oberländer & Klinger 2023); no license file in the release"
URL = "https://www.romanklinger.de/data-sets/crowd-enVent2023.zip"
EMOTIONS = ["anger", "boredom", "disgust", "fear", "guilt", "joy", "no-emotion", "pride", "relief", "sadness", "shame",
            "surprise", "trust"]
OPTIONS = {e.replace("-", "_"): ("No particular emotion" if e == "no-emotion" else e.capitalize()) for e in EMOTIONS}
APPRAISALS = {  # column: (question, five levels from the study's 1 'not at all' to 5 'extremely')
    "pleasantness": ("How pleasant was the event itself for the writer?",
                     ["Not at all pleasant", "Slightly pleasant", "Moderately pleasant", "Very pleasant", "Extremely pleasant"]),
    "suddenness": ("How suddenly did the event happen for the writer?",
                   ["Not at all sudden", "Slightly sudden", "Moderately sudden", "Very sudden", "Extremely sudden"]),
    "self_responsblt": ("How responsible was the writer themselves for the event?",
                        ["Not at all responsible", "Slightly responsible", "Moderately responsible", "Very responsible",
                         "Entirely responsible"]),
    "other_responsblt": ("How responsible was someone else for the event?",
                         ["Nobody else was responsible", "Someone else was slightly responsible",
                          "Someone else was moderately responsible", "Someone else was very responsible",
                          "Someone else was entirely responsible"]),
}
PER_EMOTION, APPRAISAL_TEXTS = 46, 150


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "corpus" / "crowd-enVent_generation.tsv").exists():
        urllib.request.urlretrieve(URL, raw_dir / "ce.zip")
        zipfile.ZipFile(raw_dir / "ce.zip").extractall(raw_dir)


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def normalize(raw_dir: Path) -> Iterator[Question]:
    gen = {r["text_id"]: r for r in _read(raw_dir / "corpus" / "crowd-enVent_generation.tsv")}
    val = defaultdict(list)
    for r in _read(raw_dir / "corpus" / "crowd-enVent_validation.tsv"):
        val[r["text_id"]].append(r)
    ids = sorted(t for t in val if t in gen and gen[t]["hidden_emo_text"].strip())
    rng = random.Random(2023)
    by_emo = defaultdict(list)
    for t in ids:
        by_emo[gen[t]["emotion"]].append(t)
    picks = sorted(t for e in EMOTIONS for t in rng.sample(sorted(by_emo[e]), min(PER_EMOTION, len(by_emo[e]))))
    app = set(rng.sample(picks, APPRAISAL_TEXTS))
    for t in picks:
        g, readers = gen[t], val[t]
        story = g["hidden_emo_text"].strip()
        dist = {k: 0.0 for k in OPTIONS}
        for r in readers:
            dist[r["emotion"].replace("-", "_")] += 1 / len(readers)
        yield Question(
            text="Someone wrote `story` about an event in their own life. Which emotion did the writer feel?",
            state={"story": story}, primitive="choice", hemisphere="world", kind="perception", origin="dataset", source=NAME,
            options=OPTIONS, truth=g["emotion"].replace("-", "_"), node_hint=NODE_EMO, license=LICENSE,
            source_item_id=f"{t}:emotion",
            human=[HumanDist(population="crowd-enVent readers (Prolific), 5 per text", distribution=dist, n=len(readers),
                             source="crowd-enVent_validation.tsv, column emotion (readers' guesses)")],
            meta={"experiment": "crowd_envent", "set": "emotion", "text_id": t, "writer_emotion": g["emotion"]})
        if t not in app:
            continue
        for col, (q, levels) in APPRAISALS.items():
            rd = {str(i): 0.0 for i in range(5)}
            for r in readers:
                rd[str(int(r[col]) - 1)] += 1 / len(readers)
            yield Question(
                text=f"Someone wrote `story` about an event in their own life. {q}",
                state={"story": story}, primitive="score", hemisphere="world", kind="perception", origin="dataset",
                source=NAME, options=levels, truth=int(g[col]) - 1, node_hint=NODE_APP, license=LICENSE,
                source_item_id=f"{t}:{col}",
                human=[HumanDist(population="crowd-enVent readers (Prolific), 5 per text", distribution=rd, n=len(readers),
                                 source=f"crowd-enVent_validation.tsv, column {col} (1-5)")],
                meta={"experiment": "crowd_envent", "set": "appraisal", "appraisal": col, "text_id": t,
                      "writer_emotion": g["emotion"], "writer_level": int(g[col]) - 1})
