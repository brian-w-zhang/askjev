"""Johnson's IPIP-NEO response data (OSF tbmh5): per-item answer shares that anchor EXISTING `ipip` questions.

This source creates no questions. `normalize()` yields nothing; the work is `build()`, which writes
`data/normalized/ipip_neo_norms_dists.jsonl`: one row per (existing ipip question id, population) with the share of
respondents at each of the five levels. `scripts/attach_human_dists.py <file>` inserts the rows into `human_dists`.

    uv run python sources/ipip_neo_norms/adapter.py      # fetch + build the dists file

Data (public, no login): IPIP300.dat (N=307,313; Johnson 2014, J. Research in Personality 51) and IPIP120.dat
(N=619,150), web administrations of the IPIP-NEO-300 and IPIP-NEO-120. Items are coded 1-5 (Very Inaccurate ..
Very Accurate), 0 = missing; reverse-keyed items were stored reverse-scored, so they are flipped back (6 - v) to the
raw response before counting. Item order and keys come from Johnson's IPIP-NEO-300 scoring tool and the printable
questionnaires (same OSF project). Levels "0".."4" match the ipip Score levels ("does not describe me at all" ..
"describes me very well"). Question ids are taken from the ipip adapter itself (imported and run over its whole
item pool), matched on the statement text.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import orjson

from askjev.model import Question

NAME = "ipip_neo_norms"
LICENSE = "IPIP items public domain; IPIP-NEO data shared openly by J. A. Johnson on OSF (no license stated)"
OSF = "https://osf.io/download/{}/"
FILES = {
    "IPIP300.dat": "jdu2v",
    "IPIP120.dat": "q9jrh",
    "DAT300.doc": "2kfhe",
    "DAT120.doc": "hgm7n",
    "IPIP-NEO-300-scoring-tool.xlsx": "4w86n",
    "IPIP-NEO-300-Questionnaire.docx": "xzje4",
    "IPIP-NEO-120-Questionnaire.docx": "uf6dg",
}
# (file, items, first item column (0-based), population)
INSTRUMENTS = [
    ("IPIP300.dat", 300, 33, "IPIP-NEO-300 web respondents (Johnson)", "IPIP-NEO-300-Questionnaire.docx"),
    ("IPIP120.dat", 120, 31, "IPIP-NEO-120 web respondents (Johnson)", "IPIP-NEO-120-Questionnaire.docx"),
]
SOURCE = "Johnson IPIP-NEO data repository (OSF tbmh5), {}; 1=Very Inaccurate..5=Very Accurate mapped to levels 0-4"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "normalized" / "ipip_neo_norms_dists.jsonl"


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, key in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        with httpx.stream("GET", OSF.format(key), follow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)


def normalize(raw_dir: Path) -> Iterator[Question]:
    """No questions: this source only attaches norms to existing ipip questions (see build())."""
    return iter(())


def _docx_items(path: Path) -> dict[int, str]:
    x = zipfile.ZipFile(path).read("word/document.xml").decode()
    paras = [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<w:p[ >].*?</w:p>", x)]
    paras = [p for p in paras if p]
    out: dict[int, str] = {}
    for i, p in enumerate(paras[:-1]):
        if re.fullmatch(r"\d{1,3}", p) and re.search(r"[a-z]", paras[i + 1]):
            out.setdefault(int(p), paras[i + 1])
    return out


def _signs(raw_dir: Path) -> dict[str, str]:
    """Item text -> '+'/'-' from the IPIP-NEO-300 scoring tool (Sign column like '+N1' / '-A2')."""
    import openpyxl

    ws = openpyxl.load_workbook(raw_dir / "IPIP-NEO-300-scoring-tool.xlsx", read_only=True)["Input"]
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] and row[1] and row[4]:
            out[_key(row[4])] = row[1][0]
    return out


def _key(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("’", "'").replace("'", "")).strip()


def _counts(path: Path, n_items: int, start: int) -> tuple[np.ndarray, str]:
    """(n_items, 6) counts of codes 0..5 per item, and the year range."""
    lines = path.read_bytes().splitlines()
    width = start + n_items
    arr = np.frombuffer(b"".join(ln[:width].ljust(width) for ln in lines), dtype=np.uint8).reshape(len(lines), width)
    codes = arr[:, start:].astype(np.int16) - ord("0")
    bad = (codes < 0) | (codes > 5)
    codes[bad] = 0
    counts = np.stack([(codes == v).sum(0) for v in range(6)], axis=1)
    yr = arr[:, 19:22]  # YEAR, columns 20-22 in both files (years since 1900)
    years = sorted(y for y in (int(b) + 1900 for b in (bytes(r).strip() for r in yr) if b.isdigit()) if y >= 1990)
    # The 2nd..98th percentile, so a handful of bad clock values do not stretch the range.
    return counts, f"{years[len(years) // 50]}-{years[-len(years) // 50]}" if years else ""


def _ipip_questions() -> dict[str, Question]:
    """Every question the ipip adapter can emit (whole pool), by normalized statement text."""
    spec = importlib.util.spec_from_file_location("sources.ipip", ROOT / "sources" / "ipip" / "adapter.py")
    old = os.environ.get("ASKJEV_TARGET_IPIP")
    os.environ["ASKJEV_TARGET_IPIP"] = "100000"
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        qs = list(mod.normalize(ROOT / "data" / "raw" / "ipip"))
    finally:
        if old is None:
            os.environ.pop("ASKJEV_TARGET_IPIP", None)
        else:
            os.environ["ASKJEV_TARGET_IPIP"] = old
    out: dict[str, Question] = {}
    for q in qs:
        m = re.match(r'How well does this statement describe you: "I (.+)"$', q.text)
        if m:
            out.setdefault(_key(m.group(1)), q)
    return out, mod


def build(raw_dir: Path, out: Path = OUT) -> dict:
    signs = _signs(raw_dir)
    ipip, mod = _ipip_questions()
    rows, anchored, missing = [], set(), []
    for fname, n_items, start, pop, docx in INSTRUMENTS:
        items = _docx_items(raw_dir / docx)
        counts, years = _counts(raw_dir / fname, n_items, start)
        for i in range(1, n_items + 1):
            stem = items[i]
            sentence = mod._sentence(stem)
            k = _key(sentence[2:])
            q = ipip.get(k)
            sign = signs.get(_key(stem)) or (q.meta.get("keyed") if q else None)
            if q is None or sign not in ("+", "-"):
                missing.append((fname, i, stem))
                continue
            c = counts[i - 1, 1:].astype(float)  # codes 1..5 (stored, reverse-scored for '-' items)
            if sign == "-":
                c = c[::-1]  # stored 5 = raw 1 ... stored 1 = raw 5
            n = int(c.sum())
            dist = {str(j): round(float(c[j] / n), 6) for j in range(5)}
            rows.append({"question_id": q.id, "population": pop, "distribution": dist, "n": n,
                         "source": SOURCE.format(fname), "wave": years,
                         "item": f"{fname.removesuffix('.dat')}#{i}", "keyed": sign, "statement": sentence})
            anchored.add(q.id)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        for r in rows:
            fh.write(orjson.dumps(r) + b"\n")
    return {"rows": len(rows), "questions": len(anchored), "missing": missing}


if __name__ == "__main__":
    raw = ROOT / "data" / "raw" / NAME
    fetch(raw)
    res = build(raw)
    print(f"{NAME}: {res['rows']} rows, {res['questions']} ipip questions anchored -> {OUT}")
    for m in res["missing"]:
        print("  unmatched:", m, file=sys.stderr)
