"""BigCloneBench via CodeXGLUE (clone detection): pairs of Java methods labelled as clones or not.

Template "clone_pairs.same_function": Noul "Do `code_a` and `code_b` implement the same functionality?",
truth = the BigCloneBench clone label (functionality clones validated by human judges, Svajlenko et al. 2014).
Only the first test parquet shard is used; both methods must be at most 1,500 characters (never truncated),
each method appears in at most 12 sampled pairs, 50% clones.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "clone_pairs"
URL = "https://huggingface.co/api/datasets/google/code_x_glue_cc_clone_detection_big_clone_bench/parquet/default/test/0.parquet"
TARGET = env_int("TARGET_CLONE_PAIRS", 2500)
MAX_CHARS = 1500
MAX_USES = 12
LICENSE = "C-UDA-1.0 (CodeXGLUE); BigCloneBench (Svajlenko et al. 2014)"
TEXT = "Do `code_a` and `code_b` implement the same functionality?"
OPTIONS = {
    "true": "Both methods do the same job (same inputs to same kind of result), even if written differently",
    "false": "The methods do different jobs",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test0.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(code: str) -> str:
    return code.replace("\r\n", "\n").strip()


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test0.parquet")
    df = df.filter(
        (pl.col("func1").str.len_chars() <= MAX_CHARS)
        & (pl.col("func2").str.len_chars() <= MAX_CHARS)
        & (pl.col("id1") != pl.col("id2"))
    )
    rows = df.select("id", "id1", "id2", "func1", "func2", "label").rows()
    picked = []
    uses: dict[int, int] = {}
    seen_pairs: set[tuple[str, str]] = set()
    quota = {True: TARGET // 2, False: TARGET - TARGET // 2}
    for r in hash_order(rows, lambda x: x[0], "clone_pairs.v1"):
        _id, a, b, fa, fb, lab = r
        ha, hb = _clean(fa), _clean(fb)
        pair = (min(ha, hb), max(ha, hb))
        if quota[lab] <= 0 or pair in seen_pairs or uses.get(a, 0) >= MAX_USES or uses.get(b, 0) >= MAX_USES:
            continue
        if ha == hb:
            continue
        seen_pairs.add(pair)
        uses[a] = uses.get(a, 0) + 1
        uses[b] = uses.get(b, 0) + 1
        quota[lab] -= 1
        picked.append(r)
        if not any(quota.values()):
            break
    picked.sort(key=lambda x: x[0])
    for _id, a, b, fa, fb, lab in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"code_a": _clean(fa), "code_b": _clean(fb)},
            shape="verify",
            node_hint="machine.code.code_review",
            template_id="clone_pairs.same_function",
            source_item_id=f"test:{_id}",
            license=LICENSE,
            truth=bool(lab),
            meta={"language": "java", "id1": a, "id2": b},
        )
