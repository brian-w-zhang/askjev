"""Wellbeing instruments, item by item, so Jev can answer "how are you doing?" the way surveys ask people:
the Satisfaction with Life Scale (Diener et al. 1985), WHO-5 (WHO 1998), the three-item UCLA loneliness scale
(Hughes et al. 2004), the four-item Perceived Stress Scale (Cohen et al. 1983) and the Cantril ladder (Cantril 1965).
Each item also carries a "most people" wording for the human frame. No norms: published norms are means, not item
distributions."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "wellbeing"
NODE = "self.mind.happiness_wellbeing"
LICENSE = "Public instruments, free for research use (SWLS, WHO-5, UCLA-3, PSS-4, Cantril ladder)"

AGREE7 = ["Strongly disagree", "Disagree", "Slightly disagree", "Neither agree nor disagree", "Slightly agree", "Agree", "Strongly agree"]
SWLS = [
    "In most ways my life is close to my ideal.",
    "The conditions of my life are excellent.",
    "I am satisfied with my life.",
    "So far I have gotten the important things I want in life.",
    "If I could live my life over, I would change almost nothing.",
]
TIME6 = ["At no time", "Some of the time", "Less than half of the time", "More than half of the time", "Most of the time", "All of the time"]
WHO5 = [
    "I have felt cheerful and in good spirits.",
    "I have felt calm and relaxed.",
    "I have felt active and vigorous.",
    "I woke up feeling fresh and rested.",
    "My daily life has been filled with things that interest me.",
]
OFTEN3 = ["Hardly ever", "Some of the time", "Often"]
UCLA3 = [  # (you, most people)
    ("How often do you feel that you lack companionship?", "How often do most people feel that they lack companionship?"),
    ("How often do you feel left out?", "How often do most people feel left out?"),
    ("How often do you feel isolated from others?", "How often do most people feel isolated from others?"),
]
OFTEN5 = ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"]
PSS4 = [  # (you, most people, reverse-scored)
    ("In the last month, how often have you felt that you were unable to control the important things in your life?",
     "In the last month, how often have most people felt that they were unable to control the important things in their life?", False),
    ("In the last month, how often have you felt confident about your ability to handle your personal problems?",
     "In the last month, how often have most people felt confident about their ability to handle their personal problems?", True),
    ("In the last month, how often have you felt that things were going your way?",
     "In the last month, how often have most people felt that things were going their way?", True),
    ("In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
     "In the last month, how often have most people felt difficulties were piling up so high that they could not overcome them?", False),
]
LADDER = {f"step_{i}": (f"Step {i}: the worst possible life for you" if i == 0 else f"Step {i}: the best possible life for you" if i == 10 else f"Step {i}") for i in range(11)}
LADDER_Q = ("Imagine a ladder with steps numbered from 0 at the bottom to 10 at the top. The top of the ladder is the best "
            "possible life for you and the bottom is the worst possible life for you. Which step do you feel you stand on "
            "right now?")
LADDER_H = ("Imagine a ladder with steps numbered from 0 at the bottom to 10 at the top, where the top is the best possible life "
            "for a person and the bottom is the worst. Which step would most people say they stand on right now?")


def fetch(raw_dir: Path) -> None:
    """The items are transcribed above from the published instruments; nothing to download."""


def _q(text: str, human: str, options, instrument: str, item: int, **meta) -> Question:
    return Question(text=text, human_text=human, primitive="choice" if isinstance(options, dict) else "score",
                    hemisphere="self", kind="personality", origin="dataset", source=NAME, options=options,
                    node_hint=NODE, source_item_id=f"{instrument} item {item}", license=LICENSE,
                    meta={"instrument": instrument, "item": item, **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    for i, s in enumerate(SWLS, 1):
        yield _q(f'How much do you agree with this statement about your life: "{s}"',
                 f'How much would most people agree with this statement about their own life: "{s}"', AGREE7, "SWLS", i,
                 scale="1-7 agreement, higher = more satisfied")
    for i, s in enumerate(WHO5, 1):
        yield _q(f'Over the last two weeks, how often has this been true for you: "{s}"',
                 f'Over the last two weeks, how often would most people say this has been true for them: "{s}"', TIME6, "WHO-5", i,
                 scale="0-5 frequency, higher = better wellbeing")
    for i, (you, most) in enumerate(UCLA3, 1):
        yield _q(you, most, OFTEN3, "UCLA-3", i, scale="1-3 frequency, higher = lonelier")
    for i, (you, most, rev) in enumerate(PSS4, 1):
        yield _q(you, most, OFTEN5, "PSS-4", i, reverse=rev, scale="0-4 frequency, higher = more stressed (reverse items flipped)")
    yield _q(LADDER_Q, LADDER_H, LADDER, "Cantril ladder", 1, scale="0-10 steps, ordered options")
