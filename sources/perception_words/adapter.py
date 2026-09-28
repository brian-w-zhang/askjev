"""What probability and amount words mean as numbers (docs/13 experiments 1 and 3).

Human data: zonination's "perceptions" survey (Reddit r/samplesize, 2015, MIT): 46 people each gave a probability for
17 phrases ("Highly Likely", "We Doubt", ...) and a number for 10 amount phrases ("A few", "Dozens", ...). The survey
asked "What [probability / number] would you assign to the phrase '<phrase>'?"; Jev gets the same wording with the
answers as ordered bins, and each person's answer is put in the same bin.

Three extra sets have no human data and say so: the reverse direction (a probability, pick the phrase: the round
trip), each probability phrase in three settings (weather, medicine, intelligence), and three amount words across
five settings (does "a few" grow with the thing counted?).
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "perception_words"
NODE = "world.society.languages.word.probability_words"
LICENSE = "MIT (zonination/perceptions, 2015)"
URL = "https://raw.githubusercontent.com/zonination/perceptions/master/"
POP = "Reddit r/samplesize respondents (zonination 2015)"

PCT = {f"p{v:03d}": f"{v}%" for v in range(0, 101, 5)}
# amount bins: small numbers one by one, then roughly doubling
AMOUNT = [("n1", "1", 1, 1), ("n2", "2", 2, 2), ("n3", "3", 3, 3), ("n4", "4", 4, 4), ("n5", "5", 5, 5),
          ("n6_7", "6 to 7", 6, 7), ("n8_10", "8 to 10", 8, 10), ("n11_15", "11 to 15", 11, 15),
          ("n16_25", "16 to 25", 16, 25), ("n26_50", "26 to 50", 26, 50), ("n51_100", "51 to 100", 51, 100),
          ("n101_250", "101 to 250", 101, 250), ("n251_500", "251 to 500", 251, 500),
          ("n501_1000", "501 to 1,000", 501, 1000), ("n1001", "More than 1,000", 1001, float("inf"))]
AMOUNT_OPTS = {k: d for k, d, _, _ in AMOUNT}
SETTINGS_P = {
    "weather": 'A weather forecaster describes the chance of rain tomorrow with the phrase "{p}". What probability of rain does that suggest?',
    "medicine": 'A doctor describes the chance that a new medication causes a side effect with the phrase "{p}". What probability does that suggest?',
    "intelligence": 'An intelligence report describes the chance of an event next month with the phrase "{p}". What probability does that suggest?',
}
SETTINGS_N = {
    "dinner": 'Someone says "{w} people came to my dinner party." How many people is that?',
    "stadium": 'Someone says "{w} people were at the stadium when the gates opened." How many people is that?',
    "rice": 'Someone says "{w} grains of rice fell on the floor." How many grains is that?',
    "years": 'Someone says "I lived there {w} years ago." How many years is that?',
    "emails": 'Someone says "I got {w} emails today." How many emails is that?',
}


def fetch(raw_dir: Path) -> None:
    for f in ("probly.csv", "numberly.csv"):
        if not (raw_dir / f).exists():
            urllib.request.urlretrieve(URL + f, raw_dir / f)


def _cols(path: Path) -> dict[str, list[float]]:
    rows = list(csv.reader(open(path)))
    return {h.strip(): [float(r[i]) for r in rows[1:] if r[i].strip()] for i, h in enumerate(rows[0])}


def _pct_dist(vals: list[float]) -> dict[str, float]:
    d = {k: 0.0 for k in PCT}
    for v in vals:
        d[f"p{min(100, max(0, int(5 * round(v / 5)))):03d}"] += 1 / len(vals)
    return d


def _amount_dist(vals: list[float]) -> dict[str, float]:
    d = {k: 0.0 for k in AMOUNT_OPTS}
    for v in vals:
        v = max(1, round(v))
        k = next(k for k, _, lo, hi in AMOUNT if lo <= v <= hi)
        d[k] += 1 / len(vals)
    return d


def _slug(s: str) -> str:
    return s.lower().replace(" ", "_")


def _q(text, options, set_, item, human=None, truth=None, **meta) -> Question:
    return Question(text=text, primitive="choice", hemisphere="world", kind="perception", origin="dataset", source=NAME,
                    options=options, node_hint=NODE, source_item_id=f"{set_}:{item}", license=LICENSE, truth=truth,
                    human=human or [], meta={"experiment": "perception_words", "set": set_, "item": item, **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    prob = _cols(raw_dir / "probly.csv")
    num = _cols(raw_dir / "numberly.csv")
    for p, vals in prob.items():
        yield _q(f'What probability would you assign to the phrase "{p}"?', PCT, "probability", p,
                 human=[HumanDist(population=POP, distribution=_pct_dist(vals), n=len(vals),
                                  source="zonination/perceptions probly.csv, answers rounded to the nearest 5%")],
                 ordered=True)
        for s, tpl in SETTINGS_P.items():
            yield _q(tpl.format(p=p.lower()), PCT, f"probability_{s}", p, ordered=True, setting=s)
    phrases = {_slug(p): p for p in prob}
    for v in range(0, 101, 5):
        yield _q(f"An event has a {v}% chance of happening. Which phrase describes that chance best?", phrases,
                 "reverse", str(v), value=v)
    for w, vals in num.items():
        if w == "Fractions of":  # a fraction, not a count; the bins can't hold it
            continue
        yield _q(f'What number would you assign to the phrase "{w}"?', AMOUNT_OPTS, "amount", w,
                 human=[HumanDist(population=POP, distribution=_amount_dist(vals), n=len(vals),
                                  source="zonination/perceptions numberly.csv, answers put in the same bins")],
                 ordered=True)
    for w in ("A few", "Several", "Many"):
        for s, tpl in SETTINGS_N.items():
            text = tpl.format(w=w if '"{w}' in tpl else w.lower())  # capitalized only at the start of the quote
            yield _q(text, AMOUNT_OPTS, f"amount_{s}", w, ordered=True, setting=s)
