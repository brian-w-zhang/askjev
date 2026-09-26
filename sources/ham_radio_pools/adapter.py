"""FCC amateur radio license exam question pools (NCVEC): Technician, General, Amateur Extra.

The three current pools as published by the NCVEC Question Pool Committee (docx, errata applied in the pool
text: withdrawn questions appear as "Question Deleted" stubs and are skipped). The pools are public domain.
Each item: "T1A01 (C) [97.1]", the question, answers A-D, "~~".

World factual Choice over the answer texts (readable keys), truth = the keyed letter. Shared mmlu snap filter:
no figure or computation stems ("Figure T-1", "What is the value..."), no numeric answers (frequencies, powers,
lengths), no numbered-statement combos; a wrong "All these choices are correct" is removed, and the item dropped
when it is the right one. Near-duplicates across pools merged (the lower class wins). node_hint by subelement.
"""

from __future__ import annotations

import html
import importlib.util
import re
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "ham_radio_pools"
LICENSE = "Public domain (NCVEC question pools for FCC amateur radio license exams)"
TARGET = env_int("TARGET_HAM_RADIO_POOLS", 5000)
SALT = "ham-radio-pools-20260926"
BASE = "http://ncvec.org/downloads/"
POOLS = {  # local name -> (class, published file)
    "technician.docx": ("Technician", "2026-2030 Technician Pool and Syllabus Public Release Feb 19 2026.docx"),
    "general.docx": ("General", "General Class Pool and Syllabus 2023-2027 Public Release with 6th Errata Feb 4 2026.docx"),
    "extra.docx": ("Amateur Extra",
                   "2024-2028 Extra Class Question Pool and Syllabus Public Release with 4th Errata Feb 4 2026.docx"),
}
RADIO = "world.tech.telecom_networks.radio"
# subelement digit -> node (T/G/E share the syllabus layout except T7, station equipment).
SUBELEMENT_NODE = {
    "0": "world.tech.engineering_inventions.electrical_general",  # electrical and RF safety
    "1": RADIO,  # Commission's rules
    "2": RADIO,  # operating procedures
    "3": RADIO,  # propagation (+ Technician antennas basics)
    "4": RADIO,  # amateur practices / station setup
    "5": "world.science.physics.electricity",  # electrical principles
    "6": "world.tech.engineering_inventions.electronics",  # circuit components
    "7": "world.tech.engineering_inventions.electronics",  # practical circuits
    "8": "world.tech.telecom_networks.telecommunications",  # signals, modulation, digital modes
    "9": RADIO,  # antennas and feed lines
}
HEAD = re.compile(r"^([TGE]\d[A-Z]\d{2})\s*\(([A-D])\)")
ANSWER = re.compile(r"^([A-D])\.\s*(.*)$")
FIGURE = re.compile(r"\bfigures?\s+[TGE]\d", re.I)
POOL_REF = re.compile(r"^\s*(all|none) (of )?these (choices )?(are|is) correct\.?\s*$", re.I)

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fetch(raw_dir: Path) -> None:
    for local, (_, remote) in POOLS.items():
        out = raw_dir / local
        if out.exists():
            continue
        r = httpx.get(BASE + remote.replace(" ", "%20"), follow_redirects=True, timeout=180)
        r.raise_for_status()
        out.write_bytes(r.content)


def _paragraphs(path: Path) -> list[str]:
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        p = re.sub(r"<w:tab/>", " ", p)
        t = M.clean(html.unescape(re.sub(r"<[^>]+>", "", p)))
        if t:
            out.append(t)
    return out


def _items(path: Path) -> Iterator[dict]:
    paras = _paragraphs(path)
    for i, p in enumerate(paras):
        m = HEAD.match(p)
        if not m or i + 6 > len(paras):
            continue
        q, block = paras[i + 1], paras[i + 2 : i + 6]
        answers = [ANSWER.match(b) for b in block]
        if any(a is None for a in answers) or [a.group(1) for a in answers] != list("ABCD"):
            continue
        yield {"qid": m.group(1), "letter": m.group(2), "q": q, "answers": [a.group(2).strip() for a in answers]}


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    for local, (klass, _) in POOLS.items():
        for it in _items(raw_dir / local):
            if FIGURE.search(it["q"]):
                continue
            answers, correct = it["answers"], "ABCD".index(it["letter"])
            if POOL_REF.match(answers[correct]):
                continue
            keep = [i for i, a in enumerate(answers) if not POOL_REF.match(a)]
            answers, correct = [answers[i] for i in keep], keep.index(correct)
            kept = M.snap_filter(it["q"], answers, correct)
            if not kept:
                continue
            k = M.item_key(it["q"], kept[0][kept[1]])
            if k in seen:
                continue
            seen.add(k)
            pool.append({**it, "class": klass, "answers": kept[0], "correct": kept[1], "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    return hash_order(_pool(raw_dir), lambda x: x["qid"], SALT)[:TARGET]


def _node(qid: str) -> str:
    return RADIO if qid.startswith("T7") else SUBELEMENT_NODE[qid[1]]


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: x["qid"]):
        text, origin = M.completion_text(it["q"])
        meta = {"exam": f"FCC {it['class']} class", "pool_id": it["qid"], "subelement": it["qid"][:2]}
        fl = M.flags(" ".join([it["q"], *it["answers"]]))
        if fl:
            meta["flags"] = fl
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"],
                              node=_node(it["qid"]), item_id=it["qid"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
