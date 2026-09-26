"""CiteWorth (Wright & Augenstein 2021, HF `copenlu/citeworth`): paragraphs from S2ORC papers across ten
fields, split into cleaned sentences (citation markers removed), each labelled by whether the original
sentence cited an external source.

Template "citeworth.needs_citation": one Noul per sentence, shown inside its (cleaned) paragraph with the
section title: does this sentence need a citation? Truth = the original sentence carried a citation.
Balanced 50/50, round-robin across fields of study, test split only, one sentence per paragraph.
"""

from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "citeworth"
URL = "https://huggingface.co/api/datasets/copenlu/citeworth/parquet/default/test/0.parquet"
TARGET = env_int("TARGET_CITEWORTH", 2500)
SEED = 2021
LICENSE = "CC-BY-NC-4.0 (derived from S2ORC, CC-BY-NC-2.0)"
TEXT = (
    "In the original paper, did the authors cite a source in `sentence`? It comes from `paragraph` in the "
    "`section` section; all citation markers have been removed."
)
OPTIONS = {
    "true": "The sentence carried a citation: it reports something from other work (a prior finding, method, "
    "dataset, fact or definition)",
    "false": "The sentence carried no citation: it is the authors' own contribution, reasoning, description or a "
    "transition",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet")
    rng = random.Random(SEED)
    # (field, label) -> candidates; one sentence per paragraph (chosen by seeded rng, label-balanced later)
    pools: dict[tuple[str, bool], list] = defaultdict(list)
    seen = set()
    for r in df.iter_rows(named=True):
        samples = r["samples"] or []
        sents = [s["text"].strip() for s in samples]
        para = " ".join(sents)
        if len(samples) < 3 or len(para) > 1400 or len(para) < 250:
            continue
        field = (r["mag_field_of_study"] or ["Unknown"])[0]
        section = (r["section_title"] or "").strip()
        if not section or len(section) > 80:
            continue
        key = f"{r['paper_id']}:{r['section_index']}"
        if key in seen:
            continue
        seen.add(key)
        by_lab = defaultdict(list)
        for j, s in enumerate(samples):
            if 40 <= len(s["text"]) <= 400:
                by_lab[s["label"] == "check-worthy"].append(j)
        lab = rng.random() < 0.5
        if not by_lab[lab]:
            lab = not lab
        if not by_lab[lab]:
            continue
        j = rng.choice(by_lab[lab])
        pools[(field, lab)].append((key, j, sents[j], para, section, field, lab))
    fields = sorted({f for f, _ in pools})
    for k in pools:
        pools[k] = hash_order(pools[k], lambda x: x[0], NAME)
    picked = []
    cur = defaultdict(int)
    while len(picked) < TARGET:
        prog = False
        for f in fields:
            for lab in (True, False):
                if len(picked) >= TARGET:
                    break
                p = pools[(f, lab)]
                if cur[(f, lab)] < len(p):
                    picked.append(p[cur[(f, lab)]])
                    cur[(f, lab)] += 1
                    prog = True
        if not prog:
            break
    for key, j, sent, para, section, field, lab in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"section": section, "paragraph": para, "sentence": sent},
            shape="detect",
            node_hint="machine.research.claim_support",
            template_id="citeworth.needs_citation",
            source_item_id=f"test:{key}:{j}",
            license=LICENSE,
            truth=lab,
            meta={"field": field},
        )
