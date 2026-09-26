"""Sound of Shape pseudoword database (McCormick, Kim, List & Nygaard 2015; "SoS PASS", OSF ekpgh).

537 CVCV pseudowords built from American English sounds (real words removed), each heard by ~25 raters on a 1-7
"not pointed .. very pointed" scale and ~27 other raters on a 1-7 "not rounded .. very rounded" scale. The authors
combine the two into one round-to-pointed scale (1 = rounded, 7 = pointed; roundedness answers recoded as 8 - x),
and so do we: each question carries the pooled individual answers from the trial-level sheet, ~52 per item.

Raters only heard the words, so the question gives both the IPA and a plain English respelling ("koh-too"). The
trial sheet has 570 sound files: 62 of the published 537 appear there under a re-recording's file name and are matched
on their segments, the rest are items later dropped and are not asked. /kʊtu/ is listed twice; only the first is. The
workbook's second sheet repeats one participant's session verbatim and is ignored.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "pseudoword_shapes"
FILE = "SoS_Pseudoword_Database.xlsx"
URL = "https://osf.io/download/wnzt5/"
LICENSE = "No explicit license (public OSF project ekpgh, McCormick, Kim, List & Nygaard 2015); research use"
NODE = "world.science.psychology_neuroscience.perception"

TEXT = ('Say the made-up word "{r}" (IPA /{ipa}/) out loud. Does it sound more like a round shape or a pointed '
        'shape to you?')
HUMAN_TEXT = ('Say the made-up word "{r}" (IPA /{ipa}/) out loud. Does it sound more like a round shape or a '
              'pointed shape to most people?')
LEVELS = [
    'It sounds like a smooth, soft blob with no corners at all, like a cloud',
    'It sounds curved and soft, with a corner or two at most',
    'It sounds more like curves than points, though not entirely smooth',
    'It sounds just as much like curves as like points',
    'It sounds more like corners and edges than curves, though not entirely sharp',
    'It sounds angular and sharp, with a curve or two at most',
    'It sounds like a jagged, spiky shape, all sharp points, like a star or broken glass',
]

# IPA (as coded in the database; "I" is the lax vowel /ɪ/) -> English respelling
VOWELS = {"i": "ee", "e": "ay", "o": "oh", "u": "oo", "ʊ": "uu", "I": "ih", "ɪ": "ih", "ɛ": "eh"}
IPA_VOWEL = {"I": "ɪ"}
CONS = {"tʃ": "ch", "dʒ": "j"}
FRONT = {"i", "e", "I", "ɪ", "ɛ"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / FILE
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _sheets(path: Path) -> dict[int, list[dict]]:
    with zipfile.ZipFile(path) as z:
        strings = ["".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t"))
                   for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        out = {}
        for s in (1, 3):
            rows = []
            for row in ET.fromstring(z.read(f"xl/worksheets/sheet{s}.xml")).find("m:sheetData", NS).findall("m:row", NS):
                d = {}
                for c in row.findall("m:c", NS):
                    v = c.find("m:v", NS)
                    if v is not None:
                        d[re.match(r"[A-Z]+", c.get("r")).group(0)] = strings[int(v.text)] if c.get("t") == "s" else v.text
                rows.append(d)
            head = rows[0]
            out[s] = [{head[k]: v for k, v in r.items() if k in head} for r in rows[1:] if r]
    return out


def _cons(c: str, next_vowel: str) -> str:
    if c in CONS:
        return CONS[c]
    if c == "g" and next_vowel in FRONT:
        return "gh"  # keep it hard: "ghee", not "gee"
    return c


def respell(c1: str, v1: str, c2: str, v2: str) -> str:
    return f"{_cons(c1, v1)}{VOWELS[v1]}-{_cons(c2, v2)}{VOWELS[v2]}"


def ipa(c1: str, v1: str, c2: str, v2: str) -> str:
    return "".join(IPA_VOWEL.get(x, x) for x in (c1, v1, c2, v2)).replace("g", "ɡ")


def normalize(raw_dir: Path) -> Iterator[Question]:
    sh = _sheets(raw_dir / FILE)
    answers: dict[str, list[int]] = defaultdict(list)
    n_by_scale: dict[str, Counter] = defaultdict(Counter)
    named = {it["SoundFile"] for it in sh[3]}
    orphan: dict[tuple, str] = {}  # re-recorded items carry a different file name in the trial sheet ("Start-119-3")
    for r in sh[1]:
        if r["SoundFile"] not in named:
            orphan[(r["Position1_C1"], r["Position2_V1"], r["Position3_C2"], r["Position4_V2"])] = r["SoundFile"]
        x = int(r["LikertRESPONSE"])
        if r["RightOption"] == "very pointed":
            answers[r["SoundFile"]].append(x)
            n_by_scale[r["SoundFile"]]["pointed"] += 1
        elif r["RightOption"] == "very rounded":
            answers[r["SoundFile"]].append(8 - x)
            n_by_scale[r["SoundFile"]]["rounded"] += 1
    items = sh[3]
    print(f"{NAME}: {len(items)} pseudowords, {len(answers)} with trials")
    seen = set()
    for it in items:
        f = it["SoundFile"]
        seg = (it["Position1_C1"], it["Position2_V1"], it["Position3_C2"], it["Position4_V2"])
        r, p = respell(*seg), ipa(*seg)
        tf = f if f in answers else orphan.get(seg)
        a = answers.get(tf)
        if not a or (r, p) in seen:
            continue
        seen.add((r, p))
        cnt = Counter(a)
        yield Question(
            text=TEXT.format(r=r, ipa=p),
            primitive="score",
            hemisphere="world",
            kind="perception",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            node_hint=NODE,
            human_text=HUMAN_TEXT.format(r=r, ipa=p),
            source_item_id=f,
            license=LICENSE,
            template_id=f"{NAME}.round_pointed",
            human=[HumanDist(
                population="Emory University community, native English speakers, heard the spoken word",
                distribution={str(k - 1): cnt[k] / len(a) for k in range(1, 8)},
                n=len(a),
                source="McCormick et al. 2015 SoS PASS trial data; pointed scale + recoded rounded scale (8 - x)",
            )],
            meta={
                "respelling": r,
                "ipa": p,
                "mean_1_7": round(sum(a) / len(a), 3),
                "published_mean_1_7": round(float(it["Mean rating recoded to single scale (1= rounded; 7=pointed)"]), 3),
                "trial_sound_file": tf,
                "n_pointed_scale": n_by_scale[tf]["pointed"],
                "n_rounded_scale": n_by_scale[tf]["rounded"],
                "consonants": f'{it["Consonant Manner"]}, {it["Consonant Voicing"]}',
                "vowels": f'{it["Vowel Roundedness"]}, {it["Vowel Backness"]}',
            },
        )
