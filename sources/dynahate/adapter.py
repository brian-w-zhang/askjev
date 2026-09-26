"""Dynamically Generated Hate Speech Dataset (DynaHate; Vidgen et al., ACL 2021).

~41k statements written by trained annotators over four rounds of human-and-model-in-the-loop data
collection, each labelled hate / not hate and, for hate from round 2 on, a type (derogation, animosity,
threatening, support for hateful entities, dehumanization) and target. Labels were set by the writer and
checked by expert annotators. The statements are human-written (adversarial against a model), not generated.

Template "dynahate.hate_type" (Choice over the five types): hateful statements with a given type,
stratified (support is rare, ~200; the other four share the rest). Truth = dataset type.
Dropped: slurs, sexual content mentioning minors, > 1,500 chars, duplicates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "dynahate"
URL = ("https://raw.githubusercontent.com/bvidgen/Dynamically-Generated-Hate-Speech-Dataset/main/"
       "Dynamically%20Generated%20Hate%20Dataset%20v0.2.3.csv")
LICENSE = "CC-BY-4.0"
NODE = "machine.trust_safety.toxicity_harassment"
TARGET = env_int("TARGET_DYNAHATE", 2000)

TEXT = "Which kind of hate does `statement` express?"
OPTIONS = {
    "derogation": "Explicitly demeans a group: negative traits, stereotypes, insults or disgust stated outright",
    "animosity": "Implicit or subtle hostility: backhanded remarks, resentment or blame without open insults",
    "threatening": "States an intention, wish or call to harm, attack or kill members of a group",
    "support_for_hate": "Praises or defends hateful groups, people or events, such as Nazis, the KKK or the Holocaust",
    "dehumanization": "Describes a group as less than human: animals, insects, vermin, disease or filth",
}
TYPE = {"derogation": "derogation", "animosity": "animosity", "threatening": "threatening",
        "support": "support_for_hate", "dehumanization": "dehumanization"}

SLUR = re.compile(
    r"\b(nigg\w*|niggu\w*|nigs?|fag|fags|faggot\w*|kikes?|spics?|chinks?|retard\w*|trann(y|ies)|wetbacks?|"
    r"coons?|jigaboos?|spear ?chuck\w*|shit ?skins?|sand ?niggers?|ragheads?|towel ?heads?|dykes?|beaners?|"
    r"gooks?|muzzies?|paki|pakis|camel ?jockeys?|golliwogs?|wogs?)\b",
    re.I,
)
MINOR = re.compile(r"\b(child\w*|kids?|minors?|teen\w*|underage|pedo\w*|paedo\w*)\b", re.I)
SEXUAL = re.compile(
    r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|erotic\w*|horny|rape\w*|raping|dick|cock|pussy|penis|vagina|"
    r"slut\w*|whore\w*)\b",
    re.I,
)
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|biden|maga|gop|republican\w*|democrat\w*|liberals?|conservatives?|"
    r"election\w*|vot(e|es|ed|ers|ing)|abortion\w*|immigra\w*|migrants?|refugees?|illegals?|deport\w*|border|"
    r"brexit|leftists?|antifa|black lives matter|blm|proud boys|zionis\w*|israel\w*|palestin\w*|welfare)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "dynahate_v0.2.3.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    d = pl.read_csv(raw_dir / "dynahate_v0.2.3.csv", infer_schema_length=0)
    d = d.filter((pl.col("label") == "hate") & pl.col("type").is_in(list(TYPE)) & (pl.col("level") == "original"))
    by: dict[str, list] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for r in d.iter_rows(named=True):
        t = " ".join((r["text"] or "").split())
        if len(t) < 15 or len(t) > 1500 or t.lower() in seen or SLUR.search(t):
            continue
        if SEXUAL.search(t) and MINOR.search(t):
            continue
        seen.add(t.lower())
        by[TYPE[r["type"]]].append((r["acl.id"], t, r))
    ordered = {k: hash_order(v, lambda x: x[0], f"dynahate.{k}") for k, v in by.items()}
    take = {k: 0 for k in OPTIONS}
    quota = TARGET
    while quota > 0:
        open_ = [k for k in OPTIONS if take[k] < len(ordered[k])]
        if not open_:
            break
        share = max(1, quota // len(open_))
        for k in open_:
            add = min(share, len(ordered[k]) - take[k], quota)
            take[k] += add
            quota -= add
            if quota == 0:
                break
    for k in OPTIONS:
        for aid, t, r in sorted(ordered[k][: take[k]], key=lambda x: x[0]):
            flags = []
            if SEXUAL.search(t):
                flags.append("sensitive")
            if POLITICAL.search(t):
                flags.append("political")
            yield Question(
                text=TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME,
                options=OPTIONS, state={"statement": t}, shape="classify", node_hint=NODE,
                template_id="dynahate.hate_type", source_item_id=aid, license=LICENSE, truth=k,
                meta={"round": r["round"], "level": r["level"], "split": r["split"], "target": r["target"],
                      **({"flags": flags} if flags else {})},
            )
