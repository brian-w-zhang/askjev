"""arXiv abstracts (gfissore/arxiv-abstracts-2021, the arXiv metadata snapshot, CC0) with their categories.

Template "arxiv.field": Choice "Which field of arXiv is the paper with `title` and `abstract` from?" over
10 top-level areas, truth = the area of the paper's primary (first-listed) category. "physics" is every
physics archive except astro-ph and cond-mat, which get their own options; math-ph primaries are left
out (they sit between math and physics). Only papers whose categories all fall in one area are sampled
(an eess.IV paper cross-listed to cs.CV has no single right answer). Balanced across the 10 areas.

Template "arxiv.is_ml": Noul "Is the paper with `title` and `abstract` about machine learning?".
Positives: primary category cs.LG or stat.ML. Negatives: papers with no ML-adjacent category anywhere in
their listing (cs.LG, stat.ML, cs.AI, cs.CV, cs.CL, cs.NE, cs.IR, cs.RO, cs.MA, eess.IV, eess.AS) so an
unlabelled ML paper is not counted as false. Half positive; the negatives are spread over the 10 areas.

Only one of the snapshot's five parquet shards is downloaded (shard 3: 363k papers, ids 1912.x-2112.x, i.e. Dec 2019 -
Dec 2021), which has every area in volume, including econ and eess.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "arxiv_screen"
SHARD = 3
URL = f"https://huggingface.co/api/datasets/gfissore/arxiv-abstracts-2021/parquet/default/train/{SHARD}.parquet"
TARGET = env_int("TARGET_ARXIV_SCREEN", 2000)
TARGET_ML = env_int("TARGET_ARXIV_SCREEN_ML", 1000)
SALT = "arxiv_screen.v1"
LICENSE = "CC0-1.0"
FIELD_TEXT = "Which field of arXiv is the paper with `title` and `abstract` from?"
ML_TEXT = "Is the paper with `title` and `abstract` about machine learning?"

FIELDS = {
    "computer_science": "Computer science (cs)",
    "mathematics": "Mathematics (math)",
    "physics": "Physics other than astrophysics and condensed matter: high-energy, nuclear, quantum, "
    "gravitation, optics, fluids, plasma, applied and general physics",
    "astrophysics": "Astrophysics (astro-ph)",
    "condensed_matter": "Condensed matter physics (cond-mat)",
    "quantitative_biology": "Quantitative biology (q-bio)",
    "quantitative_finance": "Quantitative finance (q-fin)",
    "statistics": "Statistics (stat)",
    "economics": "Economics (econ)",
    "electrical_engineering_and_systems_science": "Electrical engineering and systems science (eess)",
}
PHYSICS_ARCHIVES = {"physics", "hep-th", "hep-ph", "hep-ex", "hep-lat", "gr-qc", "nucl-th", "nucl-ex",
                    "quant-ph", "nlin"}
ML_CATS = {"cs.LG", "stat.ML"}
ML_ADJACENT = ML_CATS | {"cs.AI", "cs.CV", "cs.CL", "cs.NE", "cs.IR", "cs.RO", "cs.MA", "eess.IV", "eess.AS"}
ML_OPTIONS = {
    "true": "The paper's main subject is machine learning: learning methods, models, training, or their theory",
    "false": "The paper's main subject is something else, even if it mentions data or computation",
}


def _field(cat: str) -> str | None:
    archive = cat.split(".")[0]
    if archive == "math" and cat == "math.MP":
        return None
    return {
        "cs": "computer_science", "math": "mathematics", "astro-ph": "astrophysics",
        "cond-mat": "condensed_matter", "q-bio": "quantitative_biology", "q-fin": "quantitative_finance",
        "stat": "statistics", "econ": "economics", "eess": "electrical_engineering_and_systems_science",
    }.get(archive) or ("physics" if archive in PHYSICS_ARCHIVES else None)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / f"train_{SHARD}.parquet"
    if out.exists():
        return
    tmp = out.with_suffix(".part")
    with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_bytes(1 << 20):
                fh.write(chunk)
    tmp.rename(out)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _question(it: dict, text: str, prim: str, options: dict, shape: str, tid: str, truth) -> Question:
    return Question(
        text=text,
        primitive=prim,
        hemisphere="machine",
        origin="dataset",
        source=NAME,
        options=options,
        state={"title": it["title"], "abstract": it["abstract"]},
        shape=shape,
        node_hint="machine.research.paper_screening",
        template_id=tid,
        source_item_id=it["id"],
        license=LICENSE,
        truth=truth,
        meta={"categories": it["cats"], "primary": it["cats"][0]},
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / f"train_{SHARD}.parquet", columns=["id", "title", "abstract", "categories"])
    by_field: dict[str, list[dict]] = defaultdict(list)
    ml_pos: list[dict] = []
    ml_neg: dict[str, list[dict]] = defaultdict(list)
    for pid, title, abstract, cats in df.iter_rows():
        cats = " ".join(cats or []).split()
        if not cats:
            continue
        field = _field(cats[0])
        title, abstract = _clean(title), _clean(abstract)
        if field is None or not title or not (200 <= len(abstract) <= 1500):
            continue
        if "withdrawn" in abstract.lower()[:200]:
            continue
        it = {"id": pid, "title": title, "abstract": abstract, "cats": cats, "field": field}
        if all(_field(c) == field for c in cats):
            by_field[field].append(it)
        if cats[0] in ML_CATS:
            ml_pos.append(it)
        elif not ML_ADJACENT & set(cats):
            ml_neg[field].append(it)

    # arxiv.field: equal share per field, salted hash order within each.
    keys = list(FIELDS)
    per = [TARGET // len(keys) + (1 if j < TARGET % len(keys) else 0) for j in range(len(keys))]
    for f, k in zip(keys, per):
        for it in hash_order(by_field[f], lambda x: x["id"], f"{SALT}|field|{f}")[:k]:
            yield _question(it, FIELD_TEXT, "choice", FIELDS, "classify", "arxiv.field", f)

    # arxiv.is_ml: half positives, half negatives spread evenly over the fields.
    n_pos = TARGET_ML // 2
    n_neg = TARGET_ML - n_pos
    for it in hash_order(ml_pos, lambda x: x["id"], f"{SALT}|ml|pos")[:n_pos]:
        yield _question(it, ML_TEXT, "noul", ML_OPTIONS, "detect", "arxiv.is_ml", True)
    per = [n_neg // len(keys) + (1 if j < n_neg % len(keys) else 0) for j in range(len(keys))]
    for f, k in zip(keys, per):
        for it in hash_order(ml_neg[f], lambda x: x["id"], f"{SALT}|ml|neg|{f}")[:k]:
            yield _question(it, ML_TEXT, "noul", ML_OPTIONS, "detect", "arxiv.is_ml", False)
