"""SkillSpan (Zhang et al. 2022): sentences from real English job postings (StackOverflow tech jobs and a
large job platform), with expert-annotated spans for skills (what the candidate must be able to do, including
soft skills) and knowledge (tools, technologies, fields, qualifications).

Template "skillspan_jobs.requires_skill": Noul "Does `sentence` from a job posting name a skill or knowledge the
job asks for?", truth = the sentence has at least one annotated skill or knowledge span. Sentences of 8+ tokens,
50/50. Company names and places are anonymised in the source (<ORGANIZATION>, <LOCATION>).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "skillspan_jobs"
URL = "https://huggingface.co/api/datasets/jjzha/skillspan/parquet/default/{split}/0.parquet"
SPLITS = ("train", "validation", "test")
TARGET = env_int("TARGET_SKILLSPAN_JOBS", 2500)
LICENSE = "CC-BY-4.0"
TEXT = "Does `sentence` from a job posting name a skill or knowledge the job asks for?"
OPTIONS = {
    "true": "It names at least one thing the candidate should be able to do (including soft skills such as teamwork) "
    "or should know (a tool, technology, field or qualification)",
    "false": "It describes the company, the benefits, the process or the team without naming any required skill or knowledge",
}


def fetch(raw_dir: Path) -> None:
    for s in SPLITS:
        out = raw_dir / f"{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=s), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _detok(tokens: list[str]) -> str:
    s = " ".join(t.replace("\x93", "“").replace("\x94", "”").replace("\x92", "’") for t in tokens)
    s = re.sub(r"\s+([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools = {True: [], False: []}
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, idx, tokens, ts, tk, src in df.select("row", "idx", "tokens", "tags_skill", "tags_knowledge", "source").rows():
            if len(tokens) < 8:
                continue
            sent = _detok(tokens)
            if sent.lower() in seen:
                continue
            seen.add(sent.lower())
            skills = [t for t, g in zip(tokens, ts) if g != "O"]
            know = [t for t, g in zip(tokens, tk) if g != "O"]
            pools[bool(skills or know)].append((f"{split}:{row}", sent, src, bool(skills), bool(know)))
    n_true = TARGET // 2
    items = hash_order(pools[True], lambda x: x[0], "skillspan.t")[:n_true]
    items += hash_order(pools[False], lambda x: x[0], "skillspan.f")[: TARGET - len(items)]
    for sid, sent, src, has_s, has_k in sorted(items):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"sentence": sent[:1500]},
            shape="detect",
            node_hint="machine.people",
            template_id="skillspan_jobs.requires_skill",
            source_item_id=sid,
            license=LICENSE,
            truth=has_s or has_k,
            meta={"posting_source": src, "has_skill_span": has_s, "has_knowledge_span": has_k},
        )
