"""Gold commodity news headlines (Sinha & Khandait 2021, "Impact of News on the Commodity Market"): ~11k real
news headlines about gold (2000-2019), each annotated by human annotators on several dimensions. Read from the
FinGPT instruction-format mirror, which asks one Yes/No question per dimension.

Templates:
- "gold_headlines.direction": Choice "Does `headline` report the gold price going up, going down, or neither?"
  (up / down / neither), from the "price going up" and "price going down" dimensions; headlines marked both
  are dropped. Balanced 1/3 each.
- "gold_headlines.asset_comparison": Noul "Does `headline` compare gold with another asset?", 50/50.
The mirror's "talks about price" and "price staying constant" columns carry identical counts (523 yes each),
which looks like a conversion error, so those dimensions are not used.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "gold_headlines"
URL = "https://huggingface.co/api/datasets/FinGPT/fingpt-headline/parquet/default/{split}/0.parquet"
SPLITS = ("train", "test")
TARGET_DIR = env_int("TARGET_GOLD_DIRECTION", 2500)
TARGET_CMP = env_int("TARGET_GOLD_COMPARISON", 1500)
LICENSE = "Research dataset (Sinha & Khandait 2021, Kaggle 'Gold commodity news and dimensions'); FinGPT HF mirror, no license tag"
UP = "Does the news headline talk about price going up? Please choose an answer from {Yes/No}."
DOWN = "Does the news headline talk about price going down? Please choose an answer from {Yes/No}."
CMP = "Does the news headline compare gold with any other asset? Please choose an answer from {Yes/No}."
DIR_TEXT = "Does `headline` report the gold price going up, going down, or neither?"
DIR_OPTIONS = {
    "up": "The headline says the price of gold rose, is rising or will rise",
    "down": "The headline says the price of gold fell, is falling or will fall",
    "neither": "The headline reports no rise or fall in the gold price",
}
CMP_TEXT = "Does `headline` compare gold with another asset?"
CMP_OPTIONS = {
    "true": "The headline sets gold against another asset, such as silver, stocks, bonds, the dollar or bitcoin",
    "false": "The headline is about gold alone",
}


def fetch(raw_dir: Path) -> None:
    for s in SPLITS:
        out = raw_dir / f"{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=s), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.concat([pl.read_parquet(raw_dir / f"{s}.parquet") for s in SPLITS])
    labels: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for inp, out, ins in df.select("input", "output", "instruction").rows():
        h = " ".join(inp.split())
        labels[h][ins].add(out)
    # Keep headlines whose labels are consistent (a duplicated headline with conflicting labels is dropped).
    heads = {}
    for h, d in labels.items():
        if any(len(v) != 1 for v in d.values()) or not all(k in d for k in (UP, DOWN, CMP)):
            continue
        heads[h] = {k: next(iter(v)) == "Yes" for k, v in d.items()}
    dirs = defaultdict(list)
    for h, d in heads.items():
        if d[UP] and d[DOWN]:
            continue
        dirs["up" if d[UP] else "down" if d[DOWN] else "neither"].append(h)
    per = TARGET_DIR // 3
    picked_dir = []
    for k in DIR_OPTIONS:
        picked_dir += [(h, k) for h in hash_order(dirs[k], lambda x: x, f"gold.dir.{k}")[:per + (1 if k == "up" and TARGET_DIR % 3 else 0)]]
    used = {h for h, _ in picked_dir}
    cmp_pool = {True: [], False: []}
    for h, d in heads.items():
        if h not in used:
            cmp_pool[d[CMP]].append(h)
    n_true = min(TARGET_CMP // 2, len(cmp_pool[True]))
    picked_cmp = [(h, True) for h in hash_order(cmp_pool[True], lambda x: x, "gold.cmp.t")[:n_true]]
    picked_cmp += [(h, False) for h in hash_order(cmp_pool[False], lambda x: x, "gold.cmp.f")[: TARGET_CMP - n_true]]

    for h, k in sorted(picked_dir):
        yield Question(
            text=DIR_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=DIR_OPTIONS,
            state={"headline": h},
            shape="classify",
            node_hint="machine.finance",
            template_id="gold_headlines.direction",
            source_item_id=h,
            license=LICENSE,
            truth=k,
            meta={},
        )
    for h, v in sorted(picked_cmp):
        yield Question(
            text=CMP_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CMP_OPTIONS,
            state={"headline": h},
            shape="detect",
            node_hint="machine.finance",
            template_id="gold_headlines.asset_comparison",
            source_item_id=h,
            license=LICENSE,
            truth=v,
            meta={},
        )
