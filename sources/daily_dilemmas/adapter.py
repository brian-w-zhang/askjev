"""DailyDilemmas (Chiu, Jiang & Choi 2024, CC-BY-4.0): 1,360 everyday moral dilemmas, each with a "do" and a
"not do" action tagged with the human values it serves. Asked as a two-way Choice between the actions; no truth."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "daily_dilemmas"
BASE = "https://huggingface.co/api/datasets/kellycyy/daily_dilemmas/parquet/{c}/test/0.parquet"
CONFIGS = ("Dilemmas_with_values_aggregated", "Values")
LICENSE = "CC-BY-4.0 (kellycyy/daily_dilemmas)"
TARGET = env_int("TARGET_DAILY_DILEMMAS", 2500)  # the dataset has 1,360 dilemmas; all are kept
SALT = "daily_dilemmas-v1"
TEXT = "What is the right thing to do in `dilemma`?"

SEXUAL = re.compile(r"\b(sex\w*|porn\w*|nudes?|naked|erotic\w*|affair|one[- ]night stand|intimacy|intimate)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|self[- ]harm\w*|overdos\w*|eating disorder|anorexi\w*|bulimi\w*|euthanas\w*)\b", re.I)
POLITICAL = re.compile(r"\b(abort\w*|terminat\w* (the|her|a|my|your) pregnancy|republican\w*|democrat\w*|election\w*|"
                       r"vot(e|ed|ing)\b|immigra\w*|illegal immigrant\w*|gun control|firearm\w*|guns?|protest\w*|"
                       r"political part\w*|politician\w*|death penalty)\b", re.I)

NODES = [  # (situation+actions regex, value-tag regex or None, node), first match wins
    (re.compile(r"\b(animals?|wildlife|pets?|dogs?|cats?|birds?|species|poach\w*|hunt\w*|zoo|environment\w*|"
                r"forest\w*|pollut\w*|climate|endangered|habitat|recycl\w*|vegan|meat)\b", re.I), None,
     "self.values.animals_environment.animal_nature_dilemmas"),
    (re.compile(r"\b(donat\w*|charit\w*|homeless|volunteer\w*|beggar\w*|fundrais\w*|needy|poverty)\b", re.I), None,
     "self.values.giving_charity"),
    (re.compile(r"\b(lie|lied|lying|truth\w*|secret\w*|reveal\w*|confess\w*|honest\w*|admit\w*|disclos\w*|"
                r"tell (him|her|them|your|his|the)|deceiv\w*|cheat\w*|promise\w*)\b", re.I),
     re.compile(r"honesty|truth|transparen|decepti|dishonest|trust", re.I), "self.values.honesty_trust.honesty_dilemmas"),
    (re.compile(r"\b(fair\w*|unfair\w*|credit|punish\w*|justice|deserv\w*|equal\w*|discriminat\w*|favoritism|bias\w*)\b",
                re.I), re.compile(r"fairness|justice|equality|equity", re.I), "self.values.fairness_justice"),
    (re.compile(r"\b(retaliat\w*|revenge|aveng\w*|forgiv\w*|get even)\b", re.I), None, "self.values.fairness_justice"),
]


def fetch(raw_dir: Path) -> None:
    for c in CONFIGS:
        out = raw_dir / f"{c}.parquet"
        if not out.exists():
            r = httpx.get(BASE.format(c=c), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _slug(s: str, maxlen: int) -> str:
    words = re.findall(r"[a-z0-9]+", s.lower().replace("'", ""))
    k = ""
    for w in words:
        if len(k) + len(w) + 1 > maxlen:
            break
        k = f"{k}_{w}" if k else w
    return k


def _keys(a: str, b: str) -> tuple[str, str] | None:
    for n in (40, 60, 100):
        ka, kb = _slug(a, n), _slug(b, n)
        if ka and kb and ka != kb:
            return ka, kb
    return None


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / f"{CONFIGS[0]}.parquet")
    by_dilemma: dict[int, dict] = {}
    for r in df.iter_rows(named=True):
        by_dilemma.setdefault(r["dilemma_idx"], {})[r["action_type"]] = r

    pool = []
    for didx, acts in by_dilemma.items():
        if set(acts) != {"to_do", "not_to_do"}:
            continue
        do, dont = acts["to_do"], acts["not_to_do"]
        situation = _clean(do["dilemma_situation"])
        a, b = _clean(do["action"]).rstrip("."), _clean(dont["action"]).rstrip(".")
        keys = _keys(a, b)
        if not situation or keys is None:
            continue
        pool.append((didx, do, dont, situation, a, b, keys))

    for didx, do, dont, situation, a, b, (ka, kb) in hash_order(pool, key=lambda x: x[0], salt=SALT)[:TARGET]:
        blob = " ".join([situation, a, b])
        vals_do = ast.literal_eval(do["values_aggregated"] or "[]")
        vals_dont = ast.literal_eval(dont["values_aggregated"] or "[]")
        tags = " ".join(vals_do + vals_dont)
        node = next((n for rx, vrx, n in NODES if rx.search(blob) and (vrx is None or vrx.search(tags))),
                    "self.values.life_values.personal_priorities")
        flags = []
        if SEXUAL.search(blob) or SELF_HARM.search(blob):
            flags.append("sensitive")
        if POLITICAL.search(blob):
            flags.append("political")
        meta = {
            "values": {ka: vals_do, kb: vals_dont},
            "negative_consequence": {ka: _clean(do["negative_consequence"]), kb: _clean(dont["negative_consequence"])},
            "basic_situation": _clean(do["basic_situation"]),
            "topic_group": do["topic_group"],
            "action_type": {ka: "to_do", kb: "not_to_do"},
        }
        if flags:
            meta["flags"] = flags
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="template",
            source=NAME,
            options={ka: a, kb: b},
            state={"dilemma": situation},
            node_hint=node,
            source_item_id=str(didx),
            license=LICENSE,
            meta=meta,
        )
