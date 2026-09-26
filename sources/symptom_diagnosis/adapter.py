"""Symptom to Diagnosis (Gretel, HF gretelai/symptom_to_diagnosis; built from the Kaggle "Symptom2Disease"
set): 1,065 first-person symptom descriptions, each labelled with one of 22 diagnoses.

Template "symptom_diagnosis.diagnosis" (Choice, node machine.healthcare.intake_admin): which diagnosis
best explains the patient's description? Truth = the dataset diagnosis. Train + test, exact-text dedup,
all rows (the dataset is already balanced, ~48 per diagnosis).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question

NAME = "symptom_diagnosis"
BASE = "https://huggingface.co/api/datasets/gretelai/symptom_to_diagnosis/parquet/default/{split}/0.parquet"
SPLITS = ("train", "test")
LICENSE = "Apache-2.0"
TEXT = "Which diagnosis best explains the symptoms the patient describes in `patient_message`?"
DIAGNOSES = {
    "allergy": None,
    "arthritis": None,
    "bronchial_asthma": None,
    "cervical_spondylosis": None,
    "chicken_pox": None,
    "common_cold": None,
    "dengue": None,
    "diabetes": None,
    "drug_reaction": None,
    "fungal_infection": None,
    "gastroesophageal_reflux_disease": None,
    "hypertension": None,
    "impetigo": None,
    "jaundice": None,
    "malaria": None,
    "migraine": None,
    "peptic_ulcer_disease": None,
    "pneumonia": None,
    "psoriasis": None,
    "typhoid": None,
    "urinary_tract_infection": None,
    "varicose_veins": None,
}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, label, text in df.select("row", "output_text", "input_text").iter_rows():
            text = " ".join(text.split())
            key = label.strip().replace(" ", "_")
            assert key in DIAGNOSES, key
            if not text or text.lower() in seen:
                continue
            seen.add(text.lower())
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=DIAGNOSES,
                state={"patient_message": text[:1500]},
                shape="classify",
                node_hint="machine.healthcare.intake_admin",
                template_id="symptom_diagnosis.diagnosis",
                source_item_id=f"{split}:{row}",
                license=LICENSE,
                truth=key,
                meta={"label_raw": label},
            )
