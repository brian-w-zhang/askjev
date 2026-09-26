"""HCV data (UCI 571; Lichtinghagen, Klawonn & Hoffmann, Hannover Medical School): 615 blood panels (age,
sex and 10 laboratory values) from blood donors and from patients with hepatitis C, fibrosis or cirrhosis.

Template "hcv_labs.liver_disease" (Noul, node machine.healthcare.lab_results): does the panel indicate
liver disease? Truth = the dataset category: Hepatitis / Fibrosis / Cirrhosis (true) vs Blood Donor
(false); the 7 "suspect blood donor" rows are left out. All 75 disease panels plus 150 donor panels
(salted-hash order), so one third are true. Values are shown with their units as a one-line report;
missing analytes are omitted. No reference ranges are added (the dataset has none).
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "hcv_labs"
URL = "https://archive.ics.uci.edu/static/public/571/hcv+data.zip"
N_DONORS = env_int("HCV_LABS_DONORS", 150)
LICENSE = "CC-BY-4.0"
TEXT = "Does the blood panel `labs` indicate liver disease?"
CRITERIA = {
    "true": "The values point to liver disease such as hepatitis, fibrosis or cirrhosis",
    "false": "The values are consistent with a healthy adult",
}
ANALYTES = [  # column, display name, unit
    ("ALB", "Albumin", "g/L"),
    ("ALP", "Alkaline phosphatase (ALP)", "U/L"),
    ("ALT", "ALT", "U/L"),
    ("AST", "AST", "U/L"),
    ("BIL", "Bilirubin", "µmol/L"),
    ("CHE", "Cholinesterase", "kU/L"),
    ("CHOL", "Cholesterol", "mmol/L"),
    ("CREA", "Creatinine", "µmol/L"),
    ("GGT", "GGT", "U/L"),
    ("PROT", "Total protein", "g/L"),
]
DISEASE = {"1=Hepatitis": "hepatitis", "2=Fibrosis": "fibrosis", "3=Cirrhosis": "cirrhosis"}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "hcvdat0.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        out.write_bytes(z.read("hcvdat0.csv"))


def _panel(r: dict) -> str:
    parts = [f"{r['Age']}-year-old {'man' if r['Sex'] == 'm' else 'woman'}"]
    for col, name, unit in ANALYTES:
        if r[col] not in ("", "NA"):
            parts.append(f"{name} {r[col]} {unit}")
    return "; ".join(parts)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = list(csv.DictReader(open(raw_dir / "hcvdat0.csv", newline="", encoding="utf-8")))
    sick = [r for r in rows if r["Category"] in DISEASE]
    donors = hash_order([r for r in rows if r["Category"] == "0=Blood Donor"], lambda r: r[""], "hcv_labs.donor")
    for r in sorted(sick + donors[:N_DONORS], key=lambda r: int(r[""])):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"labs": _panel(r)},
            shape="detect",
            node_hint="machine.healthcare.lab_results",
            template_id="hcv_labs.liver_disease",
            source_item_id=f"row:{r['']}",
            license=LICENSE,
            truth=r["Category"] in DISEASE,
            meta={"category_raw": r["Category"]},
        )
