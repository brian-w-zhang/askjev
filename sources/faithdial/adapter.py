"""FaithDial (Dziri et al., TACL 2022; McGill-NLP): knowledge-grounded Wizard-of-Wikipedia turns in which
a response should rest only on one Wikipedia `knowledge` sentence. Each original (human wizard) response is
annotated with BEGIN categories by trained annotators.

Template "faithdial.grounded" (Noul, verify): is everything in the response supported by the knowledge
sentence? Truth = true for BEGIN == [Entailment], false for BEGIN == [Hallucination] (information,
opinions or personal experiences the knowledge does not support). Mixed / generic / uncooperative labels
are skipped. The text shown is the ORIGINAL response (FaithDial's edited `response` is used only when the
original was left unedited, which the dataset stores as a null original_response).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "faithdial"
HF = "https://huggingface.co/api/datasets/McGill-NLP/FaithDial/parquet/plain_text/{split}/0.parquet"
SPLITS = ("train", "test")
LICENSE = "MIT"
TARGET = env_int("TARGET_FAITHDIAL", 1800)
TEXT = (
    "Is everything `response` says supported by `knowledge`, with no added facts, opinions or personal "
    "experiences that `knowledge` does not back up?"
)
OPTIONS = {
    "true": "Every claim in the response is stated in or follows from the knowledge sentence.",
    "false": "The response adds something the knowledge does not support: another fact, an opinion, or a "
    "claim about the speaker's own life or tastes.",
}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if not out.exists():
            r = httpx.get(HF.format(split=split), follow_redirects=True, timeout=300)
            r.raise_for_status()
            out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows, seen = {True: [], False: []}, set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for i, r in enumerate(df.iter_rows(named=True)):
            begin = list(r["BEGIN"] or [])
            if begin == ["Entailment"]:
                label, resp = True, r["original_response"] or r["response"]
            elif begin == ["Hallucination"]:
                label, resp = False, r["original_response"]
            else:
                continue
            if not resp or not r["knowledge"]:
                continue
            resp = resp.strip()
            key = re.sub(r"\W+", " ", resp.lower()).strip()
            if len(key.split()) < 4 or key in seen:
                continue
            seen.add(key)
            rows[label].append({"id": f"{split}:{r['dialog_idx']}:{i}", "knowledge": r["knowledge"].strip(),
                                "response": resp, "label": label})
    half = TARGET // 2
    pick = hash_order(rows[True], lambda r: r["id"], NAME)[:half] + hash_order(rows[False], lambda r: r["id"], NAME)[:half]
    for r in hash_order(pick, lambda r: r["id"], NAME + ".order"):
        yield Question(
            text=TEXT, primitive="noul", hemisphere="machine", origin="dataset", source=NAME, options=OPTIONS,
            state={"knowledge": r["knowledge"][:1500], "response": r["response"][:1500]}, shape="verify",
            node_hint="machine.ai_systems.hallucination_citation", template_id="faithdial.grounded",
            source_item_id=r["id"], license=LICENSE, truth=r["label"],
        )
