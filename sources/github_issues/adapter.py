"""NLBSE'24 issue report classification: GitHub issues from 5 open-source repos labelled bug / feature /
question (balanced: 200 per label per repo across train + test).

Template "github_issues.type": Choice over bug / feature / question, truth = the dataset label.
State: the issue title and its body (HTML comments from issue templates removed, whitespace tidied,
truncated to 1,200 chars). The dataset has no documentation label.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "github_issues"
BASE = "https://raw.githubusercontent.com/nlbse2024/issue-report-classification/main/data/issues_{split}.csv"
SPLITS = ("train", "test")
TARGET = env_int("TARGET_GITHUB_ISSUES", 2500)
SALT = "github_issues.v1"
BODY_MAX = 1200
# Issue templates that state the type themselves (TF "### Issue type / Bug", VS Code "Type: <b>Bug</b>",
# React "[DevTools Bug]"...): kept as real data, marked in meta.self_labelled so analysis can split them out.
SELF_LABEL = re.compile(
    r"Issue type\s*\n+\s*(Bug|Feature|Support)|Type: <b>(Bug|Feature)|\[DevTools Bug\]"
    r"|request a \*feature\* or report a \*bug\*", re.I)
TEXT = "What kind of issue is the one with `title` and `body`?"
LICENSE = "NLBSE'24 tool competition data (public GitHub issues; the repo's LICENSE file is empty)"

OPTIONS = {
    "bug": "Reports something that is broken or behaves incorrectly",
    "feature": "Asks for a new feature or an improvement to existing behavior",
    "question": "Asks for help, clarification or how to do something",
}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"issues_{split}.csv"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean_body(body: str) -> str:
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    body = body.replace("\r\n", "\n")
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if len(body) > BODY_MAX:
        body = body[:BODY_MAX].rstrip() + " …"
    return body


def normalize(raw_dir: Path) -> Iterator[Question]:
    csv.field_size_limit(10_000_000)
    by_label: dict[str, list[dict]] = defaultdict(list)
    seen: set[str] = set()
    for split in SPLITS:
        with open(raw_dir / f"issues_{split}.csv", newline="", encoding="utf-8") as fh:
            for i, r in enumerate(csv.DictReader(fh)):
                title = re.sub(r"\s+", " ", r["title"] or "").strip()
                body = _clean_body(r["body"])
                if not title or r["label"] not in OPTIONS:
                    continue
                norm = (title + "|" + body).lower()
                if norm in seen:
                    continue
                seen.add(norm)
                by_label[r["label"]].append(
                    {"sid": f"{split}:{i}", "repo": r["repo"], "created_at": r["created_at"],
                     "label": r["label"], "title": title, "body": body}
                )

    # Balanced: equal share per label, each label's pool in salted hash order.
    per = [TARGET // len(OPTIONS) + (1 if j < TARGET % len(OPTIONS) else 0) for j in range(len(OPTIONS))]
    picked = []
    for lab, k in zip(sorted(OPTIONS), per):
        picked += hash_order(by_label[lab], lambda x: x["sid"], f"{SALT}|{lab}")[:k]

    for it in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"title": it["title"], "body": it["body"] or "(empty)"},
            shape="classify",
            node_hint="machine.code.issue_triage",
            template_id="github_issues.type",
            source_item_id=it["sid"],
            license=LICENSE,
            truth=it["label"],
            meta={"repo": it["repo"], "created_at": it["created_at"],
                  "self_labelled": bool(SELF_LABEL.search(it["title"] + "\n" + it["body"]))},
        )
