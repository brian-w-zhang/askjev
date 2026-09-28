"""Guess two-thirds of the average (docs/15 E24; docs/experiments/reasoning_beauty_contest.md).

Everyone picks a whole number from 0 to 100; the winner is closest to two-thirds (or half) of the average. Human
data, as published means (no distributions are stored): Nagel 1995 (American Economic Review 85:1313-1326, Figure 1,
p. 1316), first rounds in the lab, mean 36.73 for p = 2/3 and 27.05 for p = 1/2; Richard Thaler's 1997 Financial
Times contest (reported in Bosch-Domènech, Montalvo, Nagel & Satorra 2002, American Economic Review 92:1687-1701),
mean 18.91, winning number 13. The Spektrum and Expansión contests from the same paper are left out: their means
could not be verified. For each crowd, two questions: which number Jev picks, and what it expects the crowd's
average to be. A fourth crowd, copies of Jev itself, has no human data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "beauty_contest"
NODE = "self.personality.risk_decision_style.guessing_games"
LICENSE = "Game from Nagel 1995 and Bosch-Domènech et al. 2002 (published means, research use with citation); wording authored"
BINS = {"b000": "0", "b001": "1 to 4", **{f"b{lo:03d}": f"{lo} to {lo + 4 if lo < 95 else 100}" for lo in range(5, 100, 5)}}

CROWDS = [  # (item, who the other players are, p, published mean, source)
    ("lab_two_thirds", "about 15 university students in an economics lab, most playing this game for the first time",
     "two-thirds", 36.73, "Nagel 1995, first round, p = 2/3"),
    ("lab_half", "about 15 university students in an economics lab, most playing this game for the first time",
     "half", 27.05, "Nagel 1995, first round, p = 1/2"),
    ("ft", "several thousand readers of the Financial Times who mailed in entries to a newspaper contest",
     "two-thirds", 18.91, "Thaler 1997 Financial Times contest, via Bosch-Domènech et al. 2002"),
    ("copies", "about 15 other copies of you, the same AI model, each answering this same question independently",
     "two-thirds", None, None),
]


def fetch(raw_dir: Path) -> None:
    """Nothing to download: the published means are transcribed above."""


def _bin(x: float) -> str:
    x = round(x)
    return "b000" if x == 0 else "b001" if x < 5 else f"b{min(95, 5 * (x // 5)):03d}"


def normalize(raw_dir: Path) -> Iterator[Question]:
    for item, who, p, mean, src in CROWDS:
        frac = 2 / 3 if p == "two-thirds" else 1 / 2
        rules = (f"You and the other players each pick a whole number from 0 to 100. The winner is the player whose "
                 f"number is closest to {p} of the average of all the numbers picked. The other players are {who}.")
        meta = {"experiment": "beauty_contest", "crowd": item, "p": frac, "human_mean": mean, "human_source": src,
                "winning_number": round(frac * mean, 2) if mean is not None else None, "ordered": True}
        yield Question(text=f"{rules} Which number do you pick?", primitive="choice", hemisphere="self", kind="forecast",
                       origin="dataset" if mean else "synthetic", source=NAME, options=BINS, node_hint=NODE,
                       license=LICENSE, source_item_id=f"{item}:pick", meta={**meta, "ask": "pick"})
        yield Question(text=f"{rules} What do you expect the average of all the numbers picked to be?",
                       primitive="choice", hemisphere="world", kind="forecast", origin="dataset" if mean else "synthetic",
                       source=NAME, options=BINS, node_hint=NODE, license=LICENSE, source_item_id=f"{item}:average",
                       truth=_bin(mean) if mean is not None else None, meta={**meta, "ask": "average"})
