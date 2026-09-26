"""UCI Drug Review Dataset (Drugs.com), Gräßer et al. 2018: 215k patient reviews of drugs, each with the
condition the drug was taken for and a 1-10 rating. HF mirror lewtun/drug-reviews (train + test).

Templates (node machine.healthcare.clinical_notes; disjoint samples of the same deduplicated pool):
- "drug_reviews.condition" (Choice): which condition is the review about? 44 distinct conditions; the
  site's overlapping labels (Pain / Chronic Pain / Back Pain, Obesity next to Weight Loss, Emergency
  Contraception and Abnormal Uterine Bleeding next to Birth Control, the anxiety and depression subtypes,
  Migraine Prevention, Headache, Bladder Infection, Bacterial Infection...) are left out, reviews and
  options both, so the options don't overlap. The drug name is not shown. Round-robin over conditions.
- "drug_reviews.satisfied" (Noul): is the reviewer satisfied with the drug? Truth = the reviewer's own
  rating: 8-10 true, 1-3 false, 4-7 left out. Half true, half false. Any condition.
Reviews are HTML-unescaped, whitespace-collapsed, deduplicated by text (a text posted under two
conditions is dropped), 40-1,500 chars. Sexual and self-harm mentions are flagged sensitive.
"""

from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "drug_reviews"
BASE = "https://huggingface.co/api/datasets/lewtun/drug-reviews/parquet/default/{split}/0.parquet"
SPLITS = ("train", "test")
TARGET_CONDITION = env_int("TARGET_DRUG_CONDITION", 2000)
TARGET_SATISFIED = env_int("TARGET_DRUG_SATISFIED", 1500)
LICENSE = "CC-BY-4.0"
CONDITION_TEXT = "Which condition is the patient's drug review `review` about?"
SATISFIED_TEXT = "Is the reviewer satisfied with the drug in `review`?"
SATISFIED = {
    "true": "The reviewer is happy with the drug overall: it works for them and any side effects are worth it",
    "false": "The reviewer is unhappy with the drug: it did not work, or the side effects outweighed the benefit",
}
SENSITIVE = re.compile(
    r"\b(sex\w*|orgasm\w*|erection\w*|libido|intercourse|penis|porn\w*|masturbat\w*|suicid\w*|"
    r"self[- ]harm\w*|kill(ing)? (my|him|her)self|overdos\w*)\b",
    re.I,
)

