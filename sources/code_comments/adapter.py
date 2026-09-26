"""Manually classified source-code comments from the NLBSE'23 code comment classification repo
(github.com/nlbse2023/code-comment-classification, CC0-1.0).

Templates (one per language, each with its own taxonomy):
- "code_comments.java": whole Java comments from the extended Java set (extended_java/merged_java.csv:
  Pascarella et al. 2019 "Classifying code comments in Java open-source software systems" merged with the
  NLBSE'23 Java set; Eclipse, Hadoop, Vaadin, Guava, Guice, Spark). 12 categories.
- "code_comments.python": class-comment sentences from the NLBSE'23 Python set (Rani et al. 2021 taxonomy;
  Django, pandas, PyTorch, ...). 5 categories.
- "code_comments.pharo": class-comment sentences from the NLBSE'23 Pharo (Smalltalk) set. 6 categories.

Only comments/sentences with exactly one category are used (multi-label ones are dropped), exact
duplicates removed, NLBSE sentences need at least 4 words, and each category is capped so no class
dominates. Truth = the human label.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "code_comments"
BASE = "https://raw.githubusercontent.com/nlbse2023/code-comment-classification/main/"
FILES = {
    "merged_java.csv": "extended_java/merged_java.csv",
    "python.csv": "python/input/python.csv",
    "pharo.csv": "pharo/input/pharo.csv",
}
LICENSE = "CC0-1.0"
CAP = env_int("CAP_CODE_COMMENTS", 250)
MAX_CHARS = 1500
NODE = "machine.code.semantic_lint"

JAVA_TEXT = "What kind of comment is `comment`, taken from a Java source file?"
JAVA = {
    "summary": "Summarizes what the code does or is for",
    "expand": "Explains in more detail how the code works",
    "rationale": "Explains why the code is written the way it is",
    "usage": "Tells callers how to use the code, such as @param or @return tags",
    "exception": "Describes an exception the code can throw",
    "deprecation": "Says the code is deprecated and what to use instead",
    "todo": "Notes pending work, a known bug or an issue number",
    "pointer": "Points to other code or resources, such as @see or @link",
    "commented_out_code": "Code that has been commented out",
    "section_marker": "Separates or labels a section of the file",
    "license": "A copyright or license header",
    "ownership": "Names the authors or contributors",
}
JAVA_COLS = {
    "summary": "summary", "Expand": "expand", "rational": "rationale", "usage": "usage",
    "exception": "exception", "deprecation": "deprecation", "todo": "todo", "Pointer": "pointer",
    "Commented code": "commented_out_code", "formatter": "section_marker", "License": "license",
    "Ownership": "ownership",
}
JAVA_ALL_COLS = [
    "summary", "Expand", "rational", "deprecation", "usage", "exception", "todo", "Incomplete",
    "Commented code", "directive", "formatter", "License", "Ownership", "Pointer", "Auto generated", "Noise",
]

PY_TEXT = "What does the sentence in `comment_sentence` from the docstring of the Python class `class_name` do?"
PY = {
    "summary": "Summarizes what the class is for",
    "usage": "Explains how to use the class, often with an example",
    "parameters": "Describes the class's parameters, arguments or attributes",
    "development_notes": "A note for developers: a todo, known issue, version or implementation remark",
    "expand": "Gives further detail about how the class behaves",
}
PY_LABELS = {"summary": "summary", "usage": "usage", "parameters": "parameters",
             "developmentnotes": "development_notes", "expand": "expand"}

PHARO_TEXT = (
    "What does the sentence in `comment_sentence` from the class comment of the Pharo (Smalltalk) class "
    "`class_name` describe?"
)
PHARO = {
    "intent": "The purpose of the class",
    "responsibilities": "What the class is responsible for knowing or doing",
    "collaborators": "Other classes it interacts with and how",
    "example": "An example of how to use the class",
    "key_messages": "The important messages (methods) of its API",
    "key_implementation_points": "Internal implementation details",
}
PHARO_LABELS = {"intent": "intent", "responsibilities": "responsibilities", "collaborators": "collaborators",
                "example": "example", "keymessages": "key_messages",
                "keyimplementationpoints": "key_implementation_points"}


def fetch(raw_dir: Path) -> None:
    for name, path in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(BASE + path, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _q(tid, text, options, state, truth, sid, meta) -> Question:
    return Question(
        text=text, primitive="choice", hemisphere="machine", origin="dataset", source=NAME, options=options,
        state=state, shape="classify", node_hint=NODE, template_id=tid, source_item_id=sid, license=LICENSE,
        truth=truth, meta=meta,
    )


def _capped(items: list[tuple], salt: str) -> list[tuple]:
    by: dict[str, list[tuple]] = {}
    for it in items:
        by.setdefault(it[0], []).append(it)
    out = []
    for lab in sorted(by):
        out += hash_order(by[lab], lambda x: x[1], salt)[:CAP]
    return sorted(out, key=lambda x: x[1])


def normalize(raw_dir: Path) -> Iterator[Question]:
    # Java: whole comments, single category.
    d = pl.read_csv(raw_dir / "merged_java.csv", infer_schema_length=0)
    items, seen = [], set()
    for i, r in enumerate(d.iter_rows(named=True)):
        labs = [c for c in JAVA_ALL_COLS if r[c]]
        if len(labs) != 1 or labs[0] not in JAVA_COLS:
            continue
        t = (r["Comment"] or "").strip()
        if len(t) < 3 or t in seen:
            continue
        seen.add(t)
        items.append((JAVA_COLS[labs[0]], i, t, r["Project"], r["Class"]))
    for lab, i, t, proj, cls in _capped(items, "code_comments.java"):
        yield _q("code_comments.java", JAVA_TEXT, JAVA, {"comment": t[:MAX_CHARS]}, lab, f"java:{i}",
                 {"project": proj, "file": cls})

    # Python / Pharo: NLBSE sentence-level, one row per (sentence, category) with instance_type 1 = positive.
    for lang, text, options, labels in (
        ("python", PY_TEXT, PY, PY_LABELS),
        ("pharo", PHARO_TEXT, PHARO, PHARO_LABELS),
    ):
        d = pl.read_csv(raw_dir / f"{lang}.csv", infer_schema_length=0)
        pos: dict[str, list[dict]] = {}
        for r in d.iter_rows(named=True):
            if r["instance_type"] == "1":
                pos.setdefault(r["comment_sentence_id"], []).append(r)
        items, seen = [], set()
        for sid, rs in pos.items():
            cats = {r["category"].lower() for r in rs}
            if len(cats) != 1:
                continue
            cat = cats.pop()
            if cat not in labels:
                continue
            s = rs[0]["comment_sentence"].strip()
            if len(s.split()) < 4 or s.lower() in seen:
                continue
            seen.add(s.lower())
            items.append((labels[cat], int(sid), s, rs[0]["class"]))
        for lab, sid, s, cls in _capped(items, f"code_comments.{lang}"):
            yield _q(f"code_comments.{lang}", text, options, {"class_name": cls, "comment_sentence": s[:MAX_CHARS]},
                     lab, f"{lang}:{sid}", {"label_raw": lab})
