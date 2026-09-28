"""Anchoring with an explicitly random anchor (docs/15 E10; docs/experiments/reasoning_anchoring.md).

The classic: Tversky & Kahneman 1974 (Science 185:1124-1131) spun a wheel of fortune in front of participants, asked
whether the percentage of African countries in the UN was higher or lower than the number it landed on, then asked
for an estimate. Median estimates were 25 for a wheel landing on 10 and 45 for 65 (kept in meta; no distribution
exists). Here the same question, plus ten quantities with known answers written for this project, each asked three
ways: after a wheel landing low, after it lands high, and with no wheel. Answers are 21 ordered bins (about 0 to
about 100, in fives), so a shift between the low and high anchor can be measured.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "anchoring"
NODE = "world.science.psychology_neuroscience.cognition.judgment_biases"
LICENSE = "Classic item transcribed from Tversky & Kahneman 1974 (research use with citation); other items authored for this project"
BINS = {f"v{v:03d}": f"About {v}" for v in range(0, 101, 5)}

# (item, what is being estimated, unit, truth, low anchor, high anchor)
ITEMS = [
    ("piano_keys", "the number of keys on a standard modern piano", "keys", 88, 40, 100),
    ("earth_water", "the percentage of the Earth's surface covered by water", "percent", 71, 30, 95),
    ("body_water", "the percentage of an adult human body's weight that is water", "percent", 60, 25, 90),
    ("mozart", "the age at which Mozart died", "years", 35, 20, 70),
    ("lincoln", "the age at which Abraham Lincoln died", "years", 56, 30, 85),
    ("mlk", "the age at which Martin Luther King Jr. died", "years", 39, 20, 75),
    ("africa_count", "the number of countries in Africa", "countries", 54, 25, 85),
    ("nitrogen", "the percentage of the Earth's atmosphere that is nitrogen", "percent", 78, 40, 95),
    ("teeth", "the number of teeth in a full adult human set, including wisdom teeth", "teeth", 32, 12, 70),
    ("hand_bones", "the number of bones in one adult human hand, including the wrist", "bones", 27, 10, 60),
]


def fetch(raw_dir: Path) -> None:
    """Nothing to download: the classic item is transcribed, the rest are written here with their answers."""


def _key(x: float) -> str:
    return f"v{min(100, int(5 * round(x / 5))):03d}"


def _q(text, item, cond, anchor, truth, classic=False, **meta) -> Question:
    return Question(text=text, primitive="choice", hemisphere="world", kind="factual",
                    origin="dataset" if classic else "synthetic", source=NAME, options=BINS, node_hint=NODE,
                    truth=truth, license=LICENSE, source_item_id=f"{item}:{cond}",
                    meta={"experiment": "anchoring", "item": item, "condition": cond, "anchor": anchor,
                          "classic": classic, "ordered": True, **meta})


def _wheel(what: str, anchor: int) -> str:
    return (f"A wheel of fortune numbered 0 to 100 is spun in front of you and stops at {anchor}. Is {what} higher or "
            f"lower than {anchor}? Now give your best estimate of {what}.")


def normalize(raw_dir: Path) -> Iterator[Question]:
    what = "the percentage of African countries among the members of the United Nations"
    tk = {"low": 10, "high": 65}
    for cond, a in tk.items():
        yield _q(_wheel(what, a), "africa_un", cond, a, None, classic=True,
                 human_median={"low": 25, "high": 45}[cond],
                 human_note="Tversky & Kahneman 1974: median estimates were 25 (wheel at 10) and 45 (wheel at 65). "
                            "No truth is used: the share has changed since 1974 (about 28% today, 54 of 193).")
    yield _q(f"What is your best estimate of {what}?", "africa_un", "none", None, None, classic=True)
    for item, w, unit, truth, lo, hi in ITEMS:
        for cond, a in (("low", lo), ("high", hi)):
            yield _q(_wheel(w, a), item, cond, a, _key(truth), exact=truth)
        yield _q(f"What is your best estimate of {w}?", item, "none", None, _key(truth), exact=truth)