# option key -> raw dataset label (the dataset truncates labels ending in "r": "Bipolar Disorde").
CONDITIONS = {
    "acne": "Acne",
    "adhd": "ADHD",
    "alcohol_dependence": "Alcohol Dependence",
    "allergic_rhinitis": "Allergic Rhinitis",
    "anxiety": "Anxiety",
    "asthma": "Asthma, Maintenance",
    "benign_prostatic_hyperplasia": "Benign Prostatic Hyperplasia",
    "bipolar_disorder": "Bipolar Disorde",
    "birth_control": "Birth Control",
    "bowel_preparation": "Bowel Preparation",
    "constipation": "Constipation",
    "cough": "Cough",
    "depression": "Depression",
    "endometriosis": "Endometriosis",
    "erectile_dysfunction": "Erectile Dysfunction",
    "fibromyalgia": "ibromyalgia",
    "gerd": "GERD",
    "hepatitis_c": "Hepatitis C",
    "herpes_simplex": "Herpes Simplex",
    "high_blood_pressure": "High Blood Pressure",
    "high_cholesterol": "High Cholesterol",
    "hiv_infection": "HIV Infection",
    "hyperhidrosis": "Hyperhidrosis",
    "insomnia": "Insomnia",
    "irritable_bowel_syndrome": "Irritable Bowel Syndrome",
    "migraine": "Migraine",
    "multiple_sclerosis": "Multiple Sclerosis",
    "muscle_spasm": "Muscle Spasm",
    "narcolepsy": "Narcolepsy",
    "opiate_dependence": "Opiate Dependence",
    "osteoarthritis": "Osteoarthritis",
    "overactive_bladder": "Overactive Bladde",
    "psoriasis": "Psoriasis",
    "restless_legs_syndrome": "Restless Legs Syndrome",
    "rheumatoid_arthritis": "Rheumatoid Arthritis",
    "rosacea": "Rosacea",
    "schizophrenia": "Schizophrenia",
    "seizures": "Seizures",
    "sinusitis": "Sinusitis",
    "smoking_cessation": "Smoking Cessation",
    "type_2_diabetes": "Diabetes, Type 2",
    "underactive_thyroid": "Underactive Thyroid",
    "urinary_tract_infection": "Urinary Tract Infection",
    "vaginal_yeast_infection": "Vaginal Yeast Infection",
}
RAW_TO_KEY = {v: k for k, v in CONDITIONS.items()}
OPTIONS = {k: None for k in CONDITIONS}
OPTIONS["gerd"] = "Gastroesophageal reflux disease (acid reflux)"
OPTIONS["underactive_thyroid"] = "Hypothyroidism"


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = html.unescape(html.unescape(t)).strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        t = t[1:-1]
    return " ".join(t.split())


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_text: dict[str, list] = defaultdict(list)
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for uid, drug, cond, review, rating in df.select(
            "Unnamed: 0", "drugName", "condition", "review", "rating"
        ).iter_rows():
            if not review or not cond or "</span>" in cond:
                continue
            text = _clean(review)
            if 40 <= len(text) <= 1500:
                by_text[text].append((uid, drug, cond, int(rating)))

    items = []  # (uid, text, drug, cond, rating)
    for text, rows in by_text.items():
        if len({c for _, _, c, _ in rows}) != 1:
            continue
        uid, drug, cond, rating = min(rows)
        items.append((uid, text, drug, cond, rating))

    # Condition template: round-robin over the curated conditions in salted-hash order.
    pools: dict[str, list] = defaultdict(list)
    for it in items:
        if it[3] in RAW_TO_KEY:
            pools[RAW_TO_KEY[it[3]]].append(it)
    ordered = {k: hash_order(v, lambda x: x[0], f"drug_reviews.condition|{k}") for k, v in pools.items()}
    assert set(ordered) == set(CONDITIONS), set(CONDITIONS) - set(ordered)
    picked, i = [], 0
    while len(picked) < TARGET_CONDITION:
        for k in sorted(ordered):
            if i < len(ordered[k]) and len(picked) < TARGET_CONDITION:
                picked.append((k, ordered[k][i]))
        i += 1
    used = {it[0] for _, it in picked}

    for key, (uid, text, drug, cond, rating) in sorted(picked, key=lambda x: x[1][0]):
        yield Question(
            text=CONDITION_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"review": text},
            shape="classify",
            node_hint="machine.healthcare.clinical_notes",
            template_id="drug_reviews.condition",
            source_item_id=f"uid:{uid}",
            license=LICENSE,
            truth=key,
            meta={"condition_raw": cond, "drug": drug, "rating": rating,
                  **({"flags": ["sensitive"]} if SENSITIVE.search(text) else {})},
        )

    # Satisfied template: disjoint from the condition sample, half high (8-10) and half low (1-3).
    rest = [it for it in items if it[0] not in used]
    hi = hash_order([it for it in rest if it[4] >= 8], lambda x: x[0], "drug_reviews.satisfied|hi")
    lo = hash_order([it for it in rest if it[4] <= 3], lambda x: x[0], "drug_reviews.satisfied|lo")
    half = TARGET_SATISFIED // 2
    for uid, text, drug, cond, rating in sorted(hi[:half] + lo[: TARGET_SATISFIED - half]):
        yield Question(
            text=SATISFIED_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SATISFIED,
            state={"review": text},
            shape="detect",
            node_hint="machine.healthcare.clinical_notes",
            template_id="drug_reviews.satisfied",
            source_item_id=f"uid:{uid}",
            license=LICENSE,
            truth=rating >= 8,
            meta={"rating": rating, "condition_raw": cond, "drug": drug,
                  **({"flags": ["sensitive"]} if SENSITIVE.search(text) else {})},
        )
