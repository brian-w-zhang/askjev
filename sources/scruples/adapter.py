"""Scruples Dilemmas (AllenAI, Apache-2.0): "which of two real-life actions is less ethical?" with
Mechanical Turk vote counts."""

from __future__ import annotations

import json
import random
import re
import tarfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "scruples"
URL = "https://storage.googleapis.com/ai2-mosaic-public/projects/scruples/v1.0/data/dilemmas.tar.gz"
LICENSE = "Apache-2.0 (allenai/scruples); action text from Reddit"
TARGET = 600
SEED = 20260924
SPLITS = ("dev", "test")

SEXUAL = re.compile(
    r"\b(sex\w*|porn\w*|nudes?|naked|orgasm\w*|virgin\w*|penis\w*|vagina\w*|boobs?|breasts?|dick|cock|pussy|"
    r"masturbat\w*|erotic\w*|lingerie|threesome|hooker|prostitut\w*|strippers?|stripping|hook(ed|ing)? up with|"
    r"sleep(ing|s)? with (him|her|them|someone|somebody|other)|slept with|fuck ?buddy|sugar (baby|daddy)|affair|condoms?|anal|foreplay|kinky|fetish\w*|horny|seduc\w*|topless|"
    r"making out|make out|onlyfans|sext\w*|hickey|blow ?job)\b",
    re.I,
)
SELF_HARM = re.compile(
    r"\b(suicid\w*|kill(ing)? myself|self[- ]harm\w*|cutting myself|cut myself|overdos\w*|eating disorder|"
    r"anorexi\w*|bulimi\w*|want(ed)? to die)\b",
    re.I,
)
VIOLENT = re.compile(
    r"\b(kill\w*|murder\w*|punch\w*|hit(ting)?|beat(ing)? (up|him|her|them)|slap\w*|stab\w*|shoot\w*|shot|"
    r"guns?|knife|abus\w*|assault\w*|violen\w*|physical fight\w*|choke\w*|chok(ing|ed)|strangl\w*|"
    r"threaten\w*|attack\w*|rape\w*|raping|molest\w*)\b",
    re.I,
)
MINORS = re.compile(
    r"\b(child|children|kids?|minors?|teen\w*|underage|\d{1,2} ?(yo|y/o|year ?old)|little (boy|girl)|"
    r"daughter|son|students?|highschool|high school|middle school)\b",
    re.I,
)
SEXUAL_VIOLENCE = re.compile(r"\b(rape\w*|raping|sexual(ly)? assault\w*|molest\w*|incest|pedo\w*|paedo\w*)\b", re.I)
SLURS = re.compile(r"\b(fag\w*|nigg\w*|retard\w*|tranny|dyke|spic|chink|kike|gook)\b", re.I)


def fetch(raw_dir: Path) -> None:
    if all((raw_dir / "dilemmas" / f"{s}.scruples-dilemmas.jsonl").exists() for s in SPLITS):
        return
    out = raw_dir / "dilemmas.tar.gz"
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)
    with tarfile.open(out) as tf:
        tf.extractall(raw_dir, filter="data")


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip().rstrip("?").strip()
    return s[:1].upper() + s[1:]


def normalize(raw_dir: Path) -> Iterator[Question]:
    strata: dict[str, list] = {"unanimous": [], "clear": [], "split": []}
    seen = set()
    for split in SPLITS:
        with open(raw_dir / "dilemmas" / f"{split}.scruples-dilemmas.jsonl", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                a, b = (_clean(x["description"]) for x in r["actions"])
                if not a or not b or a.lower() == b.lower():
                    continue
                pair = frozenset((a.lower(), b.lower()))
                if pair in seen:
                    continue
                both = f"{a} {b}"
                sexual = bool(SEXUAL.search(both))
                if SLURS.search(both) or SEXUAL_VIOLENCE.search(both) or (sexual and MINORS.search(both)):
                    continue
                seen.add(pair)
                g = r["gold_annotations"]
                lo = min(g)
                stratum = "unanimous" if lo == 0 else "clear" if lo == 1 else "split"
                strata[stratum].append((split, r, a, b, sexual))

    # Equal thirds by gold agreement (5-0, 4-1, 3-2), seeded; leftovers fill any shortfall.
    rng = random.Random(SEED)
    per = TARGET // len(strata)
    picked, rest = [], []
    for name in strata:
        pool = sorted(strata[name], key=lambda x: x[1]["id"])
        rng.shuffle(pool)
        picked += pool[:per]
        rest += pool[per:]
    rng.shuffle(rest)
    picked += rest[: TARGET - len(picked)]
    picked.sort(key=lambda x: (x[0], x[1]["id"]))

    for split, r, a, b, sexual in picked:
        g, hp = r["gold_annotations"], r.get("human_perf_annotations") or [0, 0]
        va, vb = g[0] + hp[0], g[1] + hp[1]
        n = va + vb
        both = f"{a} {b}"
        flags = ["sensitive"] if (sexual or SELF_HARM.search(both) or VIOLENT.search(both)) else []
        yield Question(
            text="Which of these two actions is less ethical?",
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options={"a": a, "b": b},
            node_hint="self.values.everyday_ethics",
            human_text="Which of these two actions would most people say is less ethical?",
            source_item_id=f"{split}:{r['id']}",
            license=LICENSE,
            human=[
                HumanDist(
                    population="MTurk annotators",
                    distribution={"a": va / n, "b": vb / n},
                    n=n,
                    source="Scruples Dilemmas v1.0 gold + human-performance annotations",
                )
            ],
            meta={
                "split": split,
                "gold_annotations": g,
                "human_perf_annotations": hp,
                "controversial": r["controversial"],
            }
            | ({"flags": flags} if flags else {}),
        )
