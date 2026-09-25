"""MultiNLI (Williams, Nangia & Bowman 2018): premise/hypothesis pairs from ten genres of written and
spoken English (fiction, government reports, Slate, telephone speech, travel guides, 9/11 report, face-to-
face, letters, OUP non-fiction, Verbatim), hypotheses written by crowdworkers and validated by four more.

Template "mnli.grounded" (Choice, node ai_systems.extraction_verification, the node for checking
a statement read off a source against that source): taking `source` as true, does
`statement` follow from it, contradict it, or neither. Truth = gold label (the validated majority).
Pool: validation_matched + validation_mismatched (19,647 pairs; the test labels are not public).
Balanced across the three labels and stratified by genre, salted hash order.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "mnli_grounding"
BASE = "https://huggingface.co/api/datasets/nyu-mll/multi_nli/parquet/default"
SPLITS = ["validation_matched", "validation_mismatched"]
TARGET = env_int("TARGET_MNLI_GROUNDING", 2000)
LICENSE = "Mixed open licenses (OANC portions public domain / CC-BY-3.0; fiction and Slate per MultiNLI data description)"
TEXT = "Taking everything in `source` as true, does `statement` follow from it, contradict it, or neither?"
OPTIONS = {
    "follows": "`statement` has to be true if `source` is true",
    "contradicts": "`statement` cannot be true if `source` is true",
    "neither": "`source` leaves open whether `statement` is true or false",
}
LABELS = {0: "follows", 1: "neither", 2: "contradicts"}


def fetch(raw_dir: Path) -> None:
    for sp in SPLITS:
        out = raw_dir / f"{sp}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{sp}/0.parquet", follow_redirects=True, timeout=180)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list] = defaultdict(list)
    seen = set()
    for sp in SPLITS:
        df = pl.read_parquet(raw_dir / f"{sp}.parquet").select("pairID", "premise", "hypothesis", "genre", "label")
        for pid, prem, hyp, genre, label in df.iter_rows():
            if label not in LABELS:
                continue
            prem, hyp = " ".join(prem.split()), " ".join(hyp.split())
            if len(prem) < 15 or len(hyp) < 5 or (prem, hyp) in seen:
                continue
            seen.add((prem, hyp))
            pools[LABELS[label]].append((sp, pid, prem, hyp, genre))
    for li, lab in enumerate(sorted(pools)):
        per = TARGET // 3 + (1 if li < TARGET % 3 else 0)
        # interleave genres so each label covers all ten
        by_genre: dict[str, list] = defaultdict(list)
        for x in hash_order(pools[lab], lambda x: x[1], f"mnli|{lab}"):
            by_genre[x[4]].append(x)
        picked, i = [], 0
        genres = sorted(by_genre)
        while len(picked) < per and any(i < len(by_genre[g]) for g in genres):
            for g in genres:
                if i < len(by_genre[g]) and len(picked) < per:
                    picked.append(by_genre[g][i])
            i += 1
        for sp, pid, prem, hyp, genre in picked:
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OPTIONS,
                state={"source": prem[:1500], "statement": hyp[:500]},
                shape="verify",
                node_hint="machine.ai_systems.extraction_verification",
                template_id="mnli.grounded",
                source_item_id=f"{sp}:{pid}",
                license=LICENSE,
                truth=lab,
                meta={"split": sp, "genre": genre},
            )
