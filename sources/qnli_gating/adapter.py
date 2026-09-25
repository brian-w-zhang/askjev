"""QNLI (GLUE; Wang et al. 2018, built from SQuAD 1.1): a question paired with one sentence from the
Wikipedia paragraph that holds its answer. Label: entailment = the sentence contains the answer.

Template "qnli.contains_answer": Noul "Does `passage` contain the answer to `question`?" Truth = entailment.
Uses the validation split (5,463 pairs; the test labels are hidden); balanced 50/50, at most one pair per
question, salted hash order.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "qnli_gating"
BASE = "https://huggingface.co/api/datasets/nyu-mll/glue/parquet/qnli/"
SPLITS = ("validation",)
TARGET = env_int("TARGET_QNLI_GATING", 2500)
LICENSE = "CC-BY-SA-4.0 (SQuAD 1.1 / Wikipedia text; GLUE QNLI)"
TEXT = "Does `passage` contain the answer to `question`?"
CRITERIA = {
    "true": "The passage states the answer to the question, so it is worth adding to the context",
    "false": "The passage is on the same topic but does not state the answer",
}
POLITICAL = re.compile(r"\b(abortion\w*|gun control|immigra\w*|trump|obama|clinton|bush|biden|democrat\w*|"
                       r"republican\w*|election\w*|israel\w*|palestin\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}{split}/0.parquet", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[str, str, str]]] = {True: [], False: []}
    seen_q: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for q, s, label, idx in df.select("question", "sentence", "label", "idx").iter_rows():
            q, s = " ".join(q.split()), " ".join(s.split())
            if len(s) < 30 or q.lower() in seen_q:
                continue
            seen_q.add(q.lower())
            pools[label == 0].append((f"{split}:{idx}", q, s))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += [(label, x) for x in hash_order(pools[label], lambda x: x[0], f"qnli.{label}")[:k]]
    picked.sort(key=lambda x: (x[1][0].split(":")[0], int(x[1][0].split(":")[1])))

    for label, (sid, q, s) in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"question": q, "passage": s[:1500]},
            shape="verify",
            node_hint="machine.search.rag_gating",
            template_id="qnli.contains_answer",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"label_raw": "entailment" if label else "not_entailment",
                  **({"flags": ["political"]} if POLITICAL.search(q + " " + s) else {})},
        )
