"""Civil Comments (Jigsaw / Borkan et al. 2019): public news-site comments with crowd toxicity fractions.

Each comment was rated by several crowd workers; `toxicity` is the fraction who called it toxic or very
toxic, and each sub-attribute (insult, identity_attack, threat, obscene, sexual_explicit) is the fraction
who flagged that attribute. Source: the HF `google/civil_comments` test split (97,320 comments). The HF
export has no annotator counts, so HumanDist.n is None.

Templates:
- "civil_comments.toxic" (Noul): truth = toxicity >= 0.5, ~40% positive. HumanDist = the rater fraction.
- "civil_comments.harm_kind" (Choice): which kind of harm, truth = on toxic comments, the single highest sub-attribute if
  >= 0.5 (ties dropped), else `none` (only clean comments: toxicity < 0.5 and every sub-attribute < 0.2).
  Stratified across the five harm kinds, with `none` at ~30%.
Dropped: comments with slurs, sexual content mentioning minors, texts > 1,500 chars (truncation could cut
the toxic part), exact duplicates. Flags: `sensitive` when sexual_explicit >= 0.3 or sexual words;
`political` for parties, elections, named politicians and hot-button issues.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "civil_comments"
URL = "https://huggingface.co/api/datasets/google/civil_comments/parquet/default/test/0.parquet"
LICENSE = "CC0-1.0"
NODE = "machine.trust_safety.toxicity_harassment"
TARGET_TOXIC = env_int("TARGET_CIVIL_COMMENTS", 2500)
TARGET_KIND = env_int("TARGET_CIVIL_COMMENTS_KIND", 2000)
POS_SHARE = 0.40
NONE_SHARE = 0.30

TOXIC_TEXT = "Is `comment` toxic, meaning rude, disrespectful or likely to make someone leave the discussion?"
TOXIC = {
    "true": "The comment is rude, disrespectful or unreasonable enough that someone might leave the discussion",
    "false": "The comment stays civil, even if it disagrees, criticizes or is blunt",
}
KIND_TEXT = "Which kind of harm, if any, does `comment` contain?"
KINDS = {
    "insult": "Insulting, demeaning or name-calling language aimed at a person or group",
    "identity_attack": "Negative or hateful remarks about people because of their race, religion, gender, "
    "sexual orientation, disability or other identity",
    "threat": "A wish or intention to hurt, injure or kill someone",
    "obscene": "Swearing, cursing or vulgar language",
    "sexual_explicit": "References to sexual acts, sexual body parts or other lewd content",
    "none": "None of these: the comment contains no insult, identity attack, threat, obscenity or sexual content",
}
SUBS = ["insult", "identity_attack", "threat", "obscene", "sexual_explicit"]

SLUR = re.compile(r"\b(nigg\w*|fag|fags|faggot\w*|kikes?|spics?|chinks?|retard\w*|trann(y|ies)|wetbacks?)\b", re.I)
MINOR = re.compile(r"\b(child\w*|kids?|minors?|teen\w*|underage|boys?|girls?|pedo\w*|paedo\w*)\b", re.I)
SEXUAL = re.compile(
    r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|erotic\w*|horny|orgasm\w*|masturbat\w*|rape\w*|raping|"
    r"dick|cock|pussy|penis|vagina|blowjob\w*)\b",
    re.I,
)
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|trudeau\w*|harper|sanders|bernie|pence|putin|mcconnell|"
    r"pelosi|biden|romney|cruz|rubio|gop|republican\w*|democrat\w*|dems?|liberals?|conservatives?|tory|tories|"
    r"ndp|election\w*|elect(ed)?|vot(e|es|ed|er|ers|ing)|ballot\w*|campaign\w*|congress\w*|senat\w*|"
    r"parliament\w*|abortion\w*|pro-life|pro-choice|guns?|nra|second amendment|2nd amendment|immigra\w*|"
    r"refugees?|illegals?|deport\w*|border wall|brexit|left-?wing|right-?wing|leftists?|alt-right|"
    r"socialis\w*|feminis\w*|notley|wynne|kenney|legislat\w*)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(rows):
    """(row, text, scores) for usable, deduplicated comments."""
    seen: set[str] = set()
    out = []
    for row, text, *vals in rows:
        t = " ".join((text or "").split())
        key = t.lower()
        if len(t) < 15 or len(t) > 1500 or key in seen or SLUR.search(t):
            continue
        seen.add(key)
        sc = dict(zip(["toxicity", "severe_toxicity", *SUBS], (round(float(v), 4) for v in vals)))
        if (sc["sexual_explicit"] >= 0.3 or SEXUAL.search(t)) and MINOR.search(t):
            continue
        out.append((row, t, sc))
    return out


def _meta(t: str, sc: dict) -> dict:
    flags = []
    if sc["sexual_explicit"] >= 0.3 or SEXUAL.search(t):
        flags.append("sensitive")
    if POLITICAL.search(t):
        flags.append("political")
    return {"split": "test", "scores": sc, **({"flags": flags} if flags else {})}


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "test.parquet").with_row_index("row")
    items = _clean(df.select("row", "text", "toxicity", "severe_toxicity", *SUBS).iter_rows())

    # Template A: toxic yes/no, 40% positive.
    pos = [x for x in items if x[2]["toxicity"] >= 0.5]
    neg = [x for x in items if x[2]["toxicity"] < 0.5]
    n_pos = min(len(pos), round(TARGET_TOXIC * POS_SHARE))
    picked = hash_order(pos, lambda x: x[0], "cc.toxic.pos")[:n_pos]
    picked += hash_order(neg, lambda x: x[0], "cc.toxic.neg")[: TARGET_TOXIC - n_pos]
    for row, t, sc in sorted(picked, key=lambda x: x[0]):
        f = sc["toxicity"]
        yield Question(
            text=TOXIC_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=TOXIC,
            state={"comment": t},
            shape="detect",
            node_hint=NODE,
            template_id="civil_comments.toxic",
            source_item_id=f"test:{row}",
            license=LICENSE,
            truth=f >= 0.5,
            human=[
                HumanDist(
                    population="Civil Comments raters",
                    distribution={"true": f, "false": round(1 - f, 4)},
                    n=None,
                    source="google/civil_comments toxicity fraction",
                )
            ],
            meta=_meta(t, sc),
        )

    # Template B: harm kind. Positive classes need a unique top sub-attribute >= 0.5.
    by_kind: dict[str, list] = {k: [] for k in KINDS}
    for x in items:
        sc = x[2]
        vals = sorted(((sc[s], s) for s in SUBS), reverse=True)
        if sc["toxicity"] >= 0.5 and vals[0][0] >= 0.5 and vals[0][0] > vals[1][0]:
            by_kind[vals[0][1]].append(x)
        elif sc["toxicity"] < 0.5 and vals[0][0] < 0.2:
            by_kind["none"].append(x)
    n_none = round(TARGET_KIND * NONE_SHARE)
    quota = TARGET_KIND - n_none
    # Water-fill the harm quota across the five kinds (rare kinds give their slack to the others).
    ordered = {k: hash_order(by_kind[k], lambda x: x[0], f"cc.kind.{k}") for k in KINDS}
    take = {k: 0 for k in SUBS}
    while quota > 0:
        open_ = [k for k in SUBS if take[k] < len(ordered[k])]
        if not open_:
            break
        share = max(1, quota // len(open_))
        for k in open_:
            add = min(share, len(ordered[k]) - take[k], quota)
            take[k] += add
            quota -= add
            if quota == 0:
                break
    take["none"] = n_none
    for k in KINDS:
        for row, t, sc in sorted(ordered[k][: take[k]], key=lambda x: x[0]):
            yield Question(
                text=KIND_TEXT,
                primitive="choice",
                hemisphere="machine",
                origin="dataset",
                source=NAME,
                options=KINDS,
                state={"comment": t},
                shape="classify",
                node_hint=NODE,
                template_id="civil_comments.harm_kind",
                source_item_id=f"test:{row}",
                license=LICENSE,
                truth=k,
                meta=_meta(t, sc) | ({"flags": sorted({*_meta(t, sc).get("flags", []), "sensitive"})}
                                     if k == "sexual_explicit" else {}),
            )
