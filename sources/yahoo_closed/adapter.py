"""Yahoo! Answers closed questions: real yes/no and "which is better, A or B?" titles people asked (2005-2007).

Source: Yahoo! Answers Topics (Zhang, Zhao & LeCun 2015) train split, 1.4M questions, title only. The strict
filter chain, choice parsing, dedupe key and keyword tagging are quora_closed's (imported, not copied), with a few
Yahoo-specific drops on top: the Family & Relationships category entirely, titles about Yahoo! Answers itself
(points, best answer), SHOUTED titles, and names pinned to the mid-2000s news cycle. World only: self-tagged
questions are dropped. No node_hint (placed by the beam walk). No truth.
"""

from __future__ import annotations

import hashlib
import html
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

_spec = importlib.util.spec_from_file_location(
    "sources.quora_closed", Path(__file__).parents[1] / "quora_closed" / "adapter.py")
qc = importlib.util.module_from_spec(_spec)
sys.modules["sources.quora_closed"] = qc
_spec.loader.exec_module(qc)
_cspec = importlib.util.spec_from_file_location(
    "sources.concreteness", Path(__file__).parents[1] / "concreteness" / "adapter.py")
_c = importlib.util.module_from_spec(_cspec)
sys.modules["sources.concreteness"] = _c
_cspec.loader.exec_module(_c)

NAME = "yahoo_closed"
BASE = ("https://huggingface.co/api/datasets/community-datasets/yahoo_answers_topics/parquet/"
        "yahoo_answers_topics/train")
FILES = {f"train_{i}.parquet": f"{BASE}/{i}.parquet" for i in (0, 1)}
LICENSE = "Yahoo! Answers Comprehensive Q&A (Yahoo Webscope L6): non-commercial research use"
BASE_TARGET = 8000  # the original sample; a larger TARGET keeps it and tops up (prefix-stable)
TARGET = env_int("TARGET_YAHOO_CLOSED", 12000)
SALT = "yahoo_closed-20260925"
TOPICS = ["society_culture", "science_mathematics", "health", "education_reference", "computers_internet", "sports",
          "business_finance", "entertainment_music", "family_relationships", "politics_government"]
SKIP_TOPICS = {"family_relationships"}  # too personal / sexual for a public-facing tree

YAHOO = re.compile(r"\b(yahoo\w*|y!a|y!|best answers?|\d+ ?(pts|points)|points|answerers?|this site|on here|"
                   r"360|myspace|geocities|aol|msn|ipod\w*|zune|psp|ps3|wii)\b", re.I)
ERA = re.compile(  # names and events of the 2005-2007 news cycle: the question is pinned to a moment that has passed
    r"\b(bush|dubya|cheney|rumsfeld|kerry|gore|saddam|osama|bin laden|blair|chirac|katrina|tsunami|anna nicole|"
    r"paris hilton|britney|k-?fed|lindsay lohan|tom cruise|katie holmes|brangelina|american idol|idol|"
    r"sanjaya|taylor hicks|chris daughtry|fantasia|world cup|super ?bowl|world series|nba finals|playoffs?|"
    r"da vinci code|harry potter|pluto)\b",
    re.I,
)
EXTRA_MULTI = re.compile(r"\s(and|&) (is|are|was|were|do|does|did|can|could|would|will|should|how|what|why|where|"
                         r"when|who|which)\b", re.I)  # "Is it possible ... and are there people doing it?"
MESSY = re.compile(r"[()/&]| - |,\S|[.,]\?$|\b(\w+) \1\b|[a-z]\.[a-z]|\b(scare|bother|annoy|surprise|interest|remind|offend)s? you\b", re.I)
# kind mix: the corpus is short on evaluative and long on factual, so evaluative/social/forecast are taken first
# up to these shares of TARGET and factual fills the rest.
KIND_SHARE = {"evaluative": 0.40, "social": 0.10, "forecast": 0.05}
FUNNEL: Counter = Counter()


# Yahoo misspellings recur hundreds of times ("ther", "stoped"), so corpus frequency alone can't catch them: a
# lowercase word must be a Brysbaert et al. 2014 lemma (40k English words), a regular inflection of one, or very
# common in the titles (slang, brands).
COMMON = 1000
DICT: set[str] = set()


def _known(w: str, vocab: Counter) -> bool:
    w = w.strip("'")
    if w in DICT or vocab[w] >= COMMON:
        return True
    stems = []
    for suf in ("s", "es", "ed", "d", "ing", "er", "est", "ly", "'s"):
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            b = w[: -len(suf)]
            stems += [b, b + "e"] + ([b[:-1]] if len(b) >= 3 and b[-1] == b[-2] else [])  # stopped -> stop
    for suf in ("ies", "ied", "ier", "iest", "ily"):
        if w.endswith(suf):
            stems.append(w[: -len(suf)] + "y")
    return any(b in DICT for b in stems)


def _typo(q: str, vocab: Counter) -> bool:
    return any(not _known(w, vocab) for w in re.findall(r"\b[a-z][a-z']*\b", q.split(" ", 1)[-1]))


