"""How bad is a health state, and is it worse than being dead? (research pass 2, idea 20.)

Human data: the US value set for the EQ-5D-5L (Pickard, Law, Jiang et al. 2019, Value in Health 22:931-941), from
time-trade-off and discrete-choice interviews with 1,134 US adults. It gives every one of the 3,125 health states a
utility: 1 is full health, 0 is as bad as being dead, below 0 is worse than dead (the worst state is -0.573). The
coefficients below are the published ones, checked against the `eq5d` R package (v0.17.0, MIT, value set "USA",
type "VT").

Two question sets over health states described on the five EQ-5D dimensions (mobility, self-care, usual activities,
pain or discomfort, anxiety or depression; the level wording is paraphrased):
- time trade-off (the valuation method itself): 10 years in the state, then death; how many years in full health
  would be as good? 150 states, spread evenly over the value set's answers, including "worse than dying now".
- pairs: which of two states is worse to live in? 150 pairs across the range of utility gaps.
The value set is a fitted model of people's average valuations, so it is the truth here, not a distribution.
"""

from __future__ import annotations

import itertools
import random
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "health_states"
NODE = "world.health.medicine.health_state_values"
LICENSE = ("US EQ-5D-5L value set coefficients as published (Pickard et al. 2019), via the eq5d R package (MIT); "
           "dimension wording paraphrased from the EQ-5D-5L descriptive system (EuroQol); non-commercial research")

US = {  # decrements from 1 for levels 2-5 of each dimension
    "MO": [0, -0.096, -0.122, -0.237, -0.322], "SC": [0, -0.089, -0.107, -0.220, -0.261],
    "UA": [0, -0.068, -0.101, -0.255, -0.255], "PD": [0, -0.060, -0.098, -0.318, -0.414],
    "AD": [0, -0.057, -0.123, -0.299, -0.321],
}
DIMS = ["MO", "SC", "UA", "PD", "AD"]
WORDS = {
    "MO": ["no problems walking about", "slight problems walking about", "moderate problems walking about",
           "severe problems walking about", "unable to walk about"],
    "SC": ["no problems washing or dressing", "slight problems washing or dressing",
           "moderate problems washing or dressing", "severe problems washing or dressing", "unable to wash or dress"],
    "UA": ["no problems doing usual activities (work, study, housework, family or leisure)",
           "slight problems doing usual activities", "moderate problems doing usual activities",
           "severe problems doing usual activities", "unable to do usual activities"],
    "PD": ["no pain or discomfort", "slight pain or discomfort", "moderate pain or discomfort",
           "severe pain or discomfort", "extreme pain or discomfort"],
    "AD": ["not anxious or depressed", "slightly anxious or depressed", "moderately anxious or depressed",
           "severely anxious or depressed", "extremely anxious or depressed"],
}
TTO = {"worse": "None: living in this state would be worse than dying now",
       **{f"y{y:02d}": (f"{y} year" if y == 1 else f"{y} years") + (" (the state is as good as full health)" if y == 10 else "")
          for y in range(11)}}


def fetch(raw_dir: Path) -> None:
    """The coefficients are transcribed above; nothing to download."""


def utility(state: tuple[int, ...]) -> float:
    return round(1 + sum(US[d][lv - 1] for d, lv in zip(DIMS, state)), 3)


def describe(state: tuple[int, ...]) -> str:
    return "; ".join(WORDS[d][lv - 1] for d, lv in zip(DIMS, state))


def code(state: tuple[int, ...]) -> str:
    return "".join(map(str, state))


def tto_key(u: float) -> str:
    return "worse" if u < 0 else f"y{min(10, max(0, round(10 * u))):02d}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    rng = random.Random(2019)
    states = [s for s in itertools.product(range(1, 6), repeat=5) if s != (1, 1, 1, 1, 1)]
    by_key: dict[str, list] = {}
    for s in states:
        by_key.setdefault(tto_key(utility(s)), []).append(s)
    per = 150 // len(TTO) + 1
    picked = [s for k in TTO for s in rng.sample(sorted(by_key.get(k, [])), min(per, len(by_key.get(k, []))))][:150]
    for s in picked:
        u = utility(s)
        yield Question(
            text=f"Imagine you would live for 10 years in the following health state and then die: {describe(s)}. "
                 "How many years in full health, followed by death, would be just as good as those 10 years?",
            primitive="choice", hemisphere="world", kind="evaluative", origin="dataset", source=NAME, options=TTO,
            node_hint=NODE, license=LICENSE, truth=tto_key(u), source_item_id=f"tto:{code(s)}",
            meta={"experiment": "health_states", "set": "tto", "state": code(s), "utility": u, "ordered": True})
    pairs, seen = [], set()
    while len(pairs) < 150:
        a, b = rng.sample(states, 2)
        ua, ub = utility(a), utility(b)
        gap = abs(ua - ub)
        band = "small" if gap < 0.1 else "medium" if gap < 0.3 else "large"
        if ua == ub or (a, b) in seen or sum(p[2] == band for p in pairs) >= 50:
            continue
        seen.add((a, b))
        pairs.append((a, b, band))
    for a, b, band in pairs:
        ua, ub = utility(a), utility(b)
        yield Question(
            text="Which of these two health states would be worse to live in?",
            primitive="choice", hemisphere="world", kind="evaluative", origin="dataset", source=NAME,
            options={"state_a": describe(a), "state_b": describe(b)}, node_hint=NODE, license=LICENSE,
            truth="state_a" if ua < ub else "state_b", source_item_id=f"pair:{code(a)}:{code(b)}",
            meta={"experiment": "health_states", "set": "pair", "a": code(a), "b": code(b), "u_a": ua, "u_b": ub,
                  "gap": round(abs(ua - ub), 3), "band": band})
