"""LiveCareer resume dataset (Kaggle "Resume Dataset", mirrored on HF as opensporks/resumes, CC0): 2,484
resumes, each filed under one of 24 job categories on livecareer.com.

Template "resume.category": Choice "Which job category does `resume` fit best?" over the 24 categories,
truth = the category the resume was filed under. The label is the site's filing category, so a few
resumes read as another field (e.g. a DESIGNER file with nursing duties); kept as the dataset has it.
Resume text: whitespace collapsed, truncated to 1,500 chars. Balanced round-robin across categories
(the small BPO and AUTOMOBILE categories run out first).
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

NAME = "resume_match"
URL = "https://huggingface.co/api/datasets/opensporks/resumes/parquet/default/train/0.parquet"
TARGET = env_int("TARGET_RESUME_MATCH", 1000)
SALT = "resume_match.v1"
MAX_CHARS = 1500
TEXT = "Which job category does `resume` fit best?"
LICENSE = "CC0-1.0"

# dataset label -> (key Jev sees, description)
CATEGORIES: dict[str, tuple[str, str]] = {
    "ACCOUNTANT": ("accountant", "Accounting and bookkeeping"),
    "ADVOCATE": ("advocate", "Advocacy, legal aid and case work"),
    "AGRICULTURE": ("agriculture", "Farming, agronomy and agricultural work"),
    "APPAREL": ("apparel", "Clothing and fashion design, production and retail"),
    "ARTS": ("arts", "Fine and performing arts"),
    "AUTOMOBILE": ("automobile", "Automotive industry and vehicle work"),
    "AVIATION": ("aviation", "Aviation, aircraft and airline work"),
    "BANKING": ("banking", "Banking and bank branch work"),
    "BPO": ("bpo", "Business process outsourcing and call-center work"),
    "BUSINESS-DEVELOPMENT": ("business_development", "Business development and partnerships"),
    "CHEF": ("chef", "Cooking and kitchen work"),
    "CONSTRUCTION": ("construction", "Building construction and trades"),
    "CONSULTANT": ("consultant", "Consulting"),
    "DESIGNER": ("designer", "Graphic, interior or product design"),
    "DIGITAL-MEDIA": ("digital_media", "Digital media, content and online marketing"),
    "ENGINEERING": ("engineering", "Engineering"),
    "FINANCE": ("finance", "Corporate finance and financial analysis"),
    "FITNESS": ("fitness", "Fitness training and coaching"),
    "HEALTHCARE": ("healthcare", "Healthcare and medical work"),
    "HR": ("hr", "Human resources"),
    "INFORMATION-TECHNOLOGY": ("information_technology", "Information technology and IT support"),
    "PUBLIC-RELATIONS": ("public_relations", "Public relations and communications"),
    "SALES": ("sales", "Sales"),
    "TEACHER": ("teacher", "Teaching"),
}
OPTIONS = {k: d for k, d in CATEGORIES.values()}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet", columns=["ID", "Resume_str", "Category"])
    by_cat: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for rid, text, cat in df.iter_rows():
        clean = re.sub(r"\s+", " ", text or "").strip()
        if len(clean) < 200 or clean.lower() in seen:
            continue
        seen.add(clean.lower())
        if len(clean) > MAX_CHARS:
            clean = clean[:MAX_CHARS].rstrip() + " …"
        by_cat[cat].append((str(rid), clean))
    assert set(by_cat) == set(CATEGORIES), set(by_cat) ^ set(CATEGORIES)

    pools = {c: hash_order(v, lambda x: x[0], f"{SALT}|{c}") for c, v in by_cat.items()}
    picked: list[tuple[str, str, str]] = []
    depth = 0
    while len(picked) < TARGET:
        progressed = False
        for c in CATEGORIES:
            if len(picked) >= TARGET:
                break
            if depth < len(pools[c]):
                picked.append((c, *pools[c][depth]))
                progressed = True
        depth += 1
        if not progressed:
            break

    for cat, rid, resume in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"resume": resume},
            shape="classify",
            node_hint="machine.people.resume_match",
            template_id="resume.category",
            source_item_id=rid,
            license=LICENSE,
            truth=CATEGORIES[cat][0],
            meta={"label_raw": cat},
        )
