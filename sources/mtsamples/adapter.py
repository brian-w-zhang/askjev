"""MTSamples (mtsamples.com, Kaggle scrape by Tara Boyle; HF mirror harishnair04/mtsamples): 4,999
de-identified sample medical transcriptions, each filed under a medical specialty or a document category.

The site files one transcription under several categories (a colonoscopy is both "Gastroenterology" and
"Surgery"), and some categories are document types or settings rather than specialties. So the
transcriptions are deduplicated by text and the category set of each is split in two:
- specialties (Cardiovascular / Pulmonary, Orthopedic, ...): template "mtsamples.specialty" (Choice, 30
  specialties) uses transcriptions filed under exactly one specialty. Truth = that specialty.
- document types (Surgery = operative report, Consult - History and Phy., SOAP / Chart / Progress Notes,
  Discharge Summary, Emergency Room Reports, Office Notes, Letters, IME-QME-Work Comp): template
  "mtsamples.doc_type" (Choice, 8 types) uses transcriptions filed under exactly one of them.
Autopsy reports are flagged sensitive (graphic). General Medicine and Pain Management overlap everything, so they are ignored for both. Transcriptions
filed under 2+ specialties (or 2+ document types) are left out of that template: the label is ambiguous.
Text cleanup: the scrape's ":," artifacts are removed and whitespace collapsed; cut to 1,500 chars at a
word boundary. Round-robin over labels in salted-hash order, at most 400 per label (operative reports
would otherwise be 59% of doc_type).
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

NAME = "mtsamples"
URL = "https://huggingface.co/api/datasets/harishnair04/mtsamples/parquet/default/train/0.parquet"
TARGET_SPECIALTY = env_int("TARGET_MTSAMPLES_SPECIALTY", 2500)
TARGET_DOCTYPE = env_int("TARGET_MTSAMPLES_DOCTYPE", 2000)
PER_LABEL = 400  # no label above ~25% of a template
LICENSE = "CC0-1.0 (Kaggle scrape of mtsamples.com; HF mirror lists Apache-2.0)"
SPECIALTY_TEXT = "Which medical specialty does the transcription `transcription` belong to?"
DOCTYPE_TEXT = "What kind of clinical document is `transcription`?"

SPECIALTIES = {
    "Allergy / Immunology": "allergy_immunology",
    "Autopsy": "autopsy",
    "Bariatrics": "bariatrics",
    "Cardiovascular / Pulmonary": "cardiovascular_pulmonary",
    "Chiropractic": "chiropractic",
    "Cosmetic / Plastic Surgery": "cosmetic_plastic_surgery",
    "Dentistry": "dentistry",
    "Dermatology": "dermatology",
    "Diets and Nutritions": "diet_nutrition",
    "ENT - Otolaryngology": "ent_otolaryngology",
    "Endocrinology": "endocrinology",
    "Gastroenterology": "gastroenterology",
    "Hematology - Oncology": "hematology_oncology",
    "Hospice - Palliative Care": "hospice_palliative_care",
    "Lab Medicine - Pathology": "lab_medicine_pathology",
    "Nephrology": "nephrology",
    "Neurology": "neurology",
    "Neurosurgery": "neurosurgery",
    "Obstetrics / Gynecology": "obstetrics_gynecology",
    "Ophthalmology": "ophthalmology",
    "Orthopedic": "orthopedic",
    "Pediatrics - Neonatal": "pediatrics_neonatal",
    "Physical Medicine - Rehab": "physical_medicine_rehab",
    "Podiatry": "podiatry",
    "Psychiatry / Psychology": "psychiatry_psychology",
    "Radiology": "radiology",
    "Rheumatology": "rheumatology",
    "Sleep Medicine": "sleep_medicine",
    "Speech - Language": "speech_language",
    "Urology": "urology",
}
SPECIALTY_OPTIONS = {v: k for k, v in SPECIALTIES.items()}

DOCTYPES = {
    "Surgery": ("operative_report", "An operative or procedure report"),
    "Consult - History and Phy.": ("consult_history_physical", "A consultation or history and physical"),
    "SOAP / Chart / Progress Notes": ("progress_note", "A progress note or SOAP chart note"),
    "Discharge Summary": ("discharge_summary", "A hospital discharge summary"),
    "Emergency Room Reports": ("emergency_room_report", "An emergency room report"),
    "Office Notes": ("office_note", "A routine office visit note or normal-exam template"),
    "Letters": ("letter", "A letter to another clinician, patient or third party"),
    "IME-QME-Work Comp etc.": ("independent_medical_exam", "An independent medical or workers' compensation evaluation"),
}
DOCTYPE_OPTIONS = {k: d for k, d in DOCTYPES.values()}
IGNORED = {"General Medicine", "Pain Management"}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = re.sub(r"([:.])\s*,", r"\1 ", t)
    t = re.sub(r",(?=[A-Z][A-Z ,/&()-]{2,}:)", " ", t)  # ",POSTOPERATIVE DIAGNOSIS:" section joins
    return " ".join(t.split())


def _cut(t: str, n: int = 1500) -> str:
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0] + " ..."


def _round_robin(pools: dict[str, list], k: int, salt: str, per_label: int) -> list:
    ordered = {lab: hash_order(items, lambda x: x[0], f"{salt}|{lab}")[:per_label] for lab, items in pools.items()}
    out, i = [], 0
    while len(out) < k and any(i < len(v) for v in ordered.values()):
        for lab in sorted(ordered):
            if i < len(ordered[lab]) and len(out) < k:
                out.append((lab, *ordered[lab][i]))
        i += 1
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").filter(pl.col("transcription").is_not_null())
    cats: dict[str, set[str]] = defaultdict(set)
    first_row: dict[str, int] = {}
    for row, spec, tr in df.select("Unnamed: 0", "medical_specialty", "transcription").iter_rows():
        text = _clean(tr)
        if len(text) < 200:
            continue
        cats[text].add(spec.strip())
        first_row.setdefault(text, row)

    spec_pool: dict[str, list] = defaultdict(list)
    type_pool: dict[str, list] = defaultdict(list)
    for text, cs in cats.items():
        cs = cs - IGNORED
        specs = [c for c in cs if c in SPECIALTIES]
        types = [c for c in cs if c in DOCTYPES]
        assert all(c in SPECIALTIES or c in DOCTYPES for c in cs), cs
        if len(specs) == 1:
            spec_pool[SPECIALTIES[specs[0]]].append((first_row[text], text, sorted(cs)))
        if len(types) == 1:
            type_pool[DOCTYPES[types[0]][0]].append((first_row[text], text, sorted(cs)))

    for tid, text_q, options, pool, k, node in (
        ("mtsamples.specialty", SPECIALTY_TEXT, SPECIALTY_OPTIONS, spec_pool, TARGET_SPECIALTY, "machine.healthcare.clinical_notes"),
        ("mtsamples.doc_type", DOCTYPE_TEXT, DOCTYPE_OPTIONS, type_pool, TARGET_DOCTYPE, "machine.healthcare.clinical_notes"),
    ):
        for lab, row, text, cs in sorted(_round_robin(pool, k, tid, PER_LABEL), key=lambda x: x[1]):
            yield Question(
                text=text_q,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=options,
                state={"transcription": _cut(text)},
                shape="classify",
                node_hint=node,
                template_id=tid,
                source_item_id=f"row:{row}",
                license=LICENSE,
                truth=lab,
                meta={"categories_raw": cs, **({"flags": ["sensitive"]} if "Autopsy" in cs else {})},
            )
