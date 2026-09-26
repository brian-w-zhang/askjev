"""databricks-dolly-15k: instructions written by Databricks employees, each for a task category they chose.

Template "dolly.task_type": one Choice per instruction (with its reference passage when the author gave
one) over the kinds of task an AI assistant is being asked to do, truth = the author's category. Dolly's
open_qa and general_qa were written to overlapping guidelines and are not separable from the text (both
are knowledge questions without a passage), so they are merged into `open_question`. Balanced across the
seven keys, seeded, exact-duplicate instructions dropped.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "dolly_tasks"
URL = "https://huggingface.co/api/datasets/databricks/databricks-dolly-15k/parquet/default/train/0.parquet"
TARGET = env_int("TARGET_DOLLY_TASKS", 2500)
SALT = "dolly_tasks.v1"
LICENSE = "CC-BY-SA-3.0"
TEXT = "What kind of task does `prompt` ask an AI assistant to do (using `context` when a passage is given)?"

OPTIONS = {
    "open_question": "Answer a question from general knowledge, with no passage to work from",
    "closed_qa": "Answer a question using only the facts in the given passage",
    "information_extraction": "Pull specific facts, names or lists out of the given passage",
    "summarization": "Summarize the given passage",
    "classification": "Sort or label items into categories, or pick which category something belongs to",
    "brainstorming": "Come up with a list of ideas, suggestions or options",
    "creative_writing": "Write original text such as a story, poem, letter, speech or essay",
}
MAP = {"open_qa": "open_question", "general_qa": "open_question"}

SLURS = re.compile(r"\b(n[i1]gg(er|a|ers|as)|fag(got)?s?|kikes?|spics?|chinks?|trann(y|ies))\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").with_row_index("idx")
    by: dict[str, list[dict]] = defaultdict(list)
    seen: set[str] = set()
    for r in df.iter_rows(named=True):
        ins = (r["instruction"] or "").strip()
        ctx = (r["context"] or "").strip()
        if len(ins) < 8 or len(ins) > 1500 or SLURS.search(ins + " " + ctx):
            continue
        k = re.sub(r"\W+", " ", ins.lower()).strip()
        if k in seen:
            continue
        seen.add(k)
        key = MAP.get(r["category"], r["category"])
        assert key in OPTIONS, key
        by[key].append({"idx": r["idx"], "ins": ins, "ctx": ctx, "cat": r["category"]})

    per = TARGET // len(OPTIONS)
    extra = TARGET - per * len(OPTIONS)
    picked = []
    for i, key in enumerate(sorted(OPTIONS)):
        n = per + (1 if i < extra else 0)
        picked += [(key, x) for x in hash_order(by[key], lambda x: x["idx"], SALT)[:n]]
    picked.sort(key=lambda kx: kx[1]["idx"])

    for key, x in picked:
        ctx = x["ctx"]
        if len(ctx) > 1500:
            ctx = ctx[:1500].rsplit(" ", 1)[0] + " ..."
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"prompt": x["ins"], "context": ctx or "(no passage given)"},
            shape="route",
            node_hint="machine.ai_systems.model_routing",
            template_id="dolly.task_type",
            source_item_id=f"train:{x['idx']}",
            license=LICENSE,
            truth=key,
            meta={"category_raw": x["cat"]},
        )