def fetch(raw_dir: Path) -> None:
    _c.fetch_brysbaert(raw_dir)
    for fn, url in FILES.items():
        out = raw_dir / fn
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _pool(raw_dir: Path) -> list[dict]:
    DICT.update(w for w in _c.read_brysbaert(raw_dir / _c.FILE) if " " not in w)
    qc._typo = _typo  # quora_closed's _keep calls this module-level name
    df = pl.concat([pl.read_parquet(raw_dir / fn, columns=["id", "topic", "question_title"]) for fn in FILES])
    FUNNEL["0_titles"] = df.height
    df = df.filter(~pl.col("topic").is_in([TOPICS.index(t) for t in SKIP_TOPICS]))
    FUNNEL["1_not_family_relationships"] = df.height
    topic_of: dict[str, int] = {}
    for tid, topic, title in zip(df["id"].to_list(), df["topic"].to_list(), df["question_title"].to_list()):
        t = " ".join(html.unescape(title or "").replace("\\n", " ").split())
        if t and t not in topic_of:
            topic_of[t] = topic
    uniq = sorted(topic_of)
    FUNNEL["2_unique_titles"] = len(uniq)
    vocab = qc._vocab(uniq)
    # capitalized-name vocabulary: a word written Capitalized mid-title most of the time is a proper noun, so a
    # title that writes it in lowercase ("is billy mehmet any good") is sloppily cased and dropped
    cap, low = Counter(), Counter()
    for t in uniq:
        for w in t.split()[1:]:
            w = w.strip(".,?!:;\"'")
            if w.isalpha():
                (cap if w[0].isupper() and w[1:].islower() else low if w.islower() else Counter())[w.lower()] += 1
    names = {w for w, c in cap.items() if c >= 20 and c >= 2 * low[w]}

    kept: dict[str, dict] = {}
    for raw in hash_order(uniq, lambda x: x, SALT + "-dedupe"):
        if sum(c.isupper() for c in raw) > 0.4 * sum(c.isalpha() for c in raw):
            continue  # SHOUTED
        if YAHOO.search(raw) or ERA.search(raw):
            FUNNEL["3_yahoo_or_era_dropped"] += 1
            continue
        words = raw.split()
        if len(words) >= 4 and sum(w[:1].isupper() for w in words[1:]) >= 0.6 * (len(words) - 1):
            FUNNEL["3_title_case_dropped"] += 1
            continue  # Title Case Titles are usually headline-ish or mis-cased names
        if EXTRA_MULTI.search(raw) or MESSY.search(raw) or \
                any(w in names for w in re.findall(r"\b[a-z]+\b", raw.split(" ", 1)[-1])):
            FUNNEL["3_messy_or_lowercased_name_dropped"] += 1
            continue
        it = qc._keep(raw, vocab)
        if not it:
            continue
        nk = qc._norm_key(it["q"])
        if nk in kept:
            FUNNEL["4_duplicates_dropped"] += 1
            continue
        it["raw"], it["topic"] = raw, TOPICS[topic_of[raw]]
        it["hemisphere"], it["kind"] = qc.tag(it["q"], it["primitive"] == "choice")
        if it["hemisphere"] != "world":
            FUNNEL["5_self_dropped"] += 1
            continue
        kept[nk] = it
    FUNNEL["6_pool_world"] = len(kept)
    return list(kept.values())


def normalize(raw_dir: Path) -> Iterator[Question]:
    pool = _pool(raw_dir)
    FUNNEL.update({f"7_pool_kind_{k}": v for k, v in Counter(x["kind"] for x in pool).items()})
    order = hash_order(pool, lambda x: x["raw"], SALT)

    def select(cands: list[dict], n: int) -> list[dict]:
        out = []
        for kind, share in KIND_SHARE.items():
            out += [x for x in cands if x["kind"] == kind][: int(n * share)]
        have = {id(x) for x in out}
        return out + [x for x in cands if x["kind"] not in KIND_SHARE and id(x) not in have][: n - len(out)]

    # The original sample is the kind-share selection at BASE_TARGET; a larger TARGET tops it up with the same
    # selection over the rest of the pool (then anything left, if a kind runs dry), so it contains the smaller one.
    picked = select(order, min(TARGET, BASE_TARGET))
    if TARGET > BASE_TARGET:
        have = {id(x) for x in picked}
        rest = [x for x in order if id(x) not in have]
        extra = select(rest, TARGET - BASE_TARGET)
        have |= {id(x) for x in extra}
        extra += [x for x in rest if id(x) not in have][: TARGET - BASE_TARGET - len(extra)]
        picked += extra
    picked = sorted(picked, key=lambda x: x["raw"])
    FUNNEL.update({f"8_picked_kind_{k}": v for k, v in Counter(x["kind"] for x in picked).items()})
    FUNNEL["8_picked"] = len(picked)
    qc.FUNNEL.clear()
    for it in picked:
        q = it["q"]
        flags = []
        if qc.POLITICAL.search(re.sub(r"\belectric\w*", "", q, flags=re.I)):  # quora's elect\w* hits "electricity"
            flags.append("political")
        if qc.SENSITIVE.search(q):
            flags.append("sensitive")
        meta = {"yahoo_title": it["raw"], "yahoo_topic": it["topic"]}
        if flags:
            meta["flags"] = flags
        options = None
        if it["primitive"] == "choice":
            options = {qc.slug(o): o for o in it["opts"]}
            if len(options) != len(it["opts"]):
                continue
        yield Question(
            text=q,
            primitive=it["primitive"],
            hemisphere="world",
            kind=it["kind"],
            origin="dataset",
            source=NAME,
            options=options,
            source_item_id=hashlib.sha1(it["raw"].encode()).hexdigest()[:16],
            license=LICENSE,
            meta=meta,
        )
    print("yahoo_closed funnel:", dict(sorted(FUNNEL.items())))
