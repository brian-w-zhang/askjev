"""CodeReviewer (Li et al. 2022), diff-quality estimation test set: code-change hunks from real GitHub pull
requests in 9 languages, labelled by whether a human reviewer left a review comment on the hunk.

Template "code_review_need.needs_comment": Noul "Does the code change in `diff` need a review comment before
it is merged?", truth = the dataset label. The label is the real review outcome, so it is noisy
(reviewers skip problems, and some comments are questions); kept balanced 50/50 and hunks <= 1,500 chars.

Only the first ~29k lines of the 1.4 GB test file are streamed; the full old-file text ("oldf") is dropped.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "code_review_need"
URL = "https://huggingface.co/datasets/fasterinnerlooper/codereviewer/resolve/main/quality/cls-test.jsonl"
KEEP_LINES = 29000
TARGET = env_int("TARGET_CODE_REVIEW_NEED", 2000)
MAX_CHARS = 1500
LICENSE = "CodeReviewer data (Microsoft, Zenodo 6900648; mirror fasterinnerlooper/codereviewer, no license tag)"
TEXT = "Does the code change in `diff` need a review comment before it is merged?"
OPTIONS = {
    "true": "A reviewer would point out something in this hunk: a bug, a style or naming problem, a missing case, or a question",
    "false": "The hunk can be accepted as it is",
}
LANGS = {"go": "go", "java": "java", "py": "python", "cpp": "c++", "js": "javascript", "rb": "ruby", ".cs": "c#", "c": "c", "php": "php"}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "cls-test.slim.jsonl"
    if out.exists():
        return
    n = 0
    with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r, open(out.with_suffix(".tmp"), "w") as fh:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line.strip():
                continue
            d = json.loads(line)
            d.pop("oldf", None)
            fh.write(json.dumps(d) + "\n")
            n += 1
            if n >= KEEP_LINES:
                break
    out.with_suffix(".tmp").rename(out)


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = []
    seen: set[str] = set()
    for i, line in enumerate(open(raw_dir / "cls-test.slim.jsonl")):
        if i >= KEEP_LINES:
            break
        d = json.loads(line)
        patch = d["patch"].strip()
        if len(patch) > MAX_CHARS or len(patch) < 80 or patch in seen:
            continue
        seen.add(patch)
        rows.append((i, patch, int(d["y"]) == 1, d.get("lang"), d.get("proj"), d.get("msg") or ""))
    out = []
    for lab in (True, False):
        pool = [r for r in rows if r[2] is lab]
        out += hash_order(pool, lambda r: r[0], f"code_review.{lab}")[: TARGET // 2 if lab else TARGET - TARGET // 2]
    for i, patch, lab, lang, proj, msg in sorted(out):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"diff": patch},
            shape="detect",
            node_hint="machine.code.code_review",
            template_id="code_review_need.needs_comment",
            source_item_id=f"cls-test:{i}",
            license=LICENSE,
            truth=lab,
            meta={"language": LANGS.get(lang, lang), "project": proj, **({"review_comment": msg[:500]} if lab else {})},
        )
