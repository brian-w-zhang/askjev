"""CommitBench (Schall et al. 2024), test split: real GitHub commits (diff + the author's commit message).

Template "commit_diff_match.message_fits": Noul "Does `commit_message` describe the change in `diff`?".
Half the pairs keep the commit's own message (truth true); half take the message of another commit from the
same repository that touched different files (truth false), so the mismatch is not a change of topic.
Messages must be 4-60 words; conventional-commit messages ("feat:", "fix(x):"...) are excluded so the inputs
do not overlap the commit_messages source (built from CommitBench's conventional subset).
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

NAME = "commit_diff_match"
URL = "https://huggingface.co/api/datasets/Maxscha/commitbench/parquet/default/test/0.parquet"
TARGET = env_int("TARGET_COMMIT_DIFF_MATCH", 2500)
MAX_DIFF = 1500
LICENSE = "CC-BY-NC-4.0 (CommitBench)"
TEXT = "Does `commit_message` describe the change in `diff`?"
OPTIONS = {
    "true": "The message is an accurate summary of what this diff changes",
    "false": "The message describes some other change",
}
CONVENTIONAL = re.compile(r"^\s*(feat|fix|chore|docs|refactor|test|tests|style|perf|build|ci|revert)(\([^)]*\))?!?:", re.I)
FILES = re.compile(r"^diff --git a/(\S+)", re.M)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    out.write_bytes(r.content)


def _msg(m: str) -> str | None:
    m = m.strip()
    if CONVENTIONAL.match(m) or m.startswith("[") or "\n\n" in m[:200] and len(m) > 400:
        return None
    m = " ".join(m.split())
    n = len(m.split())
    if n < 4 or n > 60:
        return None
    return m


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet").filter(pl.col("diff").str.len_chars() <= MAX_DIFF)
    by_proj: dict[str, list] = defaultdict(list)
    seen_msg: set[str] = set()
    for h, diff, message, proj, lang in df.select("hash", "diff", "message", "project", "diff_languages").rows():
        m = _msg(message)
        if not m or m.lower() in seen_msg:
            continue
        seen_msg.add(m.lower())
        by_proj[proj].append((h, diff.strip(), m, lang, frozenset(FILES.findall(diff))))
    # One commit per project at most per role keeps the sample spread over many repositories.
    projects = hash_order([p for p, v in by_proj.items() if len(v) >= 2], lambda p: p, "commit_diff.proj")
    n_true = TARGET // 2
    items = []
    for i, p in enumerate(projects):
        if len(items) >= TARGET:
            break
        commits = hash_order(by_proj[p], lambda c: c[0], "commit_diff.commit")
        a = commits[0]
        if i % 2 == 0 and sum(1 for x in items if x[-1]) < n_true:
            items.append((a, a[2], p, True))
            continue
        other = next((c for c in commits[1:] if not (c[4] & a[4])), None)
        if other is None:
            continue
        if sum(1 for x in items if not x[-1]) < TARGET - n_true:
            items.append((a, other[2], p, False))
    for (h, diff, own, lang, _files), message, proj, match in sorted(items, key=lambda x: x[0][0]):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"diff": diff, "commit_message": message},
            shape="verify",
            node_hint="machine.code.pr_classification",
            template_id="commit_diff_match.message_fits",
            source_item_id=f"test:{h}",
            license=LICENSE,
            truth=match,
            meta={"project": proj, "language": lang, **({} if match else {"own_message": own})},
        )
