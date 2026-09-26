"""SemEval-2013 Task 7 (Dzikovska et al. 2013), Joint Student Response Analysis: student answers to
science questions, each graded against a reference answer with one of five labels. Two corpora:
SciEntsBank (grades 3-6 science assessments) and Beetle (a basic-electricity tutoring system). HF mirrors
nkazi/SciEntsBank and nkazi/Beetle (all splits: train, test unseen answers/questions/domains).

Templates (node machine.education.answer_grading; disjoint salted samples):
- "sag.correct" (Noul): is `student_answer` correct given `reference_answer`? Truth = label "correct".
  45% correct.
- "sag.label" (Choice, 5-way): which grade fits the student answer? Truth = the 5-way label; round-robin
  over labels (non_domain and irrelevant are rare and used up).
State = question, reference answer, student answer. Deduplicated on (question, student answer); an
answer given two different labels is dropped.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "semeval_sag"
BASE = "https://huggingface.co/api/datasets/nkazi/{corpus}/parquet/default/{split}/0.parquet"
SPLITS = {"SciEntsBank": ("train", "test_ua", "test_uq", "test_ud"), "Beetle": ("train", "test_ua", "test_uq")}
TARGET_CORRECT = env_int("TARGET_SAG_CORRECT", 2000)
TARGET_LABEL = env_int("TARGET_SAG_LABEL", 1500)
CORRECT_SHARE = 0.45
LICENSE = "CC-BY-4.0"
LABELS = ["correct", "contradictory", "partially_correct_incomplete", "irrelevant", "non_domain"]
CORRECT_TEXT = "Is `student_answer` a correct answer to `question`, given the reference answer `reference_answer`?"
CORRECT = {
    "true": "The student answer is a complete and correct paraphrase of the reference answer",
    "false": "The student answer is incomplete, wrong, contradicts the reference, is off-topic, or is not an answer",
}
LABEL_TEXT = "How should `student_answer` to `question` be graded, given the reference answer `reference_answer`?"
LABEL_OPTIONS = {
    "correct": "A complete and correct paraphrase of the reference answer",
    "partially_correct_incomplete": "Correct as far as it goes but missing some of what the reference answer says",
    "contradictory": "States something that contradicts the reference answer",
    "irrelevant": "Talks about the domain but does not address what the question asks",
    "non_domain": "Not an answer to the question at all (e.g. 'I don't know', a joke, or chatter)",
}


def fetch(raw_dir: Path) -> None:
    for corpus, splits in SPLITS.items():
        for split in splits:
            out = raw_dir / f"{corpus}_{split}.parquet"
            if out.exists():
                continue
            r = httpx.get(BASE.format(corpus=corpus, split=split), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    groups: dict[tuple[str, str], list] = defaultdict(list)
    for corpus, splits in SPLITS.items():
        for split in splits:
            df = pl.read_parquet(raw_dir / f"{corpus}_{split}.parquet")
            for rid, q, ref, ans, lab in df.select("id", "question", "reference_answer", "student_answer", "label").iter_rows():
                q, ref, ans = (" ".join((x or "").split()) for x in (q, ref, ans))
                if not (q and ref and ans):
                    continue
                groups[(q.lower(), ans.lower())].append((f"{corpus}:{split}:{rid}", corpus, q, ref, ans, LABELS[lab]))
    items = []
    for rows in groups.values():
        if len({r[5] for r in rows}) == 1:
            items.append(min(rows))

    # sag.label first (it needs the rare labels), then sag.correct from the rest.
    pools: dict[str, list] = defaultdict(list)
    for it in items:
        pools[it[5]].append(it)
    ordered = {lab: hash_order(v, lambda x: x[0], f"sag.label|{lab}") for lab, v in pools.items()}
    picked, i = [], 0
    while len(picked) < TARGET_LABEL and any(i < len(v) for v in ordered.values()):
        for lab in LABELS:
            if i < len(ordered.get(lab, [])) and len(picked) < TARGET_LABEL:
                picked.append(ordered[lab][i])
        i += 1
    used = {it[0] for it in picked}
    rest = [it for it in items if it[0] not in used]
    n_true = round(TARGET_CORRECT * CORRECT_SHARE)
    pos = hash_order([it for it in rest if it[5] == "correct"], lambda x: x[0], "sag.correct|pos")[:n_true]
    neg = hash_order([it for it in rest if it[5] != "correct"], lambda x: x[0], "sag.correct|neg")[: TARGET_CORRECT - n_true]

    for tid, prim, text, options, sample in (
        ("sag.label", "choice", LABEL_TEXT, LABEL_OPTIONS, picked),
        ("sag.correct", "noul", CORRECT_TEXT, CORRECT, pos + neg),
    ):
        for sid, corpus, q, ref, ans, lab in sorted(sample):
            yield Question(
                text=text,
                primitive=prim,
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=options,
                state={"question": q[:600], "reference_answer": ref[:600], "student_answer": ans[:800]},
                shape="verify" if prim == "noul" else "classify",
                node_hint="machine.education.answer_grading",
                template_id=tid,
                source_item_id=sid,
                license=LICENSE,
                truth=(lab == "correct") if prim == "noul" else lab,
                meta={"corpus": corpus, "label_raw": lab},
            )
