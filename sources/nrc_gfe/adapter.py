"""NRC Generic Fundamentals Examination (GFE) question banks: PWR and BWR reactor-operator licensing questions.

The US Nuclear Regulatory Commission publishes the whole GFE question bank (November 2020, the final edition;
the GFE now runs from the bank) for pressurized- and boiling-water reactors: components (valves, sensors, pumps,
motors, heat exchangers, breakers), reactor theory, and thermodynamics, each with its answer. US federal
government work: public domain. Text via poppler's pdftotext (-layout), page headers/footers stripped.

World factual Choice over the answer texts (readable keys), truth = the keyed letter. Most of the bank is
computation (steam tables, given-parameter problems) and drops out through the shared mmlu snap filter (no "="
or computation stems, no numeric answers) plus: no drawing/figure/graph items, no two-column tabular answers.
The PWR and BWR banks share many questions (the QID cross-references them); near-duplicates are merged, PWR first.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "nrc_gfe"
LICENSE = "Public domain (US federal government work, US Nuclear Regulatory Commission)"
TARGET = env_int("TARGET_NRC_GFE", 5000)
SALT = "nrc-gfe-20260926"
BASE = ("https://www.nrc.gov/sites/default/files/doc_library/cdn/legacy/reactors/operator-licensing/"
        "history-rulemaking-activities/generic-fundamentals-examinations/")
BANKS = {"pwr": BASE + "pwr/pwr-files/pwr-bank.pdf", "bwr": BASE + "bwr/bwr-files/bwr-bank.pdf"}

NUCLEAR = "world.tech.engineering_inventions.nuclear_power"
MECH = "world.tech.engineering_inventions.mechanical_engineering"
ELEC = "world.tech.engineering_inventions.electrical_engineering"
# topic (last three digits after the 19x/29x prefix) -> node; x91 components, x92 reactor theory, x93 thermo.
COMPONENT_NODE = {"001": MECH, "002": "world.tech.engineering_inventions.optics_instruments", "003": MECH,
                  "004": MECH, "005": ELEC, "006": MECH, "007": NUCLEAR, "008": ELEC}

PAGE_JUNK = re.compile(r"^\s*(-\s*\d+\s*-.*|NRC Generic Fundamentals Examination Question Bank.*|"
                       r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                       r"\s+\d{4})\s*$")
FIG = re.compile(r"\b(figure|drawing|graph|curve|table|chart|shown|see below|sketch)\b", re.I)
OPTION = re.compile(r"^([A-D])\.\s+(.*)$")

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fetch(raw_dir: Path) -> None:
    for bank, url in BANKS.items():
        pdf, txt = raw_dir / f"{bank}-bank.pdf", raw_dir / f"{bank}-bank.txt"
        if not pdf.exists():
            r = httpx.get(url, follow_redirects=True, timeout=600)
            r.raise_for_status()
            pdf.write_bytes(r.content)
        if not txt.exists():
            subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)


def _join(lines: list[str]) -> str:
    return M.clean(" ".join(l.strip() for l in lines if l.strip()))


def _items(path: Path, bank: str) -> Iterator[dict]:
    lines = [l for l in path.read_text().splitlines() if not PAGE_JUNK.match(l)]
    text = "\n".join(lines)
    for block in re.split(r"\n(?=TOPIC:)", text):
        head = re.search(r"TOPIC:\s*(\d{6}).*?QID:\s*([PB]\d+)", block, re.S)
        ans = re.search(r"\nANSWER:\s*([A-D])", block)
        if not head or not ans:
            continue
        body = block[block.index("\n", block.index("QID:")) :].split("\nANSWER:")[0].strip("\n")
        stem, opts, cur = [], {}, None
        for l in body.splitlines():
            m = OPTION.match(l)
            if m and m.group(1) == "ABCD"[len(opts)]:
                cur = m.group(1)
                opts[cur] = [m.group(2)]
            elif cur:
                opts[cur].append(l)
            else:
                stem.append(l)
        if list(opts) != list("ABCD"):
            continue
        raw_opts = ["\n".join(opts[k]).strip() for k in "ABCD"]
        yield {"id": f"{bank}:{head.group(2)}", "topic": head.group(1), "stem_lines": stem,
               "q": _join(stem), "raw_opts": raw_opts, "answers": [_join(o.splitlines()) for o in raw_opts],
               "letter": ans.group(1), "bank": bank}


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    for bank in BANKS:
        for it in _items(raw_dir / f"{bank}-bank.txt", bank):
            if FIG.search(it["q"]) or any(re.search(r"\S {3,}\S", o) for o in it["raw_opts"]):
                continue
            if any(re.search(r"\S {3,}\S", l.strip()) for l in it["stem_lines"]):
                continue  # aligned "given" tables and column headers
            kept = M.snap_filter(it["q"], it["answers"], "ABCD".index(it["letter"]))
            if not kept:
                continue
            k = M.item_key(it["q"], kept[0][kept[1]])
            if k in seen:
                continue
            seen.add(k)
            pool.append({**it, "answers": kept[0], "correct": kept[1], "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    return hash_order(_pool(raw_dir), lambda x: x["id"], SALT)[:TARGET]


def _node(topic: str) -> str:
    area, sub = topic[1:3], topic[3:]
    if area == "91":
        return COMPONENT_NODE.get(sub, MECH)
    if area == "92" or sub in ("009", "010"):  # reactor theory; core thermal limits; vessel brittle fracture
        return NUCLEAR
    if sub == "006":  # fluid statics and dynamics
        return "world.science.physics.liquid"
    return "world.science.physics.thermodynamics"


TRAIL = re.compile(r"(\.\.\.|…)\s*$")
ASSUME = re.compile(r"^(.*?)\s*(\([^()]*\))\s*$", re.S)


def _text(stem: str) -> tuple[str, str]:
    """A trailing "(Assume ...)" note stays after the question; a stem that stops on ":" reads as a completion."""
    stem = TRAIL.sub(" ...", stem)
    note = ""
    m = ASSUME.match(stem)
    if m and m.group(1):
        stem, note = m.group(1), " " + m.group(2)
    if re.search(r":\s*$", stem):
        stem = re.sub(r"\s*:\s*$", " ...", stem)
    text, origin = M.completion_text(stem)
    return text + note, origin


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: x["id"]):
        q = it["q"]
        text, origin = _text(q)
        meta = {"exam": f"NRC Generic Fundamentals Examination ({it['bank'].upper()})", "topic": it["topic"]}
        fl = M.flags(" ".join([q, *it["answers"]]))
        if fl:
            meta["flags"] = fl
        out = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"],
                                node=_node(it["topic"]), item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if out:
            yield out
