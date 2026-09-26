"""HateXplain (Mathew et al., AAAI 2021): Twitter and Gab posts, each labelled by 3 MTurk annotators as
hate speech, offensive or normal.

Template "hatexplain.label" (Choice): truth = the label all three annotators gave (2-1 and 3-way splits
are dropped: the dataset's agreement is low). HumanDist = the three annotators' labels. Classes are balanced to thirds.
Source: dataset.json in the authors' GitHub repo (the HF copy is script-based, no parquet export).
Posts are stored as lowercase tokens; they are re-joined with spaces and `<user>` becomes `@user`.
Dropped: posts with slurs, sexual content mentioning minors, near-empty posts, exact duplicates.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "hatexplain"
URL = "https://raw.githubusercontent.com/hate-alert/HateXplain/master/Data/dataset.json"
LICENSE = "MIT"
NODE = "machine.trust_safety.toxicity_harassment"
TARGET = env_int("TARGET_HATEXPLAIN", 2100)

TEXT = "Is `post` hate speech, offensive without being hate speech, or normal?"
OPTIONS = {
    "hate_speech": "Attacks or dehumanizes people because of their race, religion, ethnicity, gender, "
    "sexual orientation, disability or other group identity",
    "offensive": "Rude, insulting, vulgar or abusive, but not an attack on a group identity",
    "normal": "Neither hateful nor offensive",
}
LABEL = {"hatespeech": "hate_speech", "offensive": "offensive", "normal": "normal"}

SLUR = re.compile(
    r"\b(nigg\w*|niggu\w*|nigs?|fag|fags|faggot\w*|kikes?|spics?|chinks?|retard\w*|trann(y|ies)|wetbacks?|"
    r"coons?|jigaboos?|spear ?chuck\w*|shit ?skins?|mud ?(people|races?)|sand ?niggers?|ragheads?|towel ?heads?|dykes?|beaners?|gooks?|muzzies?|paki|pakis)\b",
    re.I,
)
MINOR = re.compile(r"\b(child\w*|kids?|minors?|teen\w*|underage|pedo\w*|paedo\w*|loli\w*)\b", re.I)
SEXUAL = re.compile(
    r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|erotic\w*|horny|orgasm\w*|masturbat\w*|rape\w*|raping|"
    r"dick|cock|pussy|penis|vagina|blowjob\w*|cum|slut\w*|whore\w*)\b",
    re.I,
)
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|sanders|bernie|pence|putin|pelosi|biden|romney|aoc|"
    r"maga|gop|republican\w*|democrat\w*|dems?|liberals?|libtards?|conservatives?|election\w*|vot(e|es|ed|er|ers|ing)|"
    r"ballot\w*|congress\w*|senat\w*|parliament\w*|abortion\w*|pro-life|pro-choice|guns?|nra|"
    r"immigra\w*|migrants?|refugees?|illegals?|deport\w*|border|brexit|left-?wing|right-?wing|leftists?|"
    r"alt-right|antifa|socialis\w*|communis\w*|feminis\w*|nationalis\w*|white genocide|israel\w*|zionis\w*|"
    r"palestin\w*|politic\w*)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "dataset.json"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _flags(t: str) -> list[str]:
    f = []
    if SEXUAL.search(t):
        f.append("sensitive")
    if POLITICAL.search(t):
        f.append("political")
    return f


def normalize(raw_dir: Path) -> Iterator[Question]:
    data = json.loads((raw_dir / "dataset.json").read_text())
    by_label: dict[str, list] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for pid, v in data.items():
        t = " ".join(v["post_tokens"]).replace("<user>", "@user")
        t = re.sub(r"<(number|percent|money|time|date|url|email|phone)>", r"[\1]", t)
        t = " ".join(t.split())
        if len(t) < 20 or len(t) > 1500 or t in seen or SLUR.search(t):
            continue
        if SEXUAL.search(t) and MINOR.search(t):
            continue
        labs = [LABEL[a["label"]] for a in v["annotators"] if a["label"] in LABEL]
        if len(labs) < 3:
            continue
        top, n = Counter(labs).most_common(1)[0]
        if n < 3:  # unanimous only: HateXplain's agreement is low, so 2-1 labels are not trusted
            continue
        seen.add(t)
        dist = {k: round(labs.count(k) / len(labs), 4) for k in OPTIONS}
        targets = sorted({x for a in v["annotators"] for x in a["target"] if x not in ("None",)})
        by_label[top].append((pid, t, dist, len(labs), targets))

    per = TARGET // len(OPTIONS)
    take = {k: min(per, len(by_label[k])) for k in OPTIONS}
    slack = TARGET - sum(take.values())
    for k in sorted(OPTIONS, key=lambda k: -len(by_label[k])):
        add = min(slack, len(by_label[k]) - take[k])
        take[k] += add
        slack -= add
    for k in OPTIONS:
        for pid, t, dist, n, targets in sorted(hash_order(by_label[k], lambda x: x[0], f"hatexplain.{k}")[: take[k]]):
            flags = _flags(t)
            yield Question(
                text=TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=OPTIONS,
                state={"post": t},
                shape="classify",
                node_hint=NODE,
                template_id="hatexplain.label",
                source_item_id=pid,
                license=LICENSE,
                truth=k,
                human=[HumanDist(population="MTurk annotators (HateXplain)", distribution=dist, n=n,
                                 source="HateXplain dataset.json annotator labels")],
                meta={"platform": pid.rsplit("_", 1)[-1], "targets": targets, **({"flags": flags} if flags else {})},
            )
