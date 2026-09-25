"""MATH (Hendrycks et al. 2021): 12,500 competition problems (AMC 10/12, AIME and more, via AoPS), each
tagged by its source with one of seven subjects and a difficulty level 1-5. Public copy:
EleutherAI/hendrycks_math (the original hendrycks/competition_math repo was taken down).

Two routing templates for a model router (node machine.ai_systems.model_routing):
- "math.subject" (Choice): which subject specialist should get `problem`. Truth = the dataset subject.
  Balanced across the 7 subjects.
- "math.hardest" (Noul): is `problem` among the hardest problems of its (given) subject? MATH levels are
  relative to the subject, so the subject is in the state. Truth = Level 5 (true) against Levels 1-2 (false); Levels 3-4 are left out so the label is a clear contrast, not a one-level guess.
Problems over 1,500 characters are dropped; the two templates use disjoint problems.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "math_routing"
BASE = "https://huggingface.co/api/datasets/EleutherAI/hendrycks_math/parquet/"
TARGET_SUBJECT = env_int("TARGET_MATH_SUBJECT", 2500)
TARGET_HARD = env_int("TARGET_MATH_HARD", 2000)
LICENSE = "MIT"
SUBJECT_TEXT = "Which area of competition mathematics is `problem` from?"
SUBJECTS = {
    "prealgebra": "Arithmetic, fractions, decimals, percents, ratios, simple equations, basic counting, "
    "perimeter and area",
    "algebra": "Linear and quadratic equations and inequalities, systems, functions and their graphs, "
    "exponents and radicals, arithmetic and geometric sequences",
    "intermediate_algebra": "Polynomials and their roots, advanced inequalities, complex numbers, "
    "logarithms, conic sections, functional equations, series",
    "counting_and_probability": "Counting arrangements and selections, combinations, probability, "
    "expected value, Pascal's triangle",
    "number_theory": "Divisibility, primes, remainders and modular arithmetic, digits and number bases, "
    "gcd and lcm",
    "geometry": "Triangles, circles, polygons, angles, areas and volumes, coordinate and solid geometry",
    "precalculus": "Trigonometry, vectors, matrices and determinants, complex numbers in polar form, "
    "parametric and polar curves",
}
HARD_TEXT = "Is `problem` among the hardest `subject` problems in high-school competition mathematics?"
HARD = {
    "true": "One of the hardest problems of its subject (Level 5 of 5): most well-prepared contest students "
    "would struggle with it",
    "false": "An easy problem of its subject (Level 1 or 2 of 5): a routine exercise most prepared students solve",
}
SUBJECT_NAMES = {
    "prealgebra": "prealgebra", "algebra": "algebra", "intermediate_algebra": "intermediate algebra",
    "counting_and_probability": "counting and probability", "number_theory": "number theory",
    "geometry": "geometry", "precalculus": "precalculus",
}


def fetch(raw_dir: Path) -> None:
    for subj in SUBJECTS:
        for split in ("train", "test"):
            out = raw_dir / f"{subj}_{split}.parquet"
            if out.exists():
                continue
            r = httpx.get(f"{BASE}{subj}/{split}/0.parquet", follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows: list[tuple[str, str, str, int]] = []  # (sid, subject, problem, level)
    seen: set[str] = set()
    for subj in SUBJECTS:
        for split in ("train", "test"):
            df = pl.read_parquet(raw_dir / f"{subj}_{split}.parquet").with_row_index("row")
            for row, problem, level in df.select("row", "problem", "level").iter_rows():
                p = problem.strip()
                if not p or len(p) > 1500 or p in seen or not level.startswith("Level ") or level[-1] not in "12345":
                    continue
                seen.add(p)
                rows.append((f"{subj}:{split}:{row}", subj, p, int(level[-1])))

    # math.subject: equal share per subject.
    per = TARGET_SUBJECT // len(SUBJECTS)
    subject_pick = []
    for i, subj in enumerate(SUBJECTS):
        k = per + (1 if i < TARGET_SUBJECT - per * len(SUBJECTS) else 0)
        pool = [r for r in rows if r[1] == subj]
        subject_pick += hash_order(pool, lambda x: x[0], f"math.subject.{subj}")[:k]
    used = {r[0] for r in subject_pick}

    # math.hardest: Level 5 vs Levels 1-2, disjoint from math.subject.
    hard_pick = []
    for label, levels, k in ((True, {5}, TARGET_HARD // 2), (False, {1, 2}, TARGET_HARD - TARGET_HARD // 2)):
        pool = [r for r in rows if r[3] in levels and r[0] not in used]
        hard_pick += [(label, r) for r in hash_order(pool, lambda x: x[0], f"math.hardest.{label}")[:k]]

    for sid, subj, p, level in sorted(subject_pick):
        yield Question(
            text=SUBJECT_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SUBJECTS,
            state={"problem": p},
            shape="route",
            node_hint="machine.ai_systems.model_routing",
            template_id="math.subject",
            source_item_id=sid,
            license=LICENSE,
            truth=subj,
            meta={"level": level},
        )
    for label, (sid, subj, p, level) in sorted(hard_pick, key=lambda x: x[1][0]):
        yield Question(
            text=HARD_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=HARD,
            state={"subject": SUBJECT_NAMES[subj], "problem": p},
            shape="route",
            node_hint="machine.ai_systems.model_routing",
            template_id="math.hardest",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"level": level, "subject": subj},
        )
