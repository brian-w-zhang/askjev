"""Idioms: how familiar, how plausible taken literally, and how people finish them (research pass 2, idea 2).

Human data: Bulkes & Tanner 2017, "'Going to town': Large-scale norming and statistical analysis of 870 American
English idioms" (Behavior Research Methods 49:772-783), electronic supplementary material 1 (Springer). About 100
US adults rated each idiom per dimension. Familiarity and literal plausibility are published as means on 1-5 (kept
in meta). Predictability is a completion task: people saw the idiom without its last word and wrote one word; the
file lists every completion with its count, which gives a real distribution.

The same 200 idioms, sampled evenly over the range of familiarity, get three questions: familiarity and literal
plausibility (five described levels; the descriptions are this project's, anchored on the study's 1-5 scales) and
completion (a Choice over the expected word, up to five other completions people gave at least twice, and
"another word").
"""

from __future__ import annotations

import random
import re
import urllib.request
from pathlib import Path
from typing import Iterator

import openpyxl

from askjev.model import HumanDist, Question

NAME = "idiom_norms"
NODE = "world.society.languages.word.idioms"
LICENSE = "Published research data (Bulkes & Tanner 2017, BRM supplementary material); no license stated; used for non-commercial research"
URL = "https://static-content.springer.com/esm/art%3A10.3758%2Fs13428-016-0747-8/MediaObjects/13428_2016_747_MOESM1_ESM.xlsx"
FILE = "bulkes_tanner_2017.xlsx"
N = 200
FAMILIAR = ["I have never come across it: it means nothing to me",
            "I may have seen it once or twice, but I'm not sure what it means",
            "I have come across it now and then",
            "I hear or read it fairly often",
            "I know it very well: it comes up all the time"]
LITERAL = ["Taken word for word it makes no sense at all",
           "Taken word for word it is very hard to picture",
           "Taken word for word it could happen, but only in odd circumstances",
           "Taken word for word it describes something that could easily happen",
           "Taken word for word it describes something ordinary and common"]


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / FILE).exists():
        urllib.request.urlretrieve(URL, raw_dir / FILE)


def _count(cell) -> int | None:
    m = re.match(r"=(\d+)/B\d+", str(cell or ""))
    return int(m.group(1)) if m else (int(cell) if isinstance(cell, (int, float)) else None)


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50] or "blank"


def _sheet(wb, name: str) -> dict[str, tuple]:
    return {r[0].strip(): r for r in list(wb[name].iter_rows(values_only=True))[1:] if r and r[0]}


def normalize(raw_dir: Path) -> Iterator[Question]:
    wb = openpyxl.load_workbook(raw_dir / FILE, read_only=True)
    fam, lit, pred = _sheet(wb, "FAMILIARITY"), _sheet(wb, "LITERAL PLAUSIBILITY"), _sheet(wb, "PREDICTABILITY")
    idioms = sorted((i for i in fam if i in lit and i in pred and isinstance(fam[i][2], (int, float))),
                    key=lambda i: (fam[i][2], i))
    k = len(idioms) / N
    rng = random.Random(2017)
    picks = sorted({idioms[min(len(idioms) - 1, int(j * k + rng.random() * k))] for j in range(N)})
    for idiom in picks:
        f, l_, p = fam[idiom], lit[idiom], pred[idiom]
        meta = {"idiom": idiom, "familiarity": float(f[2]), "literal_plausibility": float(l_[2])}
        yield Question(
            text=f'How familiar is the idiom "{idiom}"?', primitive="score", hemisphere="world", kind="perception",
            origin="dataset", source=NAME, options=FAMILIAR, node_hint=NODE, license=LICENSE,
            source_item_id=f"familiarity:{idiom}",
            meta={"experiment": "idioms", "set": "familiarity", **meta, "human_mean": float(f[2]), "human_n": f[1]})
        yield Question(
            text=f'Taken literally, word for word, how plausible is "{idiom}"?', primitive="score", hemisphere="world",
            kind="perception", origin="dataset", source=NAME, options=LITERAL, node_hint=NODE, license=LICENSE,
            source_item_id=f"literal:{idiom}",
            meta={"experiment": "idioms", "set": "literal", **meta, "human_mean": float(l_[2]), "human_n": l_[1]})
        words = idiom.split()
        expected = re.sub(r"[^\w'-]", "", words[-1])
        n, hit = p[1], _count(p[2])
        others = [(str(p[i]).strip(), _count(p[i + 1])) for i in range(4, len(p) - 1, 2) if p[i] and _count(p[i + 1])]
        others = sorted((o for o in others if o[1] >= 2 and _key(o[0]) != _key(expected)), key=lambda o: (-o[1], o[0]))[:5]
        if not n or hit is None or len(words) < 3:
            continue
        opts = {_key(expected): expected, **{_key(w): w for w, _ in others}, "another_word": "Another word"}
        dist = {_key(expected): hit / n, **{_key(w): c / n for w, c in others}}
        dist["another_word"] = max(0.0, 1 - sum(dist.values()))
        stem = " ".join(words[:-1]) + " ___"
        yield Question(
            text=f'Finish this idiom with one word: "{stem}"', primitive="choice", hemisphere="world", kind="perception",
            origin="dataset", source=NAME, options=opts, node_hint=NODE, license=LICENSE, truth=_key(expected),
            source_item_id=f"completion:{idiom}",
            human=[HumanDist(population="US adults (Bulkes & Tanner 2017)", distribution=dist, n=int(n),
                             source="Predictability sheet: one-word completions of the idiom without its last word")],
            meta={"experiment": "idioms", "set": "completion", **meta, "expected": expected,
                  "expected_share": hit / n})
