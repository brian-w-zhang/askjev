"""HotpotQA comparison questions (Yang et al. 2018) asked closed-book: World factual with truth.

Every HotpotQA comparison question contrasts the two Wikipedia articles in its supporting facts. Yes/no ones
("Were Scott Derrickson and Ed Wood of the same nationality?") become Noul; the rest become Choice over the two
article subjects when both are named in the question and the gold answer is one of them ("Which band, Letters to
Cleo or Screaming Trees, had more members?"). No passage is passed: it is a knowledge question.
"""

from __future__ import annotations

import importlib.util
import re
import unicodedata
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "hotpot_compare"
LICENSE = "CC BY-SA 4.0"
TARGET = env_int("TARGET_HOTPOT_COMPARE", 3000)
CHOICE_SHARE = 0.6  # of TARGET; Noul fills the rest, half yes / half no
SALT = "hotpot_compare-20260924"
FILES = {"train_0.parquet": "distractor/train/0.parquet", "train_1.parquet": "distractor/train/1.parquet",
         "validation_0.parquet": "distractor/validation/0.parquet"}

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

AUX = re.compile(r"^(is|are|was|were|do|does|did|can|could|has|have|had|will|would|should)\b", re.I)
NON_YEAR_DIGIT = re.compile(r"\d(?<!\b\d{4})(?!\d{3}\b)|\b\d{1,3}\b|\b\d{5,}\b|\d,\d")
TIMELY = re.compile(r"\b(deceased|alive|living|still|currently|current|now|today|recent\w*|latest)\b", re.I)
DISAMBIG = re.compile(r"\s*\([^)]*\)\s*$")


def fetch(raw_dir: Path) -> None:
    M.hf_fetch(raw_dir, "hotpotqa/hotpot_qa", FILES)


def _toks(s: str) -> set[str]:
    return set(M.norm(s).split()) - {"of", "and", "in", "de", "la", "le"}


def _match(answer: str, name: str) -> bool:
    a, n = _toks(answer), _toks(name)
    if not a or not n:
        return False
    return a <= n or n <= a or len(a & n) / len(a | n) >= 0.5


def _text(q: str) -> str | None:
    q = re.sub(r"\s+", " ", q).strip()
    q = re.sub(r"\s+([?,.])", r"\1", q)
    q = re.sub(r",(?=\S)", ", ", q)
    if not q.endswith("?"):
        if not (AUX.match(q) or re.match(r"^(which|who|what)\b", q, re.I)):
            return None
        q = q.rstrip(".") + "?"
    if not 20 <= len(q) <= 200 or q.count("?") != 1 or NON_YEAR_DIGIT.search(q) or TIMELY.search(q):
        return None
    return q[0].upper() + q[1:]


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", re.sub(r"^the\s+", "", s.strip(), flags=re.I)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:48]


def _pool(raw_dir: Path) -> tuple[list[dict], list[dict]]:
    choice, noul, seen = [], [], set()
    for f in FILES:
        df = pl.read_parquet(raw_dir / f, columns=["id", "question", "answer", "type", "supporting_facts"])
        for qid, q, ans, typ, sf in df.filter(pl.col("type") == "comparison").iter_rows():
            text = _text(q)
            if not text:
                continue
            key = M.norm(text)
            if key in seen:
                continue
            titles = list(dict.fromkeys(sf["title"]))
            if len(titles) != 2:
                continue
            a = ans.strip().lower()
            it = {"id": f"{f.split('_')[0]}:{qid}", "q": text, "titles": titles}
            if a in ("yes", "no"):
                if not AUX.match(text):
                    continue
                seen.add(key)
                noul.append({**it, "truth": a == "yes"})
                continue
            names = [DISAMBIG.sub("", t) for t in titles]
            low = text.lower()
            if any(n.lower() not in low for n in names) or len({_slug(n) for n in names}) != 2:
                continue  # both subjects must be named in the question
            hits = [i for i, n in enumerate(names) if _match(ans, n)]
            if len(hits) != 1:
                continue
            # show the options in the order the question names them
            order = sorted(range(2), key=lambda i: low.index(names[i].lower()))
            seen.add(key)
            choice.append({**it, "names": [names[i] for i in order], "truth": order.index(hits[0]), "answer": ans})
    return choice, noul


def normalize(raw_dir: Path) -> Iterator[Question]:
    choice, noul = _pool(raw_dir)
    n_choice = min(len(choice), round(TARGET * CHOICE_SHARE))
    n_noul = TARGET - n_choice
    picked = hash_order(choice, lambda x: x["id"], SALT)[:n_choice]
    yes = hash_order([x for x in noul if x["truth"]], lambda x: x["id"], SALT)
    no = hash_order([x for x in noul if not x["truth"]], lambda x: x["id"], SALT)
    picked += yes[: n_noul // 2] + no[: n_noul - n_noul // 2]
    for it in sorted(picked, key=lambda x: x["id"]):
        meta = {"titles": it["titles"], "split": it["id"].split(":")[0]}
        fl = M.flags(it["q"])
        if fl:
            meta["flags"] = fl
        node = M.topic_hint(it["q"], title=it["titles"][0], within="world")
        if "names" in it:
            opts = {_slug(n): n for n in it["names"]}
            meta["answer"] = it["answer"]
            yield Question(text=it["q"], primitive="choice", hemisphere="world", kind="factual", origin="dataset",
                           source=NAME, options=opts, truth=_slug(it["names"][it["truth"]]), node_hint=node,
                           source_item_id=it["id"], license=LICENSE, meta=meta)
        else:
            yield Question(text=it["q"], primitive="noul", hemisphere="world", kind="factual", origin="dataset",
                           source=NAME, truth=it["truth"], node_hint=node, source_item_id=it["id"], license=LICENSE,
                           meta=meta)
