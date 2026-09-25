"""MedMCQA (Pal et al. 2022): Indian medical entrance exam (AIIMS / NEET PG) questions, World factual Choice with truth.

Choice over the four answer texts (readable keys), truth = the correct one. The whole dev split plus a salted-hash
sample of train, capped per subject so Medicine/Surgery don't dominate. Filters, keys, flags and dedupe are shared
with the mmlu adapter (snap filter: no picture/computation stems, no numeric answers, no numbered-statement combos,
a wrong "all/none of the above" removed and the item dropped when it is the right one); items near-duplicating an
mmlu pick are skipped. The explanation field is never used.
"""

from __future__ import annotations

import hashlib
import importlib.util
import random
import re
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "medmcqa"
LICENSE = "Apache-2.0"
TARGET = env_int("TARGET_MEDMCQA", 5000)
PER_SUBJECT = env_int("MEDMCQA_PER_SUBJECT", 420)
SALT = "medmcqa-20260924"
SPLITS = ("validation", "train")  # dev first: it is the cleaner split
EARLIER = ("mmlu",)

_spec = importlib.util.spec_from_file_location("sources.arc", Path(__file__).parents[1] / "arc" / "adapter.py")
ARC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ARC)
M = ARC.M

SUBJECT_NODE = {
    "Anatomy": "world.health.human_body",
    "Physiology": "world.health.human_body",
    "Biochemistry": "world.science.biology_genetics",
    "Pathology": "world.health.diseases",
    "Microbiology": "world.health.diseases",
    "Medicine": "world.health.diseases",
    "Pharmacology": "world.health.medicine",
    "Surgery": "world.health.medicine",
    "Anaesthesia": "world.health.medicine",
    "Radiology": "world.health.medicine",
    "Forensic Medicine": "world.health.medicine",
    "Orthopaedics": "world.health.diseases",
    "Skin": "world.health.diseases",
    "Ophthalmology": "world.health.diseases",
    "ENT": "world.health.diseases",
    "Psychiatry": "world.health.mental_health",
    "Gynaecology & Obstetrics": "world.health",
    "Pediatrics": "world.health",
    "Social & Preventive Medicine": "world.health",
    "Dental": "world.health",  # dental materials and procedures: no closer node; beam placement decides
    "Unknown": "world.health",
}
SEXUAL = re.compile(
    r"\b(abortion\w*|mtp|termination of pregnancy|sexual\w*|intercourse|coitus|coital|rape\w*|sodomy|incest|"
    r"contracepti\w+|condoms?|penis|penile|vagin\w*|vulv\w*|clitor\w*|genital\w*|erectile|erection|ejaculat\w*|"
    r"orgasm\w*|sex worker\w*|prostitut\w*|syphilis|gonorrh\w*|chlamydia|stds?|stis?|hiv|aids|virginity|hymen|"
    r"homosexual\w*|paraphilia\w*|sexually)\b",
    re.I,
)
SELF_HARM = re.compile(r"\b(suicid\w*|self[- ]harm|hanging|strangulation|poison\w*|infanticide|autopsy|post[- ]mortem)\b",
                       re.I)
JUNK_TAIL = re.compile(r"[\s'\")(:;,.\-–]+$")
QSTART = re.compile(r"^(which|what|who|whom|whose|where|when|why|how|is|are|was|were|do|does|did|can|could|should|"
                    r"will|would|has|have)\b", re.I)
GARBLED = re.compile(r"[^\x00-\x7f]|\?\?|\b(ans|ref|explanation)\b[.:]|\s{2,}|_{3,}", re.I)


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "openlifescienceai/medmcqa", {f"{s}.parquet": f"default/{s}/0.parquet" for s in SPLITS})


def _stem(q: str) -> str | None:
    s = M.clean(q or "")
    if GARBLED.search(s) or not 5 <= len(s.split()) <= 60:
        return None
    if s.endswith("?"):
        return s
    body = JUNK_TAIL.sub("", s)
    if (QSTART.match(body) or re.search(r"\bwhich\b", body, re.I)) and not re.search(r"\b(is|are|was|were|of|the|a|an|to|by|in)$", body, re.I):
        return body + "?"  # "Which of the following is not true for myelinated nerve fibers:" -> "...fibers?"
    return body  # a sentence fragment: mmlu's completion_text wraps it


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], ARC.taken_norms(EARLIER)
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for qid, q, a, b, c, d, cop, subj in df.select(
                "id", "question", "opa", "opb", "opc", "opd", "cop", "subject_name").iter_rows():
            stem = _stem(q)
            if not stem or subj not in SUBJECT_NODE or cop not in (0, 1, 2, 3):
                continue
            answers = [JUNK_TAIL.sub("", M.clean(x or "")) for x in (a, b, c, d)]
            if any(not x or GARBLED.search(x) or len(x) > 150 for x in answers):
                continue
            # the source's answer letter is skewed toward (a): shuffle deterministically per item
            order = list(range(4))
            random.Random(int(hashlib.sha256(f"{SALT}:{qid}".encode()).hexdigest()[:16], 16)).shuffle(order)
            kept = M.snap_filter(stem, [answers[i] for i in order], order.index(cop))
            if not kept:
                continue
            answers, correct = kept
            k = M.item_key(stem, answers[correct])
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": f"{split}:{qid}", "split": split, "subject": subj, "q": stem, "answers": answers,
                         "correct": correct, "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    by_subject: dict[str, list[dict]] = {}
    for it in pool_sorted(_pool(raw_dir)):
        by_subject.setdefault(it["subject"], []).append(it)
    capped = [it for s in sorted(by_subject) for it in by_subject[s][:PER_SUBJECT]]
    return pool_sorted(capped)[:TARGET]


def pool_sorted(items: list[dict]) -> list[dict]:
    """Dev before train, each in salted-hash order (prefix-stable in the caps)."""
    return sorted(hash_order(items, lambda x: x["id"], SALT), key=lambda x: x["split"] != "validation")


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: (x["subject"], x["id"])):
        blob = " ".join([it["q"], *it["answers"]])
        fl = M.flags(blob)
        if (SEXUAL.search(blob) or SELF_HARM.search(blob) or it["subject"] == "Forensic Medicine") \
                and "sensitive" not in fl:
            fl.append("sensitive")
        if re.search(r"\babortion\w*|\bmtp\b|termination of pregnancy", blob, re.I) and "political" not in fl:
            fl.append("political")
        text, origin = M.completion_text(it["q"])
        meta = {"subject": it["subject"], "split": it["split"]}
        if fl:
            meta["flags"] = fl
        base = SUBJECT_NODE[it["subject"]]
        node = M.science_hint(it["q"], it["answers"][it["correct"]], default="world.health") \
            if base == "world.health" and it["subject"] == "Unknown" else base
        if not node.startswith(("world.health", "world.science.biology_genetics")):
            node = "world.health"
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=node,
                              item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
