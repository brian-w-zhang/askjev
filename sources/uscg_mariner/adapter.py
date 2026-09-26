"""USCG merchant mariner sample exams (National Maritime Center): deck, navigation, rules of the road, engineering.

The NMC publishes one "sample examination" PDF per exam module (Q100 Rules of the Road ... Q808 Pumpman), each a
real draw from the question bank with the answer marked ("If choice B is selected set score to 1."). US federal
government work: public domain. dco.uscg.mil refuses scripted downloads (Akamai 403), so the PDFs come from the
Internet Archive's copies of the same URLs: the latest capture of each file at or before CUTOFF, listed once from
the Wayback CDX API and saved (cdx.json) so reruns read the same files. Navigation-problem / chart / stability-
problem modules are skipped outright (they are computation over charts and tables). Text via poppler's pdftotext.

World factual Choice over the answer texts (readable keys), truth = the marked answer. Shared mmlu snap filter: no
illustration or computation stems, no numeric answers, no "all of the above" as the right answer. Questions repeat
across modules; near-duplicates are merged (first module wins).
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "uscg_mariner"
LICENSE = "Public domain (US federal government work, USCG National Maritime Center)"
TARGET = env_int("TARGET_USCG_MARINER", 5000)
SALT = "uscg-mariner-20260926"
CUTOFF = "20260301000000"
CDX = ("https://web.archive.org/cdx/search/cdx?url=dco.uscg.mil/Portals/9/NMC/pdfs/examinations/*"
       "&output=json&fl=original,timestamp,statuscode&filter=statuscode:200")
SKIP_FILE = re.compile(r"problem|chart", re.I)

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def _files(raw_dir: Path) -> dict[str, tuple[str, str]]:
    """exam file name -> (timestamp, original url): latest capture at or before CUTOFF."""
    cdx = raw_dir / "cdx.json"
    if not cdx.exists():
        r = httpx.get(CDX, timeout=120, follow_redirects=True)
        r.raise_for_status()
        cdx.write_text(r.text)
    best: dict[str, tuple[str, str]] = {}
    for orig, ts, _ in json.loads(cdx.read_text())[1:]:
        url = orig.split("?")[0]
        fn = url.rsplit("/", 1)[-1].lower()
        if not re.match(r"q\d{3}", fn) or not fn.endswith(".pdf") or SKIP_FILE.search(fn) or ts > CUTOFF:
            continue
        if fn not in best or ts > best[fn][0]:
            best[fn] = (ts, url)
    return best


def fetch(raw_dir: Path) -> None:
    pdf_dir, txt_dir = raw_dir / "pdf", raw_dir / "txt"
    pdf_dir.mkdir(exist_ok=True)
    txt_dir.mkdir(exist_ok=True)
    with httpx.Client(timeout=180, follow_redirects=True, headers={"User-Agent": "askjev research fetch"}) as c:
        for fn, (ts, url) in sorted(_files(raw_dir).items()):
            pdf, txt = pdf_dir / fn, txt_dir / (fn[:-4] + ".txt")
            if not pdf.exists():
                for attempt in range(4):
                    try:
                        r = c.get(f"https://web.archive.org/web/{ts}id_/{url}")
                        if r.status_code == 200 and r.content[:4] == b"%PDF":
                            pdf.write_bytes(r.content)
                        break
                    except httpx.HTTPError:
                        time.sleep(10 * (attempt + 1))
                time.sleep(1.5)
            if pdf.exists() and not txt.exists():
                subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)


SHIP = "world.tech.vehicles.ship"
ENGINE = "world.tech.engineering_inventions.machines_engines"
# file-name keyword -> node, first match wins
FILE_NODE = [
    (r"electric", "world.tech.engineering_inventions.electrical_engineering"),
    (r"refrigerat", "world.tech.engineering_inventions.mechanical_engineering"),
    (r"motor_plant|steam_plant|gas_turbine|junior_engineer|oiler|fireman|machinist|pump", ENGINE),
    (r"q5\d\d_general_subjects|q6\d\d_general_subjects|q7\d\d_general_subjects|general_subjects",
     "world.tech.engineering_inventions.mechanical_engineering"),
    (r"nav_general|navigation_general|nav-general|nav_gen_", "world.tech.engineering_inventions.navigation"),
]
RULE_SCOPE = [
    (re.compile(r"^\s*INLAND ONLY\s+"), "Under the U.S. Inland Navigation Rules: "),
    (re.compile(r"^\s*INTERNATIONAL ONLY\s+"), "Under the International Navigation Rules (COLREGS): "),
    (re.compile(r"^\s*BOTH INTERNATIONAL (&|AND) INLAND\s+"), "Under both the International and Inland Navigation Rules: "),
]
HEADER_START = re.compile(r"Page \d+ of \d+\s*$")
HEADER_END = re.compile(r"^\s*Illustrations:\s*\d+\s*$")
INSTRUCTION = re.compile(r"^\s*(Choose the best answer|NO reference materials|.*reference materials? (are|is) authorized)", re.I)
QSTART = re.compile(r"^\s{0,4}(\d{1,3})\.\s+(\S.*)$")
BULLET_OPT = re.compile(r"^\s*[o•●○]\s+\(([A-D])\)\s*(.*)$")
PLAIN_OPT = re.compile(r"^\s*([A-D])\.\s+(.*)$")
KEY = re.compile(r"If choice ([A-D]) is selected|Correct answer:\s*([A-D])\b", re.I)
MARKED = re.compile(r"^\s*[•●]\s+\(")
# Shared-flag false positives in seamanship text: sextants, signal/grease/line-throwing guns, "executed" (a release
# is executed), the immigration service as the office stowaways are reported to, EEOC's "sex, or national origin".
FLAG_MASK = re.compile(r"sextants?|\bguns?\b|\bexecuted\b|immigration( and naturalization)?( service)?|"
                       r"religion, sex, or national origin", re.I)
ILLUS = re.compile(r"\billustrat\w*|\bdiagram\b|\bsketch\b|\bshown\b|\bfigure\b|\btable\b|\bgraph\b", re.I)


def _lines(path: Path) -> list[str]:
    out, skip = [], False
    for l in path.read_text(errors="replace").splitlines():
        if HEADER_START.search(l):
            skip = True
            continue
        if skip:
            skip = not HEADER_END.match(l)
            continue
        if INSTRUCTION.match(l) or not l.strip():
            continue
        out.append(l)
    return out


def _items(path: Path) -> Iterator[dict]:
    cur: dict | None = None
    def done(it: dict | None):
        if not it or list(it["opts"]) != list("ABCD") or not it["key"]:
            return None
        return it
    for l in _lines(path):
        m = QSTART.match(l)
        if m and (cur is None or cur["key"] or cur["opts"]):
            if (it := done(cur)):
                yield it
            cur = {"n": int(m.group(1)), "stem": [m.group(2)], "opts": {}, "key": None, "marked": None}
            continue
        if cur is None:
            continue
        k = KEY.search(l)
        if k:
            cur["key"] = k.group(1) or k.group(2)
            continue
        o = BULLET_OPT.match(l) or PLAIN_OPT.match(l)
        if o and o.group(1) == "ABCD"[len(cur["opts"])] if len(cur["opts"]) < 4 else False:
            cur["opts"][o.group(1)] = [o.group(2)]
            if MARKED.match(l):
                cur["marked"] = o.group(1)
        elif cur["opts"] and not cur["key"]:
            cur["opts"][list(cur["opts"])[-1]].append(l)
        elif not cur["opts"]:
            cur["stem"].append(l)
    if (it := done(cur)):
        yield it


def _node(fn: str) -> str:
    for pat, node in FILE_NODE:
        if re.search(pat, fn):
            return node
    return SHIP


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    for txt in sorted((raw_dir / "txt").glob("q*.txt")):
        exam = txt.stem
        for it in _items(txt):
            stem = M.clean(" ".join(s.strip() for s in it["stem"]))
            answers = [M.clean(" ".join(s.strip() for s in it["opts"][k])) for k in "ABCD"]
            if it["marked"] and it["marked"] != it["key"]:
                continue  # the bullet and the scoring line disagree: trust neither
            if ILLUS.search(stem) or any(len(a) > 200 for a in answers):
                continue
            scope = ""
            for rx, words in RULE_SCOPE:
                if rx.match(stem):
                    stem, scope = rx.sub("", stem), words
            kept = M.snap_filter(stem, answers, "ABCD".index(it["key"]))
            if not kept:
                continue
            k = M.item_key(scope + stem, kept[0][kept[1]])
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": f"{exam}:{it['n']}", "exam": exam, "q": stem, "scope": scope,
                         "answers": kept[0], "correct": kept[1], "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    return hash_order(_pool(raw_dir), lambda x: x["id"], SALT)[:TARGET]


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: x["id"]):
        text, origin = M.completion_text(it["q"])
        text = it["scope"] + text
        node = _node(it["exam"])
        if node.endswith("navigation"):
            hint = M.science_hint(it["q"], it["answers"][it["correct"]], default=node)
            node = hint if hint.startswith("world.nature.weather_climate") else node
        meta = {"exam": it["exam"]}
        fl = M.flags(FLAG_MASK.sub(" ", " ".join([it["q"], *it["answers"]])))
        if fl:
            meta["flags"] = fl
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=node,
                              item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
