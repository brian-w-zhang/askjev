"""How many people know it? Tauber et al. 2013 general-knowledge norms.

Human data: Tauber, Dunlosky, Rawson, Rhodes & Sitzman (2013), "General knowledge norms: Updated and expanded from the
Nelson and Narens (1980) norms", Behavior Research Methods 45:1115-1143 (doi 10.3758/s13428-012-0307-9): 299
questions answered with no choices (free recall) by about 670 US college students, with the share who recalled the
answer. The paper's appendix table isn't openly downloadable; the per-item shares come from a public transcription
(ehsankia.com/quiz, quiz.js: question, answer, percent recalled), checked here against the item ranks the German
update reprints for the same 299 questions (Buchin & Mulligan-style German norms, PLOS ONE 2023,
doi 10.1371/journal.pone.0281305, S1 Table, CC BY 4.0): Spearman 0.99 over the 290 items matched by text. Question
wording and casing come from that S1 table where matched.

Jev is asked what share of the students came up with the answer (12 bins, finer below 10%); the question and its answer
are shown, so this measures whether Jev knows how widely known a fact is, not whether it knows the fact.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "recall_norms"
NODE = "world.society.education.general_knowledge_norms"
LICENSE = ("Published research norms (Tauber et al. 2013), per-item values from a public transcription; question text "
           "from PLOS ONE S1 Table (CC BY 4.0); private non-commercial research use")
QUIZ = "https://ehsankia.com/quiz/quiz.js"
S1 = "https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0281305.s007"
EDGES = [0, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # finer at the bottom: most items are rarely recalled
BINS = {f"r{a:02d}": f"{a}-{b}%" for a, b in zip(EDGES, EDGES[1:])}


def _bin(share: float) -> str:
    v = share * 100
    return next(f"r{a:02d}" for a, b in zip(EDGES, EDGES[1:]) if v < b or b == 100)


def fetch(raw_dir: Path) -> None:
    req = lambda u: urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})  # noqa: E731
    if not (raw_dir / "quiz.js").exists():
        (raw_dir / "quiz.js").write_bytes(urllib.request.urlopen(req(QUIZ)).read())
    if not (raw_dir / "s007.xlsx").exists():
        (raw_dir / "s007.xlsx").write_bytes(urllib.request.urlopen(req(S1)).read())


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _s1(raw_dir: Path) -> dict[str, dict]:
    """English question text, answer and Tauber's 2012 rank from the German norms' S1 table (openpyxl, read-only)."""
    import openpyxl

    ws = openpyxl.load_workbook(raw_dir / "s007.xlsx", read_only=True).worksheets[1]
    out = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        r12, q, a, p20 = row[1], row[5], row[6], row[7]
        if isinstance(r12, (int, float)) and q:
            out[_norm(str(q))] = {"q": str(q).strip(), "a": str(a).strip(), "rank_2012": int(r12),
                                  "german_2020": float(p20) if isinstance(p20, (int, float)) else None}
    return out


CASE = {  # the transcription is upper case; these items aren't in the S1 table, so proper nouns are restored by hand
    "u.s.": "U.S.", "greek": "Greek", "bonn": "Bonn", "jules verne": "Jules Verne",
    "20,000 leagues beneath the sea": "20,000 Leagues Beneath the Sea",
}


def _case(q: str) -> str:
    t = q.capitalize()
    for a, b in CASE.items():
        t = t.replace(a, b)
    return t


def _fuzzy(q: str, s1: dict[str, dict]) -> dict | None:
    """Items whose text differs only in punctuation or a word between the two sources (difflib ratio >= 0.9)."""
    from difflib import SequenceMatcher

    k = _norm(q)
    best = max(s1, key=lambda x: SequenceMatcher(None, k, x).ratio())
    return s1[best] if SequenceMatcher(None, k, best).ratio() >= 0.9 else None


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = re.findall(r'\["(.*?)", "(.*?)", ([\d.]+)\]', (raw_dir / "quiz.js").read_text())
    s1 = _s1(raw_dir)
    for q, a, p in rows:
        m = s1.get(_norm(q)) or _fuzzy(q, s1)
        text = m["q"] if m else _case(q)
        ans = m["a"] if m else a.title()
        share = float(p) / 100
        yield Question(
            text=f'In a 2012 study, US college students were asked this question with no answer choices: "{text}" '
                 f'(The answer is: {ans}.) What share of the students came up with the answer?',
            primitive="choice", hemisphere="world", kind="factual", origin="dataset", source=NAME, options=BINS,
            node_hint=NODE, license=LICENSE, source_item_id=_norm(q), truth=_bin(share),
            meta={"experiment": "recall_norms", "recall_2012": share, "answer": ans, "rank_2012": m["rank_2012"] if m else None,
                  "german_2020": m["german_2020"] if m else None, "ordered": True})
