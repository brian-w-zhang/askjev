"""Wikipedia Talk Labels: Personal Attacks (Wulczyn, Thain & Dixon 2017, Wikimedia / Jigsaw "Ex Machina").

115,864 English Wikipedia talk-page comments, each labelled by ~10 CrowdFlower workers: whether it contains a
personal attack, and whether the attack targets the recipient, a third party, quotes someone else, or other.
Source: the figshare release (CC0).

Templates (HumanDist = the annotator shares, n = annotators):
- "wiki_attacks.attack" (Noul): truth = true when >= 60% of annotators saw an attack, false when <= 10%;
  comments in between are dropped. 40% positive.
- "wiki_attacks.target" (Choice the_person_addressed / someone_else): among clear attacks (>= 60%), who
  it targets. the_person_addressed = recipient_attack share >= 50% and at least twice third_party; someone_else =
  third_party_attack share >= 50% and at least twice recipient. Distribution = recipient vs third-party shares,
  renormalised. Balanced halves.
Text cleanup: NEWLINE_TOKEN / TAB_TOKEN -> whitespace, doubled backticks -> quotes. Dropped: slurs, sexual
content mentioning minors, texts > 1,500 chars or < 15 chars, exact duplicates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "wiki_attacks"
FILES = {
    "attack_annotated_comments.tsv": "https://ndownloader.figshare.com/files/7554634",
    "attack_annotations.tsv": "https://ndownloader.figshare.com/files/7554637",
}
LICENSE = "CC0-1.0"
NODE = "machine.trust_safety.toxicity_harassment"
TARGET_ATTACK = env_int("TARGET_WIKI_ATTACKS", 2400)
TARGET_TARGET = env_int("TARGET_WIKI_ATTACKS_TARGET", 1800)

ATTACK_TEXT = "Does `comment` contain a personal attack on someone?"
ATTACK = {
    "true": "The comment insults, harasses, threatens or demeans a person, directly or by quoting or describing them",
    "false": "The comment has no personal attack, even if it disagrees sharply or criticizes an edit",
}
TARGET_TEXT = "Who does the personal attack in `comment` target?"
TARGET = {
    "the_person_addressed": "The person the comment is replying to or talking to",
    "someone_else": "A third party who is being talked about, not the person being addressed",
}

SLUR = re.compile(
    r"\b(nigg\w*|niggu\w*|nigs?|fag|fags|faggot\w*|kikes?|spics?|chinks?|retard\w*|trann(y|ies)|wetbacks?|"
    r"coons?|jigaboos?|shit ?skins?|sand ?niggers?|ragheads?|towel ?heads?|dykes?|beaners?|gooks?|paki|pakis)\b",
    re.I,
)
MINOR = re.compile(r"\b(child\w*|kids?|minors?|teen\w*|underage|pedo\w*|paedo\w*)\b", re.I)
SEXUAL = re.compile(
    r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|erotic\w*|horny|orgasm\w*|masturbat\w*|rape\w*|raping|"
    r"dick|cock|pussy|penis|vagina|blowjob\w*|cum|slut\w*|whore\w*)\b",
    re.I,
)
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|bush|cheney|sanders|putin|gop|republican\w*|democrat\w*|"
    r"liberals?|conservatives?|election\w*|abortion\w*|pro-life|pro-choice|nra|immigra\w*|refugees?|"
    r"illegals?|left-?wing|right-?wing|leftists?|zionis\w*|israel\w*|palestin\w*)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    for name, url in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(t: str) -> str:
    t = t.replace("NEWLINE_TOKEN", "\n").replace("TAB_TOKEN", " ").replace("``", '"').replace("`", "'")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip(" \n'\":")


def _meta(t: str, split: str, year: int) -> dict:
    flags = []
    if SEXUAL.search(t):
        flags.append("sensitive")
    if POLITICAL.search(t):
        flags.append("political")
    return {"split": split, "year": year, **({"flags": flags} if flags else {})}


def normalize(raw_dir: Path) -> Iterator[Question]:
    com = pl.read_csv(raw_dir / "attack_annotated_comments.tsv", separator="\t", quote_char=None)
    ann = pl.read_csv(raw_dir / "attack_annotations.tsv", separator="\t")
    g = ann.group_by("rev_id").agg(
        pl.len().alias("n"),
        pl.col("attack").mean().alias("att"),
        pl.col("recipient_attack").mean().alias("rec"),
        pl.col("third_party_attack").mean().alias("third"),
    )
    df = com.join(g, on="rev_id").sort("rev_id")
    items = []
    seen: set[str] = set()
    for r in df.iter_rows(named=True):
        t = _clean(r["comment"] or "")
        if len(t) < 15 or len(t) > 1500 or t.lower() in seen or SLUR.search(t):
            continue
        if SEXUAL.search(t) and MINOR.search(t):
            continue
        seen.add(t.lower())
        items.append((r, t))

    pos = [x for x in items if x[0]["att"] >= 0.6]
    neg = [x for x in items if x[0]["att"] <= 0.1]
    n_pos = min(len(pos), round(TARGET_ATTACK * 0.4))
    picked = [(x, True) for x in hash_order(pos, lambda x: x[0]["rev_id"], "wiki.attack.pos")[:n_pos]]
    picked += [(x, False) for x in hash_order(neg, lambda x: x[0]["rev_id"], "wiki.attack.neg")[: TARGET_ATTACK - n_pos]]
    for (r, t), truth in sorted(picked, key=lambda z: z[0][0]["rev_id"]):
        a = round(r["att"], 4)
        yield Question(
            text=ATTACK_TEXT, primitive="noul", hemisphere="machine", origin="dataset", source=NAME,
            options=ATTACK, state={"comment": t}, shape="detect", node_hint=NODE,
            template_id="wiki_attacks.attack", source_item_id=f"rev:{r['rev_id']}", license=LICENSE, truth=truth,
            human=[HumanDist(population="CrowdFlower annotators (Wikipedia Detox)",
                             distribution={"true": a, "false": round(1 - a, 4)}, n=r["n"],
                             source="Wikipedia Talk Labels: Personal Attacks, attack")],
            meta=_meta(t, r["split"], r["year"]),
        )

    rec = [x for x in pos if x[0]["rec"] >= 0.5 and x[0]["rec"] >= 2 * x[0]["third"]]
    third = [x for x in pos if x[0]["third"] >= 0.5 and x[0]["third"] >= 2 * x[0]["rec"]]
    per = TARGET_TARGET // 2
    n_third = min(per, len(third))
    chosen = [(x, "someone_else") for x in hash_order(third, lambda x: x[0]["rev_id"], "wiki.target.third")[:n_third]]
    chosen += [(x, "the_person_addressed") for x in
               hash_order(rec, lambda x: x[0]["rev_id"], "wiki.target.rec")[: TARGET_TARGET - n_third]]
    for (r, t), truth in sorted(chosen, key=lambda z: z[0][0]["rev_id"]):
        s = r["rec"] + r["third"]
        dist = {"the_person_addressed": round(r["rec"] / s, 4), "someone_else": round(r["third"] / s, 4)}
        yield Question(
            text=TARGET_TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME,
            options=TARGET, state={"comment": t}, shape="classify", node_hint=NODE,
            template_id="wiki_attacks.target", source_item_id=f"rev:{r['rev_id']}", license=LICENSE, truth=truth,
            human=[HumanDist(population="CrowdFlower annotators (Wikipedia Detox)", distribution=dist, n=r["n"],
                             source="Wikipedia Talk Labels: Personal Attacks, recipient vs third_party (renormalised)")],
            meta=_meta(t, r["split"], r["year"]),
        )
