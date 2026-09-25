"""Medical Question Pairs (McCreery et al. 2020, Curai): 1,524 real patient questions;
for each, doctors wrote one rewording with the same meaning and one closely related question that needs
a different answer. 3,048 labelled pairs.

Template "medqp.same_question": Noul "Do `question_a` and `question_b` ask the same medical question?"
Truth = the doctor's label (similar = true). Which question is shown first is set by hash. Balanced
50/50 in salted hash order.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "medical_question_pairs"
URL = "https://huggingface.co/api/datasets/curaihealth/medical_questions_pairs/parquet/default/train/0.parquet"
TARGET = env_int("TARGET_MEDICAL_QUESTION_PAIRS", 2000)
LICENSE = "Unknown license (HF card); public research dataset, cite McCreery et al. 2020"
TEXT = "Do `question_a` and `question_b` ask the same medical question?"
CRITERIA = {
    "true": "A doctor could answer both with the same answer: they ask the same thing in different words",
    "false": "They are about a related topic but need different answers",
}
SENSITIVE = re.compile(r"\b(sex\w*|intercourse|penis|vagina\w*|genital\w*|erectile|erection\w*|condom\w*|"
                       r"orgasm\w*|masturbat\w*|porn\w*|suicid\w*|self[- ]harm|overdose\w*|abortion\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").with_row_index("row")
    pools: dict[bool, list[tuple[int, str, str]]] = {True: [], False: []}
    for row, q1, q2, label in df.select("row", "question_1", "question_2", "label").iter_rows():
        a, b = " ".join(q1.split()), " ".join(q2.split())
        if not a or not b or a.lower() == b.lower():
            continue
        pools[label == 1].append((row, a, b))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += [(label, x) for x in hash_order(pools[label], lambda x: x[0], f"medqp.{label}")[:k]]
    picked.sort(key=lambda x: x[1][0])

    for label, (row, a, b) in picked:
        if int(hashlib.sha256(f"medqp.swap|{row}".encode()).hexdigest(), 16) % 2:
            a, b = b, a
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"question_a": a[:1500], "question_b": b[:1500]},
            shape="verify",
            node_hint="machine.documents.entity_resolution",
            template_id="medqp.same_question",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=label,
            meta={"label_raw": int(label), **({"flags": ["sensitive"]} if SENSITIVE.search(a + " " + b) else {})},
        )
