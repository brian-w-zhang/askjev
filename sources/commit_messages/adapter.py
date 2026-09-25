"""Conventional-commit messages from CommitBench (Schall et al. 2024), filtered to messages written in the
Conventional Commits format (HF djtereano/commitbench_conventional: 44k commits from 6.2k GitHub repos).

Template "commit_messages.type": Choice "What kind of change does `commit_message` describe?" over the
conventional types. The author's own `type(scope):` prefix is the label and is stripped from the text Jev
sees. Messages whose body repeats a conventional prefix (squash-merge lists) are dropped so the answer
does not leak. Per-type quotas so `fix` (53% of the pool) does not dominate; at most 2 per repo.
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

NAME = "commit_messages"
URL = "https://huggingface.co/api/datasets/djtereano/commitbench_conventional/parquet/default/train/0.parquet"
TARGET = env_int("TARGET_COMMIT_MESSAGES", 1500)
PER_REPO = 2
MAX_CHARS = 800
LICENSE = "CC-BY-NC-4.0 (CommitBench)"
TEXT = "What kind of change does `commit_message` describe?"
TYPES: dict[str, str] = {
    "fix": "Fixes a bug or incorrect behavior",
    "feat": "Adds a new feature or capability",
    "refactor": "Restructures code without changing what it does",
    "test": "Adds or changes tests only",
    "docs": "Changes documentation, comments or README only",
    "chore": "Maintenance such as dependency bumps, releases, config or tooling",
    "style": "Formatting, whitespace or lint fixes with no change in behavior",
    "perf": "Makes something faster or use fewer resources",
    "ci": "Changes the continuous-integration setup or pipelines",
    "other": "None of the above",
}
# Share of TARGET per type.
QUOTA = {"fix": 0.19, "feat": 0.19, "refactor": 0.16, "test": 0.13, "chore": 0.13, "docs": 0.11,
         "style": 0.04, "perf": 0.03, "ci": 0.02}
PREFIX = re.compile(r"^\s*(\w+)(?:\([^)\n]*\))?!?:\s*")
LEAK = re.compile(r"(?im)^\s*(?:[*\-]\s*)?(?:fix|feat|refactor|test|docs|chore|style|perf|ci|build|revert)(?:\([^)\n]*\))?!?:")


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(body: str) -> str:
    body = re.sub(r"\s*\(#<I>\)", "", body)
    body = re.sub(r"\n\s*\n+", "\n\n", body.replace("\r\n", "\n"))
    body = body.strip()
    return body if len(body) <= MAX_CHARS else body[: MAX_CHARS - 1].rstrip() + "…"


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet", columns=["hash", "message", "project"])
    pools: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for h, msg, project in df.iter_rows():
        m = PREFIX.match(msg or "")
        if not m or m.group(1).lower() not in QUOTA:
            continue
        typ = m.group(1).lower()
        body = _clean(msg[m.end():])
        key = " ".join(body.lower().split())
        if len(body) < 12 or key in seen or LEAK.search(body):
            continue
        seen.add(key)
        pools[typ].append((h, body, project, msg.split("\n", 1)[0][:120]))

    # Per-type quotas (capped by what exists); any shortfall goes to `fix`, the largest pool.
    want = {t: min(round(TARGET * share), len(pools[t])) for t, share in QUOTA.items()}
    want["fix"] += TARGET - sum(want.values())

    picked = []
    for typ, k in want.items():
        per_repo: dict[str, int] = defaultdict(int)
        n = 0
        for item in hash_order(pools[typ], lambda x: x[0], f"commit.{typ}"):
            if n >= k:
                break
            if per_repo[item[2]] >= PER_REPO:
                continue
            per_repo[item[2]] += 1
            picked.append((typ, item))
            n += 1
    picked.sort(key=lambda x: x[1][0])

    for typ, (h, body, project, first_line) in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=TYPES,
            state={"commit_message": body},
            shape="classify",
            node_hint="machine.code.pr_classification",
            template_id="commit_messages.type",
            source_item_id=h,
            license=LICENSE,
            truth=typ,
            meta={"repo": project, "original_first_line": first_line},
        )
