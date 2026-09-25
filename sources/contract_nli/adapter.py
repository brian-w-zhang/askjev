"""ContractNLI (Koreeda & Manning 2021): non-disclosure agreements annotated against 17 fixed
hypotheses as entailment, contradiction or not mentioned. Task A variant (HF kiddothe2b/contract-nli
config contractnli_a): the premise is the relevant span(s) of the NDA for the hypothesis (for "not
mentioned" pairs, a span from the same NDA that does not settle it).

Template "contract_nli.entailment" (Choice, node legal.clause_detection): does the excerpt entail,
contradict or not mention the hypothesis. Truth = label. All train/validation/test pairs pooled;
excerpts > 1,500 chars dropped; contradictions are the rarest class so all of them are kept, the rest
is split evenly between entailed and not mentioned, round-robin over the 17 hypotheses.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "contract_nli"
BASE = "https://huggingface.co/api/datasets/kiddothe2b/contract-nli/parquet/contractnli_a/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
TARGET = env_int("TARGET_CONTRACT_NLI", 2500)
LICENSE = "CC-BY-4.0 (ContractNLI, Koreeda & Manning 2021); HF copy kiddothe2b/contract-nli tagged CC-BY-NC-SA-4.0"
TEXT = "Does `contract_excerpt` entail, contradict, or not mention `hypothesis`?"
OPTIONS = {
    "entailed": "The excerpt states or clearly implies that the hypothesis holds for this agreement",
    "contradicted": "The excerpt states or clearly implies that the hypothesis does not hold for this agreement",
    "not_mentioned": "The excerpt does not settle whether the hypothesis holds",
}
LABELS = ["contradicted", "entailed", "not_mentioned"]  # dataset ClassLabel order
MAX_CHARS = 1500


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"a_{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    seen: set[tuple[str, str]] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"a_{split}.parquet").with_row_index("row")
        for row, premise, hyp, label in df.select("row", "premise", "hypothesis", "label").iter_rows():
            excerpt = "\n".join(" ".join(l.split()) for l in premise.split("\n") if l.strip())
            hyp = " ".join(hyp.split())
            if len(excerpt) < 30 or len(excerpt) > MAX_CHARS or (excerpt, hyp) in seen:
                continue
            seen.add((excerpt, hyp))
            pools[LABELS[label]][hyp].append((f"{split}:{row}", split, excerpt, hyp))

    def round_robin(by_hyp: dict[str, list], k: int, salt: str) -> list:
        orders = {h: hash_order(v, lambda x: x[0], f"{salt}.{h}") for h, v in by_hyp.items()}
        out, i = [], 0
        while len(out) < k and any(i < len(v) for v in orders.values()):
            for h in sorted(orders):
                if len(out) < k and i < len(orders[h]):
                    out.append(orders[h][i])
            i += 1
        return out

    n_contra = min(sum(len(v) for v in pools["contradicted"].values()), TARGET // 2)
    rest = TARGET - n_contra
    picked = [("contradicted", x) for x in round_robin(pools["contradicted"], n_contra, "cnli.c")]
    picked += [("entailed", x) for x in round_robin(pools["entailed"], rest // 2, "cnli.e")]
    picked += [("not_mentioned", x) for x in round_robin(pools["not_mentioned"], rest - rest // 2, "cnli.n")]
    picked.sort(key=lambda x: (SPLITS.index(x[1][1]), int(x[1][0].split(":")[1])))

    for label, (sid, split, excerpt, hyp) in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"contract_excerpt": excerpt, "hypothesis": hyp},
            shape="verify",
            node_hint="machine.legal.clause_detection",
            template_id="contract_nli.entailment",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"split": split, "label_raw": {"contradicted": "contradiction", "entailed": "entailment",
                                               "not_mentioned": "neutral"}[label]},
        )
