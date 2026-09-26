"""ASAP-AES essay set 7 (Hewlett Foundation Automated Student Assessment Prize, 2012): 1,569 grade-7
narrative essays on "patience", each scored by two trained raters on four traits (0-3). Public, ungated
HF mirror llm-aes/asap-7-original (the Kaggle original needs a login).

Three Score templates (node machine.education.essay_feedback), one per trait, rubric levels rewritten
as concrete situations: "asap7.ideas", "asap7.organization", "asap7.conventions". An essay enters a
trait template only when both raters gave the same score on that trait; truth = that score (level
index). The Style trait is left out (it overlaps Ideas and Conventions). Essays over 1,500 chars are
left out rather than cut. The dataset replaced names and some capitalised words with placeholders
(@PERSON1, @CAPS1); the state says so, so they are not graded as errors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "asap_essays"
URL = "https://huggingface.co/api/datasets/llm-aes/asap-7-original/parquet/default/train/0.parquet"
PER_TRAIT = env_int("TARGET_ASAP7_PER_TRAIT", 700)
LICENSE = "ASAP-AES competition data (Hewlett Foundation / Kaggle, research use); HF mirror states no license"
PROMPT = (
    "Write about patience. Being patient means that you are understanding and tolerant. A patient person "
    "experience difficulties without complaining. Do only one of the following: write a story about a time "
    "when you were patient OR write a story about a time when someone you know was patient OR write a story "
    "in your own way about patience."
)
NOTE = "Written by a seventh grader. Names and some capitalized words were replaced with placeholders such as @PERSON1 or @CAPS1 for anonymity."

TRAITS = {
    "ideas": (
        1,
        "How well does the essay `essay` develop a story about patience?",
        [
            "The essay does not tell a story about patience, or says almost nothing",
            "The essay touches on patience, but the story is thin and uses only a few general details",
            "The essay tells a story about patience using a mix of specific and general details",
            "The essay tells a focused story about patience, developed throughout with specific, relevant details",
        ],
    ),
    "organization": (
        2,
        "How well is the essay `essay` organized?",
        [
            "Sentences and events are jumbled, with no order a reader can follow",
            "Events are roughly in order, but the links between them are weak or missing and parts feel disjointed",
            "Events follow a logical order from beginning to end, with a few abrupt jumps",
            "The story moves clearly from beginning to end, with transitions linking each event",
        ],
    ),
    "conventions": (
        4,
        "How well does the essay `essay` follow the conventions of written English (spelling, grammar, capitalization, punctuation)?",
        [
            "Errors are so frequent that the essay is hard to read",
            "Frequent spelling, grammar, capitalization or punctuation errors distract the reader",
            "There are some errors, but they rarely get in the way of reading",
            "Spelling, grammar, capitalization and punctuation are consistently correct for a seventh grader",
        ],
    ),
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet")
    rows = [r for r in df.iter_rows(named=True) if r["essay"] and len(" ".join(r["essay"].split())) <= 1500]
    for trait, (t, text, levels) in TRAITS.items():
        agreed = [r for r in rows if r[f"rater1_trait{t}"] is not None and r[f"rater1_trait{t}"] == r[f"rater2_trait{t}"]]
        for r in sorted(hash_order(agreed, lambda r: r["essay_id"], f"asap7.{trait}")[:PER_TRAIT], key=lambda r: r["essay_id"]):
            yield Question(
                text=text,
                primitive="score",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=levels,
                state={"assignment": PROMPT, "note": NOTE, "essay": " ".join(r["essay"].split())},
                shape="score",
                node_hint="machine.education.essay_feedback",
                template_id=f"asap7.{trait}",
                source_item_id=f"essay:{r['essay_id']}",
                license=LICENSE,
                truth=int(r[f"rater1_trait{t}"]),
                meta={"trait": trait, "rater1": int(r[f"rater1_trait{t}"]), "rater2": int(r[f"rater2_trait{t}"]),
                      "domain1_score": r["domain1_score"]},
            )
