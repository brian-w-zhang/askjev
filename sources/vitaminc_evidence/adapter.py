"""VitaminC (Schuster, Fisch & Barzilay 2021): contrastive fact verification built from real Wikipedia
revisions. Annotators wrote claims that one version of a revised sentence supports and the other
refutes; each (claim, evidence sentence) pair carries SUPPORTS / REFUTES / NOT ENOUGH INFO.

Template "vitaminc.evidence_verdict" (Choice, node research.claim_support): what does the Wikipedia
sentence in `evidence` say about `claim`. Truth = label. Pool: the test split, revision_type == "real"
only (the "synthetic" half pairs claims with annotator-rewritten evidence), and rows with a FEVER_id
dropped (FEVER-derived claims; FEVER is already the fever_claims source). The release's tokenised spacing
is undone. Balanced across labels, salted hash order, at most one pair per case (revision).
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

NAME = "vitaminc_evidence"
URL = "https://huggingface.co/api/datasets/tals/vitaminc/parquet/default/test/0.parquet"
TARGET = env_int("TARGET_VITAMINC_EVIDENCE", 2000)
LICENSE = "CC-BY-SA-3.0"
TEXT = "Does the Wikipedia sentence in `evidence` confirm `claim`, contradict it, or not decide it?"
OPTIONS = {
    "confirms": "`evidence` states facts that make `claim` true",
    "contradicts": "`evidence` states facts that make `claim` false",
    "does_not_decide": "`evidence` does not contain enough to tell whether `claim` is true",
}
LABELS = {"SUPPORTS": "confirms", "REFUTES": "contradicts", "NOT ENOUGH INFO": "does_not_decide"}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=180)
    r.raise_for_status()
    out.write_bytes(r.content)


def detok(s: str) -> str:
    s = " ".join(s.replace("�", " ").split())
    s = re.sub(r" ([,.;:!?%)\]])", r"\1", s)
    s = re.sub(r"([(\[]) ", r"\1", s)
    s = re.sub(r" (['’](?:s|re|ve|d|ll|m|t)\b)", r"\1", s)
    s = re.sub(r" n't\b", "n't", s)
    s = re.sub(r"(\w) - (\w)", r"\1-\2", s)
    s = re.sub(r"`` ?| ?''", '"', s)
    s = re.sub(r"-LRB- ?", "(", s)
    s = re.sub(r" ?-RRB-", ")", s)
    return s


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet").filter(
        (pl.col("revision_type") == "real") & (pl.col("FEVER_id") == "")
    )
    pools: dict[str, list] = defaultdict(list)
    for uid, case, label, claim, ev, page in df.select(
        "unique_id", "case_id", "label", "claim", "evidence", "page"
    ).iter_rows():
        claim, ev = detok(claim), detok(ev)
        if len(claim) < 10 or len(ev) < 30 or claim == ev:
            continue
        pools[LABELS[label]].append((uid, case, claim, ev, page))
    used_cases: set[str] = set()
    for li, lab in enumerate(sorted(pools)):
        per = TARGET // 3 + (1 if li < TARGET % 3 else 0)
        n = 0
        for uid, case, claim, ev, page in hash_order(pools[lab], lambda x: x[0], f"vitc|{lab}"):
            if n >= per:
                break
            if case in used_cases:
                continue
            used_cases.add(case)
            n += 1
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OPTIONS,
                state={"claim": claim[:500], "evidence": ev[:1500]},
                shape="verify",
                node_hint="machine.research.claim_support",
                template_id="vitaminc.evidence_verdict",
                source_item_id=f"test:{uid}",
                license=LICENSE,
                truth=lab,
                meta={"split": "test", "page": page, "label_raw": [k for k, v in LABELS.items() if v == lab][0]},
            )
