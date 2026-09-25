"""CodeXGLUE defect detection (Devign; Zhou et al. 2019): C functions from FFmpeg and QEMU, labelled
`target` = the function was changed by a vulnerability-fixing commit (manually labelled).

Template "code_defects.vulnerable": Noul "Does the function in `code` contain a security vulnerability or
memory-safety bug?" Truth = target. Only functions of at most 1,500 chars; balanced 50/50, seeded hash order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "code_defects"
BASE = "https://huggingface.co/api/datasets/google/code_x_glue_cc_defect_detection/parquet/default"
SPLITS = ("train", "validation", "test")
TARGET = env_int("TARGET_CODE_DEFECTS", 2000)
MAX_CHARS = 1500
LICENSE = "C-UDA-1.0 (CodeXGLUE)"
TEXT = "Does the function in `code` contain a security vulnerability or memory-safety bug?"
CRITERIA = {
    "true": "The function has a flaw an attacker or bad input could trigger, such as a buffer overflow, "
    "out-of-bounds read or write, use-after-free, null dereference, integer overflow, memory leak or missing check",
    "false": "The function has no such flaw",
}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{split}/0.parquet", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _tidy(code: str) -> str:
    # Devign doubles every newline; drop all blank lines and trailing spaces.
    lines = [ln.rstrip() for ln in code.replace("\r\n", "\n").split("\n")]
    return "\n".join(ln for ln in lines if ln).strip()


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list[tuple[str, str, str, str]]] = {True: [], False: []}
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for id_, func, target, project, commit in df.select("id", "func", "target", "project", "commit_id").iter_rows():
            code = _tidy(func)
            key = " ".join(code.split())
            if not code or len(code) > MAX_CHARS or key in seen:
                continue
            seen.add(key)
            pools[bool(target)].append((f"{split}:{id_}", code, project, commit))

    picked = []
    for label, k in ((True, TARGET // 2), (False, TARGET - TARGET // 2)):
        picked += [(label, x) for x in hash_order(pools[label], lambda x: x[0], f"devign.{label}")[:k]]
    picked.sort(key=lambda x: x[1][0])

    for label, (sid, code, project, commit) in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"code": code},
            shape="detect",
            node_hint="machine.code.semantic_lint",
            template_id="code_defects.vulnerable",
            source_item_id=sid,
            license=LICENSE,
            truth=label,
            meta={"project": project, "commit_id": commit, "language": "C"},
        )
