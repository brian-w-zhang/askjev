"""Measuring Hate Speech (Kennedy et al. 2020, UC Berkeley D-Lab): 39,565 social media comments (YouTube,
Twitter, Reddit, Gab) with 135,556 crowd annotations on a battery of survey items.

Templates (only comments with >= 3 annotators; HumanDist = those annotators' answers):
- "mhs.hate_speech" (Noul): item `hatespeech` (0 no / 1 unclear / 2 yes). Shares are over annotators who
  answered yes or no; truth = true when >= 75% said yes, false when >= 75% said no, other comments dropped.
  40% positive.
- "mhs.stance" (Choice attacks / defends / neither): item `attack_defend` (0-1 strongly/somewhat
  defending, 2 neutral, 3-4 somewhat/strongly attacking the targeted group). Truth when >= 2/3 of
  annotators fall in one bucket. Balanced across the three buckets; `defends` is the counter-speech class
  the dataset was built to capture.
Dropped: slurs, sexual content mentioning minors, texts > 1,500 chars, exact duplicates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "measuring_hate_speech"
URL = "https://huggingface.co/api/datasets/ucberkeley-dlab/measuring-hate-speech/parquet/default/train/0.parquet"
LICENSE = "CC-BY-4.0"
NODE = "machine.trust_safety.toxicity_harassment"
TARGET_HATE = env_int("TARGET_MHS_HATE", 2400)
TARGET_STANCE = env_int("TARGET_MHS_STANCE", 2100)
PLATFORM = {0: "reddit", 1: "twitter", 2: "youtube", 3: "gab"}

HATE_TEXT = "Is `comment` hate speech against a group of people defined by an identity such as race, religion, " \
    "national origin, gender, sexual orientation, age or disability?"
HATE = {
    "true": "The comment attacks, demeans, dehumanizes or calls for harm against people because of their "
    "group identity",
    "false": "The comment does not attack an identity group, even if it mentions one or is rude",
}
STANCE_TEXT = "Does `comment` attack the identity group it talks about, defend it, or neither?"
STANCE = {
    "attacks": "The comment is hostile toward the group or its members",
    "defends": "The comment supports the group or pushes back against people who attack it",
    "neither": "The comment mentions the group without attacking or defending it",
}

SLUR = re.compile(
    r"\b(nigg\w*|niggu\w*|nigs?|fag|fags|faggot\w*|kikes?|spics?|chinks?|retard\w*|trann(y|ies)|wetbacks?|"
    r"coons?|jigaboos?|spear ?chuck\w*|shit ?skins?|sand ?niggers?|ragheads?|towel ?heads?|dykes?|beaners?|"
    r"gooks?|muzzies?|paki|pakis)\b",
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
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _meta(cid: int, platform: int, t: str, politics_target: float) -> dict:
    flags = []
    if SEXUAL.search(t):
        flags.append("sensitive")
    if POLITICAL.search(t) or politics_target >= 0.5:
        flags.append("political")
    return {"platform": PLATFORM.get(platform), **({"flags": flags} if flags else {})}


def _q(tid, prim, text, options, shape, cid, t, truth, dist, n, meta):
    return Question(
        text=text,
        primitive=prim,
        hemisphere="machine",
        origin="dataset",
        source=NAME,
        options=options,
        state={"comment": t},
        shape=shape,
        node_hint=NODE,
        template_id=tid,
        source_item_id=f"comment:{cid}",
        license=LICENSE,
        truth=truth,
        human=[HumanDist(population="MTurk annotators (Measuring Hate Speech)", distribution=dist, n=n,
                         source=f"ucberkeley-dlab/measuring-hate-speech item {'hatespeech' if prim == 'noul' else 'attack_defend'}")],
        meta=meta,
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    m = pl.read_parquet(raw_dir / "train.parquet", columns=[
        "comment_id", "platform", "text", "hatespeech", "attack_defend", "target_politics"])
    g = (
        m.group_by("comment_id")
        .agg(
            pl.len().alias("n"),
            pl.col("text").first(),
            pl.col("platform").first(),
            (pl.col("hatespeech") == 2).sum().alias("hs_yes"),
            (pl.col("hatespeech") == 0).sum().alias("hs_no"),
            (pl.col("attack_defend") <= 1).sum().alias("ad_def"),
            (pl.col("attack_defend") == 2).sum().alias("ad_neu"),
            (pl.col("attack_defend") >= 3).sum().alias("ad_att"),
            pl.col("target_politics").cast(pl.Float64).mean().alias("tpol"),
        )
        .filter(pl.col("n") >= 3)
        .sort("comment_id")
    )
    items = []
    seen: set[str] = set()
    for r in g.iter_rows(named=True):
        t = " ".join((r["text"] or "").split())
        if len(t) < 15 or len(t) > 1500 or t.lower() in seen or SLUR.search(t):
            continue
        if SEXUAL.search(t) and MINOR.search(t):
            continue
        seen.add(t.lower())
        items.append((r, t))

    # Template A: hate speech yes/no, 40% positive.
    pos, neg = [], []
    for r, t in items:
        k = r["hs_yes"] + r["hs_no"]
        if k < 3:
            continue
        y = r["hs_yes"] / k
        if y >= 0.75:
            pos.append((r, t, y, k))
        elif y <= 0.25:
            neg.append((r, t, y, k))
    n_pos = min(len(pos), round(TARGET_HATE * 0.4))
    picked = [(x, True) for x in hash_order(pos, lambda x: x[0]["comment_id"], "mhs.hate.pos")[:n_pos]]
    picked += [(x, False) for x in hash_order(neg, lambda x: x[0]["comment_id"], "mhs.hate.neg")[: TARGET_HATE - n_pos]]
    for (r, t, y, k), truth in sorted(picked, key=lambda z: z[0][0]["comment_id"]):
        yield _q("mhs.hate_speech", "noul", HATE_TEXT, HATE, "detect", r["comment_id"], t, truth,
                 {"true": round(y, 4), "false": round(1 - y, 4)}, k,
                 _meta(r["comment_id"], r["platform"], t, r["tpol"]))

    # Template B: stance toward the group, balanced thirds.
    buckets: dict[str, list] = {k: [] for k in STANCE}
    for r, t in items:
        cnt = {"attacks": r["ad_att"], "defends": r["ad_def"], "neither": r["ad_neu"]}
        tot = sum(cnt.values())
        if tot < 3:
            continue
        top = max(cnt, key=cnt.get)
        if cnt[top] / tot >= 2 / 3:
            buckets[top].append((r, t, {k: round(v / tot, 4) for k, v in cnt.items()}, tot))
    per = TARGET_STANCE // 3
    for k in STANCE:
        for r, t, dist, tot in sorted(hash_order(buckets[k], lambda x: x[0]["comment_id"], f"mhs.stance.{k}")[:per],
                                      key=lambda z: z[0]["comment_id"]):
            yield _q("mhs.stance", "choice", STANCE_TEXT, STANCE, "classify", r["comment_id"], t, k, dist, tot,
                     _meta(r["comment_id"], r["platform"], t, r["tpol"]))
