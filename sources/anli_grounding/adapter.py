"""Adversarial NLI (Nie et al. 2020, Facebook AI): context passages (Wikipedia in rounds 1-2; Wikipedia,
news, fiction, spoken text and procedural text in round 3) paired with hypotheses that crowdworkers wrote
to fool a strong NLI model, each verified by other workers.

Template "anli.backed_up" (Choice, node ai_systems.extraction_verification): does `context` back up
`claim`, rule it out, or leave it open. Truth = the verified gold label. Pool: dev + test of all three
rounds (6,400 pairs). Balanced across labels and round-robin across rounds, salted hash order.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "anli_grounding"
BASE = "https://huggingface.co/api/datasets/facebook/anli/parquet/plain_text"
SPLITS = [f"{s}_r{r}" for r in (1, 2, 3) for s in ("dev", "test")]
TARGET = env_int("TARGET_ANLI_GROUNDING", 1500)
LICENSE = "CC-BY-NC-4.0"
TEXT = "Does `context` back up `claim`, rule it out, or leave it open?"
OPTIONS = {
    "backed_up": "`context` shows that `claim` is true",
    "ruled_out": "`context` shows that `claim` is false",
    "left_open": "`context` does not settle whether `claim` is true",
}
LABELS = {0: "backed_up", 1: "left_open", 2: "ruled_out"}


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
        df = pl.read_parquet(raw_dir / f"{sp}.parquet").select("uid", "premise", "hypothesis", "label")
        for uid, prem, hyp, label in df.iter_rows():
            if label not in LABELS:
                continue
            prem = "\n".join(" ".join(x.split()) for x in prem.split("<br>") if x.strip())
            hyp = " ".join(hyp.split())
            if len(prem) < 30 or len(hyp) < 5 or (prem, hyp) in seen:
                continue
            seen.add((prem, hyp))
            pools[LABELS[label]].append((sp, uid, prem, hyp))
    for li, lab in enumerate(sorted(pools)):
        per = TARGET // 3 + (1 if li < TARGET % 3 else 0)
        by_round: dict[str, list] = defaultdict(list)
        for x in hash_order(pools[lab], lambda x: x[1], f"anli|{lab}"):
            by_round[x[0][-2:]].append(x)
        rounds = sorted(by_round)
        picked, i = [], 0
        while len(picked) < per and any(i < len(by_round[r]) for r in rounds):
            for r in rounds:
                if i < len(by_round[r]) and len(picked) < per:
                    picked.append(by_round[r][i])
            i += 1
        for sp, uid, prem, hyp in picked:
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OPTIONS,
                state={"context": prem[:1500], "claim": hyp[:500]},
                shape="verify",
                node_hint="machine.ai_systems.extraction_verification",
                template_id="anli.backed_up",
                source_item_id=f"{sp}:{uid}",
                license=LICENSE,
                truth=lab,
                meta={"split": sp, "round": sp[-2:]},
            )
