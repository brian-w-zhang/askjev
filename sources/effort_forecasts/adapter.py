"""What motivates effort? Forecasting 15 incentive treatments, against 208 experts (DellaVigna & Pope 2018).

Data: DellaVigna & Pope 2018, "What Motivates Effort? Evidence and Expert Forecasts", Review of Economic Studies
85(2):1029-1069 (NBER w22193). 9,861 MTurk workers pressed "a" then "b" for 10 minutes (a point per a-b pair) under
one of 18 descriptions of pay. The paper's Table 4 gives each treatment's wording, N and mean points, and for 15 of
them the mean forecast of 208 economists and psychologists, who were told the three benchmark results first. Jev gets
the same benchmarks and forecasts each of the 15 in 50-point bins. Transcribed from Table 4 of the working paper;
fetch() is a no-op.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "effort_forecasts"
NODE = "world.money.economics.incentives_effort"
LICENSE = "Treatment wording and results quoted from DellaVigna & Pope 2018 (Table 4) for research use"
CONTEXT = ("In an online experiment, workers on Amazon Mechanical Turk did a simple typing task for 10 minutes: pressing "
           "the \"a\" key and then the \"b\" key, scoring one point for each a-then-b pair. Everyone got the same base pay; "
           "groups differed only in one paragraph describing a bonus. Three groups' average scores were: "
           "\"Your score will not affect your payment in any way\": 1,521 points. \"As a bonus, you will be paid an extra "
           "1 cent for every 100 points that you score\": 2,029 points. \"As a bonus, you will be paid an extra 10 cents "
           "for every 100 points that you score\": 2,175 points.")
LO, HI, STEP = 1500, 2300, 50
BINS = {"under_1500": "Under 1,500 points",
        **{f"p{v}": f"{v:,} to {v + STEP - 1:,} points" for v in range(LO, HI, STEP)},
        "over_2300": "2,300 points or more"}
# (category, wording, N, mean effort, experts' mean forecast, experts' SD) from Table 4
TREATMENTS = [
    ("piece rate", "As a bonus, you will be paid an extra 4 cents for every 100 points that you score.", 562, 2132, 2057, 120.86),
    ("pay enough or don't pay", "As a bonus, you will be paid an extra 1 cent for every 1,000 points that you score.", 538, 1883, 1657, 262.00),
    ("charity", "As a bonus, the Red Cross charitable fund will be given 1 cent for every 100 points that you score.", 554, 1907, 1894, 202.20),
    ("charity", "As a bonus, the Red Cross charitable fund will be given 10 cents for every 100 points that you score.", 549, 1918, 1997, 196.75),
    ("gift exchange", "In appreciation to you for performing this task, you will be paid a bonus of 40 cents. Your score will "
                      "not affect your payment in any way.", 545, 1602, 1709, 207.12),
    ("discounting", "As a bonus, you will be paid an extra 1 cent for every 100 points that you score. This bonus will be "
                    "paid to your account two weeks from today.", 544, 2004, 1933, 142.02),
    ("discounting", "As a bonus, you will be paid an extra 1 cent for every 100 points that you score. This bonus will be "
                    "paid to your account four weeks from today.", 550, 1970, 1895, 162.54),
    ("gains vs losses", "As a bonus, you will be paid an extra 40 cents if you score at least 2,000 points.", 545, 2136, 1955, 149.90),
    ("gains vs losses", "As a bonus, you will be paid an extra 40 cents. However, you will lose this bonus (it will not be "
                        "placed in your account) unless you score at least 2,000 points.", 532, 2155, 2002, 143.57),
    ("gains vs losses", "As a bonus, you will be paid an extra 80 cents if you score at least 2,000 points.", 532, 2188, 2007, 131.93),
    ("probability weighting", "As a bonus, you will have a 1% chance of being paid an extra $1 for every 100 points that you "
                              "score. One out of every 100 participants who perform this task will be randomly chosen to "
                              "be paid this reward.", 555, 1896, 1967, 253.43),
    ("probability weighting", "As a bonus, you will have a 50% chance of being paid an extra 2 cents for every 100 points "
                              "that you score. One out of two participants who perform this task will be randomly chosen "
                              "to be paid this reward.", 568, 1977, 1941, 179.27),
    ("social comparison", "Your score will not affect your payment in any way. In a previous version of this task, many "
                          "participants were able to score more than 2,000 points.", 526, 1848, 1877, 209.48),
    ("ranking", "Your score will not affect your payment in any way. After you play, we will show you how well you did "
                "relative to other participants who have previously done this task.", 543, 1761, 1850, 234.28),
    ("task significance", "Your score will not affect your payment in any way. We are interested in how fast people choose "
                          "to press digits and we would like you to do your very best. So please try as hard as you can.",
     554, 1740, 1757, 230.15),
]


def bin_of(v: float) -> str:
    if v < LO:
        return "under_1500"
    if v >= HI:
        return "over_2300"
    return f"p{LO + STEP * int((v - LO) // STEP)}"


def fetch(raw_dir: Path) -> None:
    """Transcribed from Table 4 of NBER w22193 (data/raw/effort_forecasts/w22193.pdf was used to check)."""


def normalize(raw_dir: Path) -> Iterator[Question]:
    for i, (cat, wording, n, effort, forecast, sd) in enumerate(TREATMENTS):
        yield Question(
            text=f"{CONTEXT}\n\nAnother group's paragraph said: \"{wording}\"\n\nWhat was that group's average score?",
            primitive="choice", hemisphere="world", kind="forecast", origin="dataset", source=NAME, options=BINS,
            node_hint=NODE, license=LICENSE, source_item_id=f"DellaVigna-Pope 2018 Table 4 #{i + 1}", truth=bin_of(effort),
            meta={"experiment": "effort_forecasts", "category": cat, "n": n, "effort": effort,
                  "expert_forecast": forecast, "expert_sd": sd, "ordered": True})
