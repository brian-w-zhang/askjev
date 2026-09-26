"""Self-admitted technical debt (SATD) in source-code comments (Maldonado, Shihab & Tsantalis, "Using Natural
Language Processing to Automatically Detect Self-Admitted Technical Debt", TSE 2017;
github.com/maldonado/tse.satd.data). 62,275 comments from 10 Java projects (Ant, ArgoUML, Columba, EMF,
Hibernate, JEdit, JFreeChart, JMeter, JRuby, SQuirreL), each manually labelled as not technical debt or as
design / defect / implementation / test / documentation debt.

Templates (disjoint comments):
- "satd_comments.debt_type": Choice over the five debt types, SATD comments only, per-type caps.
- "satd_comments.admits_debt": Noul "Does `comment` admit technical debt ...", balanced half SATD, half not.
Comments need at least 3 words; exact duplicates dropped.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "satd_comments"
URL = "https://raw.githubusercontent.com/maldonado/tse.satd.data/master/dataset/technical_debt_dataset.zip"
LICENSE = "No license file; public research dataset (Maldonado, Shihab & Tsantalis, TSE 2017), cite the paper"
PER_SIDE = env_int("PER_SIDE_SATD_COMMENTS", 1200)
TYPE_CAP = env_int("TYPE_CAP_SATD_COMMENTS", 550)
NODE = "machine.code.code_review"

DETECT_TEXT = (
    "Does the source-code comment in `comment` admit technical debt, that is, say the surrounding code is a "
    "temporary, incomplete, buggy or poorly designed solution that should be revisited?"
)
DETECT_OPTS = {
    "true": "The comment admits the code is a workaround, hack, incomplete, known-buggy or badly designed",
    "false": "The comment just explains, labels or documents the code",
}
TYPE_TEXT = "What kind of technical debt does the source-code comment in `comment` admit?"
TYPES = {
    "design": "The design or structure is wrong: a hack, workaround, misplaced code or a needed refactoring",
    "defect": "The code has a known bug or does not work correctly in some case",
    "implementation": "A feature or part of the code is unfinished and still needs to be implemented",
    "test": "Tests are missing, incomplete or need to be improved",
    "documentation": "Documentation or comments are missing or out of date",
}
LABELS = {"DESIGN": "design", "DEFECT": "defect", "IMPLEMENTATION": "implementation", "TEST": "test",
          "DOCUMENTATION": "documentation"}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "technical_debt_dataset.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        out.write_bytes(z.read("technical_debt_dataset.csv"))


def _q(tid, prim, text, options, shape, comment, truth, i, proj, lab) -> Question:
    return Question(
        text=text, primitive=prim, hemisphere="machine", origin="dataset", source=NAME, options=options,
        state={"comment": comment[:1500]}, shape=shape, node_hint=NODE, template_id=tid,
        source_item_id=f"row:{i}", license=LICENSE, truth=truth, meta={"project": proj, "label_raw": lab},
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    d = pl.read_csv(raw_dir / "technical_debt_dataset.csv", infer_schema_length=0, encoding="utf8-lossy")
    items, seen = [], set()
    for i, r in enumerate(d.iter_rows(named=True)):
        t = " ".join((r["commenttext"] or "").split())
        if len(t.lstrip("/*# ").split()) < 3 or t.lower() in seen:
            continue
        seen.add(t.lower())
        items.append((i, r["classification"], t, r["projectname"]))

    used: set[int] = set()
    typed = []
    for raw, key in LABELS.items():
        pool = hash_order([x for x in items if x[1] == raw], lambda x: x[0], "satd.type")[:TYPE_CAP]
        typed += pool
    for i, raw, t, proj in sorted(typed):
        used.add(i)
        yield _q("satd_comments.debt_type", "choice", TYPE_TEXT, TYPES, "classify", t, LABELS[raw], i, proj, raw)

    pos = hash_order([x for x in items if x[1] in LABELS and x[0] not in used], lambda x: x[0], "satd.detect")
    neg = hash_order([x for x in items if x[1] == "WITHOUT_CLASSIFICATION"], lambda x: x[0], "satd.detect")
    n = min(PER_SIDE, len(pos))
    for i, raw, t, proj in sorted(pos[:n] + neg[:n]):
        yield _q("satd_comments.admits_debt", "noul", DETECT_TEXT, DETECT_OPTS, "detect", t,
                 raw != "WITHOUT_CLASSIFICATION", i, proj, raw)
