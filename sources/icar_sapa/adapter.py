"""SAPA Project temperament items (Condon & Revelle, CC0 Harvard Dataverse releases) with item-level response
distributions from the public 696-item SAPA data (22 Dec 2015 - 7 Feb 2017, 48,350 participants).

Almost every SAPA temperament item (including all of the SPI-135) is an IPIP item already carried by the `ipip`
and `openpsych` sources, so this adapter keeps only the SAPA items those sources lack (checked against
the database and both normalized files on 2026-09-24): 78 of the 79 EPQ-R-style items (Eysenck extraversion,
neuroticism and psychoticism) SAPA administered, plus two IPIP-analog items (MPQ unlikely virtues, plasticity/stability) that
the ipip item pool does not include. ICAR ability items are not self-descriptions and are not used."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question

NAME = "icar_sapa"
LICENSE = "CC0-1.0 (SAPA Project data, Harvard Dataverse doi:10.7910/DVN/TZJGAT); EPQ-R item wording (c) Eysenck"
DOI = "doi:10.7910/DVN/TZJGAT"
FILES = {  # Dataverse datafile ids
    "ItemInfo696.tab": 3002780,
    "sapa_2015_2017.tab": 11016294,
    "demographic_codes.txt": 11016292,
}
EXTRA_IDS = {"q_393", "q_3090"}  # non-EPQ items not in the ipip/openpsych pools
SKIP_IDS = {"q_4263"}  # "Worry about my health." is also an IPIP item (already in sources/ipip)

LEVELS = [  # same levels as sources/ipip
    "This does not describe me at all",
    "This describes me a little",
    "This describes me moderately well",
    "This describes me well",
    "This describes me very well",
]
# SAPA's 6-point accuracy scale (1 Very Inaccurate ... 6 Very Accurate) collapsed onto the 5 levels.
LEVEL_MAP = {1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4}
MAP_NOTE = "6-point accuracy collapsed to 5 levels: 1->0, 2-3->1, 4->2, 5->3, 6->4"

TEXT_FIX = {  # SAPA stems lost their apostrophes; one stem needs its subject placed
    "q_4233": "I dislike people who don't know how to behave themselves.",
    "q_4255": "I have often gone against my parents' wishes.",
    "q_4291": "It is better to follow society's rules than to go my own way.",
    "q_4297": "I believe one has special duties to one's family.",
    "q_3090": "When I am with a group, I have difficulties selecting a good topic to talk about.",
}
NO_SUBJECT = re.compile(r"^(My|Being|It|People|Good|Most|There|Other|When)\b")
SCALE = {"EPQ:E": "extraversion", "EPQ:N": "neuroticism", "EPQ:P": "psychoticism",
         "MPQ:UV": "unlikely virtues", "PS:P": "plasticity"}

NODES = [  # (regex over the statement, node): first match wins
    (re.compile(r"(?i)hurting people|really hurt people|afraid of me"), "self.personality.dark_side"),
    (re.compile(r"(?i)rashly|spur of the moment|look before|think things over|debt|mistakes in my work|appointments|"
                r"savings|act quickly|more activities"), "self.personality.big_five.conscientiousness.order_caution"),
    (re.compile(r"(?i)drugs"), "self.personality.risk_decision_style"),
    (re.compile(r"(?i)law|rules|marriage|manners|parents|duties to|right and wrong"),
     "self.personality.big_five.openness.convention_politics"),
    (re.compile(r"(?i)charit|animal suffer|animal caught|cooperating|rude"),
     "self.personality.big_five.agreeableness.kindness_cooperation"),
    (re.compile(r"(?i)lies|lying|truth|enemies|avoid me"),
     "self.personality.big_five.agreeableness.trust_modesty_temper"),
    (re.compile(r"(?i)temper|irritable|touchy|mood|fed-up|miserable|bubbling"),
     "self.personality.big_five.neuroticism.temper_moodiness"),
    (re.compile(r"(?i)hurt|embarrass|find fault|looks|guilt|what people think"),
     "self.personality.big_five.neuroticism.self_consciousness"),
    (re.compile(r"(?i)worr|nervous|tense|nerves"), "self.personality.big_five.neuroticism.fear_worry"),
]
TRAIT_NODE = {"EPQ:E": "self.personality.big_five.extraversion.sociability_energy",
              "EPQ:N": "self.personality.big_five.neuroticism", "EPQ:P": "self.personality",
              "PS:P": "self.personality.big_five.extraversion.sociability_energy"}
SENSITIVE = re.compile(r"(?i)wished that I were dead|drugs")


def fetch(raw_dir: Path) -> None:
    for name, fid in FILES.items():
        out = raw_dir / name
        if not out.exists():
            r = httpx.get(f"https://dataverse.harvard.edu/api/access/datafile/{fid}", follow_redirects=True, timeout=600)
            r.raise_for_status()
            out.write_bytes(r.content)


def _sentence(iid: str, stem: str) -> str:
    if iid in TEXT_FIX:
        return TEXT_FIX[iid]
    s = re.sub(r"\s+", " ", stem).strip()
    if not NO_SUBJECT.match(s):
        s = "I " + s[:1].lower() + s[1:]
    return s if s.endswith((".", "!", "?")) else s + "."


def normalize(raw_dir: Path) -> Iterator[Question]:
    info = pl.read_csv(raw_dir / "ItemInfo696.tab", separator="\t", null_values="NULL", infer_schema_length=0)
    info = info.rename({"": "id"}).with_columns(pl.col("id").str.to_lowercase())
    keep = [r for r in info.iter_rows(named=True)
            if (r["EPQr"] or r["id"] in EXTRA_IDS) and r["id"] not in SKIP_IDS]
    cols = [r["id"] for r in keep]
    df = pl.read_csv(raw_dir / "sapa_2015_2017.tab", separator="\t", columns=cols, infer_schema_length=0,
                     null_values=["NA", ""])
    df = df.with_columns([pl.col(c).cast(pl.Int64, strict=False) for c in cols])

    for r in sorted(keep, key=lambda r: int(r["id"][2:])):
        iid = r["id"]
        code = r["EPQr"] or r["MPQ"] or r["PS"]
        stmt = _sentence(iid, r["Item"])
        vc = dict(df[iid].drop_nulls().value_counts().iter_rows())
        counts = [0] * len(LEVELS)
        for raw, lvl in LEVEL_MAP.items():
            counts[lvl] += vc.get(raw, 0)
        n = sum(counts)
        if not n:
            continue
        node = next((nd for rx, nd in NODES if rx.search(stmt)), TRAIT_NODE.get(code, "self.personality"))
        meta = {"item_id": iid, "sapa_stem": r["Item"].strip(), "scale": code, "trait": SCALE.get(code),
                "instrument": "EPQ-R" if r["EPQr"] else "IPIP", "scale_raw": "1-6 Very Inaccurate..Very Accurate",
                "level_map": {str(a): b for a, b in LEVEL_MAP.items()}}
        if SENSITIVE.search(stmt):
            meta["flags"] = ["sensitive"]
        yield Question(
            text=f'How well does this statement describe you: "{stmt}"',
            primitive="score",
            hemisphere="self",
            kind="personality",
            origin="dataset",
            source=NAME,
            options=LEVELS,
            node_hint=node,
            human_text=f'How well would most people say this statement describes them: "{stmt}"',
            source_item_id=iid,
            license=LICENSE,
            human=[
                HumanDist(
                    population="SAPA Project web respondents (2015-2017)",
                    distribution={str(i): round(c / n, 6) for i, c in enumerate(counts)},
                    n=n,
                    source=f"SAPA 696-item temperament data 22Dec2015-07Feb2017 ({DOI}) item {iid}; {MAP_NOTE}",
                )
            ],
            meta=meta,
        )
