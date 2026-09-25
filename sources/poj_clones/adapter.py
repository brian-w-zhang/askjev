"""POJ-104 via CodeXGLUE: C/C++ programs students submitted to an online judge, labelled by problem.

Template "poj_clones.same_problem": Noul "Do `program_a` and `program_b` solve the same programming
problem?", truth = both programs were accepted submissions to the same problem (Mou et al. 2016).
Test split (24 problems x 500 programs). Half the pairs share a problem; each program is used once;
programs at most 1,500 characters.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "poj_clones"
URL = "https://huggingface.co/api/datasets/google/code_x_glue_cc_clone_detection_poj104/parquet/default/test/0.parquet"
TARGET = env_int("TARGET_POJ_CLONES", 2000)
MAX_CHARS = 1500
LICENSE = "C-UDA-1.0 (CodeXGLUE); POJ-104 (Mou et al. 2016)"
TEXT = "Do `program_a` and `program_b` solve the same programming problem?"
OPTIONS = {
    "true": "Both programs compute the answer to the same task (same input format, same required output)",
    "false": "The programs solve different tasks",
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(code: str) -> str:
    return code.replace("\r\n", "\n").strip()


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet")
    df = df.filter(pl.col("code").str.len_chars() <= MAX_CHARS)
    seen: set[str] = set()
    by_label: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for _id, code, lab in hash_order(df.select("id", "code", "label").rows(), lambda x: x[0], "poj.v1"):
        c = _clean(code)
        if c in seen or "??" in c:  # "??" = comments whose Chinese text was lost in the export
            continue
        seen.add(c)
        by_label[lab].append((_id, c))
    labels = sorted(by_label, key=int)
    n_same = TARGET // 2
    pairs = []
    # Same-problem pairs: round-robin over problems, consuming two programs at a time.
    cur = {lab: 0 for lab in labels}
    while len(pairs) < n_same:
        progressed = False
        for lab in labels:
            if len(pairs) >= n_same:
                break
            i = cur[lab]
            if i + 1 < len(by_label[lab]):
                pairs.append((by_label[lab][i], by_label[lab][i + 1], lab, lab))
                cur[lab] = i + 2
                progressed = True
        if not progressed:
            break
    # Different-problem pairs from the remaining programs: problem k with problem k+1+j (rotating).
    rest = {lab: by_label[lab][cur[lab]:] for lab in labels}
    pos = {lab: 0 for lab in labels}
    j = 0
    n_diff = TARGET - len(pairs)
    while n_diff > 0:
        progressed = False
        for k, la in enumerate(labels):
            if n_diff <= 0:
                break
            lb = labels[(k + 1 + j % (len(labels) - 1)) % len(labels)]
            if pos[la] < len(rest[la]) and pos[lb] < len(rest[lb]) and la != lb:
                pairs.append((rest[la][pos[la]], rest[lb][pos[lb]], la, lb))
                pos[la] += 1
                pos[lb] += 1
                n_diff -= 1
                progressed = True
            j += 1
        if not progressed:
            break
    for (ia, ca), (ib, cb), la, lb in sorted(pairs, key=lambda p: (p[0][0], p[1][0])):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"program_a": ca, "program_b": cb},
            shape="verify",
            node_hint="machine.code.code_review",
            template_id="poj_clones.same_problem",
            source_item_id=f"test:{ia}:{ib}",
            license=LICENSE,
            truth=la == lb,
            meta={"language": "c/c++", "problem_a": la, "problem_b": lb},
        )
