"""O*NET work activities as career-interest Scores: "How much would you enjoy this work activity: "<activity>"?".

Three pools from the O*NET 31.0 database (CSV files, no login), taken in this order so a larger target only
appends rows:
1. Interest Profiler illustrative activities (interests_illustrative_activities.csv): every item, tagged with its
   RIASEC career type or O*NET "specific interest area".
2. Detailed Work Activities (gwas_to_iwas_to_dwas.csv): every plain one.
3. Occupation task statements (task_statements.csv): plain ones, Core before Supplemental, then salted-hash order,
   up to the target. Tagged with the occupation and its top RIASEC interest (career_interest_types.csv).

Same 5 enjoyment levels and wording as the openpsych RIASEC items; items whose text already appears there are
skipped (they would be the same question). No human distribution and no truth.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int

NAME = "onet_interests"
BASE = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/"
FILES = [
    "interests_illustrative_activities.csv",
    "gwas_to_iwas_to_dwas.csv",
    "task_statements.csv",
    "career_interest_types.csv",
]
LICENSE = (
    "CC BY 4.0: O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration "
    "(USDOL/ETA). Used under the CC BY 4.0 license. O*NET is a trademark of USDOL/ETA."
)
TARGET = env_int("TARGET_ONET_INTERESTS", 5000)
SALT = "onet_interests-20260924"
MAX_CHARS = 100
MAX_WORD = 12

TEXT = 'How much would you enjoy this work activity: "{s}"'
HUMAN = 'How much would most people enjoy this work activity: "{s}"'
ENJOY5 = [  # identical to sources/openpsych ENJOY5
    "I would dislike doing this",
    "I would somewhat dislike doing this",
    "I would feel neutral about doing this",
    "I would somewhat enjoy doing this",
    "I would enjoy doing this",
]
RIASEC = {"1.B.1.a": "Realistic", "1.B.1.b": "Investigative", "1.B.1.c": "Artistic", "1.B.1.d": "Social",
          "1.B.1.e": "Enterprising", "1.B.1.f": "Conventional"}

JARGON = re.compile(r"[()\d;/:\"&]|\b[A-Z]{2,}\b|such as|\betc\b|\be\.g\b")
POLITICAL = re.compile(r"(?i)\b(politic\w*|campaign for|election\w*|lobby\w*|legislat\w*|religio\w*|church|worship)\b")
SENSITIVE = re.compile(r"(?i)\b(autops\w*|embalm\w*|corpses?|cadavers?|slaughter\w*|euthan\w*|remains of the dead)\b")


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().rstrip(".").strip()


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _plain(s: str) -> bool:
    words = re.findall(r"[A-Za-z'-]+", s)
    return (
        bool(words) and len(s) <= MAX_CHARS and not JARGON.search(s) and s.count(",") <= 1
        and max(len(w) for w in words) <= MAX_WORD
    )


def _existing(raw_dir: Path) -> set[str]:
    """Activity texts already asked by openpsych's RIASEC items (same question text)."""
    p = raw_dir.parents[1] / "normalized" / "openpsych.jsonl"
    if not p.exists():
        return set()
    out = set()
    pat = re.compile(r'enjoy this work activity: \\"(.*?)\\"')
    for line in p.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            out.add(_key(m.group(1)))
    return out


def _h(s: str) -> str:
    return hashlib.sha256(f"{SALT}|{s}".encode()).hexdigest()


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen = _existing(raw_dir)
    items: list[tuple[str, str, dict]] = []  # (activity, source_item_id, meta)

    def add(text: str, sid: str, meta: dict) -> None:
        k = _key(text)
        if k in seen:
            return
        seen.add(k)
        items.append((text, sid, meta))

    # 1. Interest Profiler illustrative activities (all).
    for r in _rows(raw_dir / FILES[0]):
        s = _clean(r["Activity"])
        if s:
            add(s, f"ip:{r['Element ID']}:{_key(s)[:60]}",
                {"pool": "illustrative_activity", "interest": r["Element Name"], "interest_type": r["Interest Type"]})

    # 2. Detailed Work Activities (all plain ones), in DWA id order.
    dwas = {}
    for r in _rows(raw_dir / FILES[1]):
        dwas.setdefault(r["DWA Element ID"], r)
    for did in sorted(dwas):
        r = dwas[did]
        s = _clean(r["DWA Element Name"])
        if _plain(s):
            add(s, f"dwa:{did}", {"pool": "dwa", "gwa": r["GWA Element Name"]})

    # 3. Task statements: plain, Core first, salted-hash order.
    top: dict[str, tuple[float, str]] = {}
    for r in _rows(raw_dir / FILES[3]):
        if r["Scale ID"] == "OI" and r["Element ID"] in RIASEC:
            v = float(r["Data Value"])
            if v > top.get(r["O*NET-SOC Code"], (-1.0, ""))[0]:
                top[r["O*NET-SOC Code"]] = (v, RIASEC[r["Element ID"]])
    tasks = [r for r in _rows(raw_dir / FILES[2]) if _plain(_clean(r["Task"]))]
    tasks.sort(key=lambda r: (r["Task Type"] != "Core", _h(r["Task ID"])))
    for r in tasks:
        if len(items) >= TARGET:
            break
        add(_clean(r["Task"]), f"task:{r['Task ID']}",
            {"pool": "task", "occupation": r["Title"], "soc": r["O*NET-SOC Code"], "task_type": r["Task Type"] or None,
             "interest": top.get(r["O*NET-SOC Code"], (0, None))[1]})

    for s, sid, meta in items[:TARGET]:
        flags = []
        if POLITICAL.search(s):
            flags.append("political")
        if SENSITIVE.search(s):
            flags.append("sensitive")
        yield Question(
            text=TEXT.format(s=s),
            primitive="score",
            hemisphere="self",
            kind="personality",
            origin="template",
            source=NAME,
            options=ENJOY5,
            node_hint="self.personality.interests",
            human_text=HUMAN.format(s=s),
            source_item_id=sid,
            license=LICENSE,
            template_id="onet_interests.enjoy",
            meta=meta | ({"flags": flags} if flags else {}),
        )
