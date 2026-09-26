"""HEAD-QA (Vilares & Gomez-Rodriguez 2019): Spanish healthcare specialization exams, English version, as World factual Choice.

The Spanish Ministry of Health's annual exams for specialist training posts (2013-2017): nursing (EIR),
pharmacology (FIR), psychology (PIR), medicine (MIR), biology (BIR) and chemistry (QIR), with the official answer
key. English text is the dataset's machine translation. Only the three profession exams are kept (nursing,
pharmacy, clinical psychology): medicine is already covered by medmcqa and a spot check found several MIR keys that
look wrong (e.g. an infant vaccine site keyed to the abdomen); biology and chemistry are general science, covered
elsewhere, and carry the most untranslated terms. Choice over the (four or five) answer texts, readable keys,
truth = the keyed answer. Items with an image are skipped. Stems and answers go through medmcqa's cleaner and the
shared mmlu snap filter (no picture/computation stems, no numeric answers such as doses or percentages, no
numbered-statement combos; a wrong "all/none of the above" removed, the item dropped when it is the right one);
near-duplicates of mmlu/medmcqa picks and of each other are skipped. All splits pooled, salted-hash order, capped
per category. Flags as medmcqa: sensitive on sexual/abortion/suicide/poisoning, abortion also political.
"""

from __future__ import annotations

import hashlib
import importlib.util
import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "head_qa"
LICENSE = "MIT (HEAD-QA; exams published by the Spanish Ministerio de Sanidad)"
TARGET = env_int("TARGET_HEAD_QA", 5000)
PER_CATEGORY = env_int("HEAD_QA_PER_CATEGORY", 2000)
SALT = "head-qa-20260926"
URL = "https://huggingface.co/datasets/dvilares/head_qa/resolve/refs%2Fconvert%2Fparquet/en/{split}/0000.parquet"
SPLITS = ("train", "validation", "test")
CATEGORY_NODE = {
    "nursery": "world.health.medicine.nursing",
    "pharmacology": "world.health.medicine.drug",
    "psychology": "world.science.psychology_neuroscience.psychology",
}  # medicine (MIR), biology (BIR), chemistry (QIR) skipped: see the module docstring
EARLIER = ("mmlu", "medmcqa")

_spec = importlib.util.spec_from_file_location("sources.medmcqa", Path(__file__).parents[1] / "medmcqa" / "adapter.py")
MED = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MED)
M = MED.M


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if not out.exists():
            r = httpx.get(URL.format(split=split), follow_redirects=True, timeout=300)
            r.raise_for_status()
            out.write_bytes(r.content)


# Translated "all/none of the above" variants the shared filter misses: removed when wrong, item dropped when right.
META_OPTION = re.compile(r"^(all|none|both|neither)\b.*\b(previous|above|preceding|former|answers?|options?|statements?|"
                         r"choices?)\b.*$|^(all|none|both) (are|is) (correct|true|false|incorrect)$|^it depends\b.*$",
                         re.I)


def _answer(text: str | None) -> str:
    t = MED.JUNK_TAIL.sub("", M.clean(text or ""))
    return t + ")" if t.count("(") > t.count(")") else t  # the tail strip eats a closing parenthesis


def _pool(raw_dir: Path) -> list[dict]:
    seen: set[str] = set()
    for n in EARLIER:
        mod, raw = M.load(n)
        seen |= {it["norm"] for it in mod.selected(raw)}
    pool = []
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for name, cat, qid, q, ra, image, answers in df.select(
                "name", "category", "qid", "qtext", "ra", "image", "answers").iter_rows():
            if cat not in CATEGORY_NODE or (image and image.get("bytes")):
                continue
            stem = MED._stem(q)
            if not stem:
                continue
            stem = re.sub(r"\s*\?+", "?", stem)  # "... from a B ?:" came out as "B ??"
            ans = sorted(answers, key=lambda a: a["aid"])
            ids = [a["aid"] for a in ans]
            if ra not in ids:
                continue
            texts = [_answer(a["atext"]) for a in ans]
            if any(not t or MED.GARBLED.search(t) or len(t) > 150 for t in texts):
                continue
            iid = f"{name}:{qid}"
            order = list(range(len(texts)))  # shuffle per item so the key position carries no signal
            random.Random(int(hashlib.sha256(f"{SALT}:{iid}".encode()).hexdigest()[:16], 16)).shuffle(order)
            right = order.index(ids.index(ra))
            texts = [texts[i] for i in order]
            if META_OPTION.match(texts[right]):
                continue
            keep = [i for i, t in enumerate(texts) if not META_OPTION.match(t)]
            kept = M.snap_filter(stem, [texts[i] for i in keep], keep.index(right))
            if not kept:
                continue
            k = M.item_key(stem, kept[0][kept[1]])
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": iid, "category": cat, "q": stem, "answers": kept[0], "correct": kept[1], "norm": k,
                         "exam": name})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    by_cat: dict[str, list[dict]] = {}
    for it in hash_order(_pool(raw_dir), lambda x: x["id"], SALT):
        by_cat.setdefault(it["category"], []).append(it)
    capped = [it for c in sorted(by_cat) for it in by_cat[c][:PER_CATEGORY]]
    return hash_order(capped, lambda x: x["id"], SALT)[:TARGET]


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: (x["category"], x["id"])):
        blob = " ".join([it["q"], *it["answers"]])
        fl = M.flags(blob)
        if (MED.SEXUAL.search(blob) or MED.SELF_HARM.search(blob)) and "sensitive" not in fl:
            fl.append("sensitive")
        if re.search(r"\babortion\w*|termination of pregnancy|voluntary interruption", blob, re.I) and "political" not in fl:
            fl.append("political")
        text, origin = M.completion_text(it["q"])
        meta = {"category": it["category"], "exam": it["exam"]}
        if fl:
            meta["flags"] = fl
        node = CATEGORY_NODE[it["category"]]
        q = M.choice_question(source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=node,
                              item_id=it["id"], license=LICENSE, meta=meta, origin=origin)
        if q:
            yield q
