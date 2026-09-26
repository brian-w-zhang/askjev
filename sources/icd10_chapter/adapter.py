"""ICD-10-CM 2026 code descriptions (CMS / CDC NCHS, FY2026 tabular order files): 74k billable diagnosis
codes with their official long descriptions.

Template "icd10.chapter" (Choice, node machine.healthcare.intake_admin): which ICD-10-CM chapter does
`diagnosis` belong to? The code itself is not shown. Truth = the chapter whose code range contains the
code (ranges from the ICD-10-CM tabular list). Chapter 22 (U codes, special purposes) is left out.
Sampling: within a chapter, one code per 3-character category first (salted-hash order), then a second
code per category, and so on, so near-duplicate siblings (7th-character encounter variants) are spread
out; round-robin over the 21 chapters.
"""

from __future__ import annotations

import io
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "icd10_chapter"
URL = "https://www.cms.gov/files/zip/2026-code-descriptions-tabular-order.zip"
MEMBER = "icd10cm_codes_2026.txt"
TARGET = env_int("TARGET_ICD10_CHAPTER", 2000)
LICENSE = "Public domain (US government work, CDC NCHS / CMS)"
TEXT = "Which ICD-10-CM chapter does the diagnosis `diagnosis` belong to?"

# (first code, last code, key, official chapter title); ranges compare on the 3-character category.
CHAPTERS = [
    ("A00", "B99", "infectious_parasitic", "Certain infectious and parasitic diseases"),
    ("C00", "D49", "neoplasms", "Neoplasms"),
    ("D50", "D89", "blood_immune", "Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism"),
    ("E00", "E89", "endocrine_metabolic", "Endocrine, nutritional and metabolic diseases"),
    ("F01", "F99", "mental_behavioral", "Mental, behavioral and neurodevelopmental disorders"),
    ("G00", "G99", "nervous_system", "Diseases of the nervous system"),
    ("H00", "H59", "eye_adnexa", "Diseases of the eye and adnexa"),
    ("H60", "H95", "ear_mastoid", "Diseases of the ear and mastoid process"),
    ("I00", "I99", "circulatory", "Diseases of the circulatory system"),
    ("J00", "J99", "respiratory", "Diseases of the respiratory system"),
    ("K00", "K95", "digestive", "Diseases of the digestive system"),
    ("L00", "L99", "skin_subcutaneous", "Diseases of the skin and subcutaneous tissue"),
    ("M00", "M99", "musculoskeletal", "Diseases of the musculoskeletal system and connective tissue"),
    ("N00", "N99", "genitourinary", "Diseases of the genitourinary system"),
    ("O00", "O9A", "pregnancy_childbirth", "Pregnancy, childbirth and the puerperium"),
    ("P00", "P96", "perinatal", "Certain conditions originating in the perinatal period"),
    ("Q00", "Q99", "congenital", "Congenital malformations, deformations and chromosomal abnormalities"),
    ("R00", "R99", "symptoms_signs_findings", "Symptoms, signs and abnormal clinical and laboratory findings, not elsewhere classified"),
    ("S00", "T88", "injury_poisoning", "Injury, poisoning and certain other consequences of external causes"),
    ("V00", "Y99", "external_causes", "External causes of morbidity"),
    ("Z00", "Z99", "health_status_factors", "Factors influencing health status and contact with health services"),
]
OPTIONS = {k: title for _, _, k, title in CHAPTERS}


def chapter(code: str) -> str | None:
    cat = code[:3]
    for lo, hi, key, _ in CHAPTERS:
        if lo <= cat <= hi:
            return key
    return None


def fetch(raw_dir: Path) -> None:
    out = raw_dir / MEMBER
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        name = next(n for n in z.namelist() if n.endswith(MEMBER))
        out.write_bytes(z.read(name))


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_ch: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    seen: set[str] = set()
    for line in (raw_dir / MEMBER).read_text(encoding="utf-8").splitlines():
        code, _, desc = line.partition(" ")
        code, desc = code.strip(), " ".join(desc.split())
        ch = chapter(code)
        if not code or not desc or ch is None or desc.lower() in seen:
            continue
        seen.add(desc.lower())
        by_ch[ch][code[:3]].append((code, desc))
    assert set(by_ch) == set(OPTIONS), set(OPTIONS) - set(by_ch)

    # Per chapter: categories in hash order, codes within a category in hash order, interleaved by rank.
    ordered: dict[str, list[tuple[str, str]]] = {}
    for ch, cats in by_ch.items():
        cat_lists = [hash_order(v, lambda x: x[0], f"icd10|{c}") for c, v in cats.items()]
        cat_lists = hash_order(cat_lists, lambda v: v[0][0][:3], f"icd10|{ch}")
        seq, r = [], 0
        while any(r < len(v) for v in cat_lists):
            seq += [v[r] for v in cat_lists if r < len(v)]
            r += 1
        ordered[ch] = seq

    picked, i = [], 0
    while len(picked) < TARGET and any(i < len(v) for v in ordered.values()):
        for ch in sorted(ordered):
            if i < len(ordered[ch]) and len(picked) < TARGET:
                picked.append((ch, *ordered[ch][i]))
        i += 1

    for ch, code, desc in sorted(picked, key=lambda x: x[1]):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"diagnosis": desc},
            shape="classify",
            node_hint="machine.healthcare.intake_admin",
            template_id="icd10.chapter",
            source_item_id=f"icd10cm2026:{code}",
            license=LICENSE,
            truth=ch,
            meta={"code": code[:3] + ("." + code[3:] if len(code) > 3 else "")},
        )
