"""Moral Stories (Emelin et al. 2021, MIT): crowdsourced short stories with a social norm, a situation, an
actor's intention, and two alternative actions, one that follows the norm and one that breaks it. Asked as
Choice between the two actions, with the situation and intention in state and the norm-following action as
truth."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "moral_stories"
URL = "https://huggingface.co/api/datasets/demelin/moral_stories/parquet/full/train/0.parquet"
LICENSE = "MIT (demelin/moral_stories)"
TARGET = env_int("TARGET_MORAL_STORIES", 5000)
SALT = "moral_stories-v1"
TEXT = "What should the person do in `situation`, given their `intention`?"

SEXUAL = re.compile(
    r"\b(sex\w*|porn\w*|nudes?|naked|orgasm\w*|erotic\w*|condoms?|horny|seduc\w*|topless|strip(per|ping)|"
    r"prostitut\w*|escort|affair|one night stand|hook(ed)? up|slept with|sleep with)\b", re.I)
SELF_HARM = re.compile(r"\b(suicid\w*|kill(ed|ing)? (him|her|them)sel(f|ves)|self[- ]harm\w*|overdos\w*|"
                       r"anorexi\w*|bulimi\w*)\b", re.I)
VIOLENT = re.compile(r"\b(murder\w*|kill\w*|rap(e|ed|ing)|stab\w*|shot|shoot\w*|molest\w*|assault\w*|strangl\w*|"
                     r"gun|guns|knife|beat(s|ing)? (him|her|them|up))\b", re.I)
POLITICAL = re.compile(r"\b(abortion|republican\w*|democrat\w*|election\w*|vot(e|es|ed|ing) for|immigra\w*|"
                       r"gun control|trump|biden|obama|clinton|liberal|conservative|pro-life|pro-choice)\b", re.I)
MINORS = re.compile(r"\b(child|children|kids?|minors?|teen\w*|underage|\d{1,2} ?(yo|y/o|year ?old)|little (boy|girl)|"
                    r"daughter|son|students?|high ?school|middle school|step(son|daughter)|niece|nephew)\b", re.I)
DROP = re.compile(r"\b(nigg\w*|fag\w*|retard\w*|tranny|incest|pedo\w*|paedo\w*)\b", re.I)

NODES = [  # (regex over the norm, node): first match wins
    (re.compile(r"\b(animals?|pets?|dogs?|cats?|puppy|kitten|birds?|fish|wildlife|litter\w*|environment\w*|"
                r"recycl\w*|nature|plants?|trees?|pollut\w*)\b", re.I),
     "self.values.animals_environment.animal_nature_dilemmas"),
    (re.compile(r"\b(cheat(s|ing)? on|loyal\w*|disloyal|betray\w*|abandon\w*|stand by|stick by|back out)\b", re.I),
     "self.values.moral_foundations.loyalty"),
    (re.compile(r"\b(lie|lies|lying|lied|liars?|honest\w*|dishonest\w*|truth\w*|cheat\w*|steal\w*|stole|theft|"
                r"secrets?|promises?|trust\w*|deceiv\w*|decept\w*|plagiar\w*|fraud\w*|mislead\w*|shoplift\w*)\b", re.I),
     "self.values.honesty_trust.honesty_dilemmas"),
    (re.compile(r"\b(donat\w*|charit\w*|homeless|volunteer\w*|generous|generosity|needy|less fortunate|strangers?|"
                r"in need|tip|tips|tipping)\b", re.I), "self.values.giving_charity"),
    (re.compile(r"\b(fair\w*|unfair\w*|justice|revenge|punish\w*|credit|equal\w*|discriminat\w*|racis\w*|sexis\w*|"
                r"prejudic\w*|exclud\w*|judge|judging|share|sharing|take advantage)\b", re.I),
     "self.values.fairness_justice"),
    (re.compile(r"\b(parents?|elders?|obey\w*|rules?|laws?|illegal\w*|authorit\w*|teachers?|boss\w*|police|"
                r"disrespect\w*|respect\w*|traditions?)\b", re.I), "self.values.moral_foundations.authority"),
    (re.compile(r"\b(disgust\w*|gross|drugs?|drunk\w*|alcohol\w*|drink\w*|smok\w*|hygien\w*|dirty|clean\w*|"
                r"bodily|litter)\b", re.I), "self.values.moral_foundations.purity"),
    (re.compile(r"\b(hurt\w*|harm\w*|abus\w*|kind\w*|unkind|cruel\w*|bully\w*|safe\w*|danger\w*|children|kids?|"
                r"child|sick|care|caring|mean|insult\w*|yell\w*|hit|comfort\w*|support\w*|help\w*)\b", re.I),
     "self.values.moral_foundations.care"),
    (re.compile(r"\b(goals?|dreams?|career|success\w*|money|health\w*|hard work|ambitio\w*|freedom|"
                r"yourself|your own)\b", re.I), "self.values.life_values"),
]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "full.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s[:1].upper() + s[1:]


def _slug(words: list[str], maxlen: int) -> str:
    k = ""
    for w in words:
        if len(k) + len(w) + 1 > maxlen:
            break
        k = f"{k}_{w}" if k else w
    return k or (words[0][:maxlen] if words else "")


def _keys(a: str, b: str) -> tuple[str, str] | None:
    """Slug keys from the first words of each action; the shared leading actor name is dropped."""
    wa, wb = (re.findall(r"[a-z0-9]+", x.lower().replace("'", "")) for x in (a, b))
    if len(wa) > 1 and len(wb) > 1 and wa[0] == wb[0]:
        wa, wb = wa[1:], wb[1:]
    for n in (40, 60, 90):
        ka, kb = _slug(wa, n), _slug(wb, n)
        if ka and kb and ka != kb:
            return ka, kb
    return None


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "full.parquet")
    pool, seen = [], set()
    for r in df.iter_rows(named=True):
        sit, intent = _clean(r["situation"]), _clean(r["intention"])
        good, bad = _clean(r["moral_action"]), _clean(r["immoral_action"])
        if not (sit and intent and good and bad) or good.lower() == bad.lower():
            continue
        blob = " ".join([r["norm"] or "", sit, intent, good, bad])
        # Garbled stories where an action names a different actor than the intention ("Debbie wants ...",
        # "Karen seduces ...") are dropped, as is sexual content that mentions minors.
        actor = intent.split()[0]
        named = all(re.search(rf"\b{re.escape(actor)}\b", x, re.I) for x in (good, bad))
        if DROP.search(blob) or (SEXUAL.search(blob) and MINORS.search(blob)) or not named:
            continue
        keys = _keys(good, bad)
        if keys is None:
            continue
        dup = (sit.lower(), good.lower(), bad.lower())
        if dup in seen:
            continue
        seen.add(dup)
        pool.append((r, sit, intent, good, bad, keys, blob))

    for r, sit, intent, good, bad, (kg, kb), blob in hash_order(pool, key=lambda x: x[0]["ID"], salt=SALT)[:TARGET]:
        # Deterministic order: the moral action comes first for half the items (by a hash of the id).
        moral_first = int(hashlib.sha256(f"{SALT}|order|{r['ID']}".encode()).hexdigest(), 16) % 2 == 0
        opts = [(kg, good), (kb, bad)] if moral_first else [(kb, bad), (kg, good)]
        flags = []
        if SEXUAL.search(blob) or SELF_HARM.search(blob) or VIOLENT.search(blob):
            flags.append("sensitive")
        if POLITICAL.search(blob):
            flags.append("political")
        norm = _clean(r["norm"])
        node = next((n for rx, n in NODES if rx.search(norm)), "self.values")
        meta = {"norm": norm, "moral_consequence": _clean(r["moral_consequence"]),
                "immoral_consequence": _clean(r["immoral_consequence"])}
        if flags:
            meta["flags"] = flags
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options=dict(opts),
            state={"situation": sit, "intention": intent},
            node_hint=node,
            source_item_id=r["ID"],
            license=LICENSE,
            truth=kg,
            meta=meta,
        )
