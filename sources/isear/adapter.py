"""ISEAR (International Survey on Emotion Antecedents and Reactions; Scherer & Wallbott 1994): about 3,000
students in 37 countries each described situations in which they had felt joy, fear, anger, sadness, disgust,
shame and guilt. Asked as a 7-way Choice with the respondent's own situation text in state and the emotion they
were reporting as truth."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "isear"
BASE = "https://huggingface.co/datasets/savalera/isear-from-original/resolve/main/original/"
FILES = ("train-00000-of-00001.parquet", "validation-00000-of-00001.parquet", "test-00000-of-00001.parquet")
LICENSE = ("ISEAR databank (Scherer & Wallbott, University of Geneva), made freely available for research; "
           "HF mirror savalera/isear-from-original tagged apache-2.0")
TARGET = env_int("TARGET_ISEAR", 5000)
SALT = "isear-v1"
TEXT = "Someone described `situation` as a time they felt a strong emotion. Which emotion did they feel?"
NODE = "self.mind.reading_people.reading_feelings"
EMOTIONS = {1: "joy", 2: "fear", 3: "anger", 4: "sadness", 5: "disgust", 6: "shame", 7: "guilt"}

# any label word or near form: the own label gives the answer away, another label is a misleading cue
LABEL_WORDS = re.compile(
    r"\b(joy\w*|happ(y|ier|iest|iness)|glad|delight\w*|fear\w*|afraid|scar(ed|y)|frighten\w*|terrif\w*|anger|angr\w*|"
    r"annoy\w*|furious|fury|rage|mad\b|sad\w*|sorrow\w*|unhapp\w*|depress\w*|disgust\w*|revolt\w*|repuls\w*|"
    r"nause\w*|shame\w*|asham\w*|embarrass\w*|humiliat\w*|guilt\w*)", re.I)
# answers that point at another answer ("the previous incident holds good here also") mean nothing alone
REFERS = re.compile(r"\b(previous|above|same (as|incident|situation|event)|as (before|in question|mentioned)|see (question|above|anger|fear|joy|sadness|disgust|shame|guilt))\b", re.I)
JUNK = re.compile(r"^\W*(no response|blank|none|do not know|don'?t know|not applicable|n/?a|nothing|"
                  r"the same as|same as|see above|as above|i can'?t remember|i do not remember|never experienced|"
                  r"not experienced)\b", re.I)
SEXUAL = re.compile(r"\b(sex\w*|porn\w*|naked|nude|orgasm\w*|erotic\w*|condoms?|intercourse|masturbat\w*|"
                    r"homosexual\w*|prostitut\w*|genital\w*|penis|vagina|breasts?|caress\w*|virgin\w*)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|kill(ed|ing)? (my|him|her|them)sel(f|ves)|self[- ]harm\w*|overdos\w*)\b", re.I)
VIOLENT = re.compile(r"\b(murder\w*|rap(e|es|ed|ing|ists?)|stab\w*|molest\w*|assault\w*|abus(e|ed|ive)|tortur\w*|"
                     r"beat(en|ing)? (me|him|her|up)|corpse\w*|blood\w*)\b", re.I)
SLUR = re.compile(r"\b(n[i1]gg\w*|fag\w*|retard\w*|spic|chink|kike|negro\w*)\b", re.I)
POLITICAL = re.compile(r"\b(politic\w*|election\w*|government|president|apartheid|communis\w*|regime|party member|"
                       r"abortion|demonstration\w*|police)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        p = raw_dir / f
        if p.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=300)
        r.raise_for_status()
        p.write_bytes(r.content)


def _clean(s: str) -> str:
    s = re.sub(r"[\x00-\x1f\x7f�]", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip().strip('"').strip()
    s = re.sub(r"\s+([,.!?;:])", r"\1", s)
    return s[:1].upper() + s[1:]


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = pl.concat([pl.read_parquet(raw_dir / f).with_columns(pl.lit(f.split("-")[0]).alias("split")) for f in FILES],
                     how="diagonal_relaxed")
    pool, seen = [], set()
    for r in rows.iter_rows(named=True):
        emo = EMOTIONS.get(r["EMOT"])
        s = _clean(r["SIT"])
        if not emo or len(s.split()) < 5 or len(s) > 800 or JUNK.search(s) or REFERS.search(s) or s.startswith("["):
            continue
        if LABEL_WORDS.search(s) or SLUR.search(s):
            continue
        key = re.sub(r"\W+", " ", s.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        pool.append({"id": str(r["MYKEY"]), "emotion": emo, "situation": s, "country": r["COUN"], "split": r["split"]})
    # balanced across the seven emotions: round-robin through each label's salted-hash order
    labels = list(EMOTIONS.values())
    by = {e: hash_order([d for d in pool if d["emotion"] == e], key=lambda d: d["id"], salt=SALT) for e in labels}
    picked, i = [], 0
    while len(picked) < TARGET and any(i < len(v) for v in by.values()):
        for e in labels:
            if i < len(by[e]) and len(picked) < TARGET:
                picked.append(by[e][i])
        i += 1
    for d in picked:
        s = d["situation"]
        flags = []
        if SEXUAL.search(s) or SELF_HARM.search(s) or VIOLENT.search(s):
            flags.append("sensitive")
        if POLITICAL.search(s):
            flags.append("political")
        meta = {"country_code": d["country"], "mirror_split": d["split"]}
        if flags:
            meta["flags"] = flags
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="social",
            origin="template",
            source=NAME,
            options={e: None for e in labels},
            state={"situation": s},
            node_hint=NODE,
            source_item_id=d["id"],
            license=LICENSE,
            truth=d["emotion"],
            template_id=f"{NAME}.emotion",
            meta=meta,
        )
