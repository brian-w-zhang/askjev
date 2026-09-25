"""LinkedIn job postings (Kaggle arshkon/linkedin-job-postings, 2023 snapshot; HF mirror xanderios): real US
postings with the experience level and employment type the employer selected when posting.

Templates:
- "linkedin_jobs.seniority": Choice "What experience level is `job_posting` hiring for?" over LinkedIn's six
  levels, truth = the employer's formatted_experience_level. Round-robin balanced across levels.
- "linkedin_jobs.work_type": Choice "What kind of employment does `job_posting` offer?" over six employment types,
  truth = formatted_work_type ("Other" dropped). Round-robin balanced; postings disjoint from the seniority set.
The posting is the title plus the description; descriptions over 1,500 chars keep the first ~1,050 and the last
~400 characters (requirements often sit at the end) joined by " [...] ".
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "linkedin_jobs"
URL = "https://huggingface.co/api/datasets/xanderios/linkedin-job-postings/parquet/default/train/0.parquet"
TARGET_LEVEL = env_int("TARGET_LINKEDIN_SENIORITY", 2500)
TARGET_TYPE = env_int("TARGET_LINKEDIN_WORK_TYPE", 2000)
MAX_CHARS = 1500
LICENSE = "CC-BY-SA-4.0 (Kaggle arshkon/linkedin-job-postings); HF mirror MIT"
LEVEL_TEXT = "What experience level is `job_posting` hiring for?"
LEVELS = {
    "Internship": ("internship", "A student or recent graduate internship"),
    "Entry level": ("entry_level", "A first job or one needing little prior experience"),
    "Associate": ("associate", "A role needing some experience, below senior level"),
    "Mid-Senior level": ("mid_senior", "An experienced individual contributor or manager"),
    "Director": ("director", "A director who leads a function or department"),
    "Executive": ("executive", "A top executive (C-level, vice president, head of the company)"),
}
TYPE_TEXT = "What kind of employment does `job_posting` offer?"
TYPES = {
    "Full-time": ("full_time", "A permanent full-time job"),
    "Part-time": ("part_time", "A permanent part-time job"),
    "Contract": ("contract", "A contract position for a fixed engagement"),
    "Temporary": ("temporary", "A temporary or seasonal job"),
    "Internship": ("internship", "An internship"),
    "Volunteer": ("volunteer", "An unpaid volunteer position"),
}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _posting(title: str, desc: str) -> str:
    title = " ".join(title.split())
    desc = "\n".join(" ".join(l.split()) for l in desc.splitlines() if l.strip())
    budget = MAX_CHARS - len(title) - 2
    if len(desc) > budget:
        head = desc[: budget - 410].rsplit(" ", 1)[0]
        tail = desc[-400:].split(" ", 1)[-1]
        desc = f"{head} [...] {tail}"
    return f"{title}\n\n{desc}"


def _round_robin(pools: dict[str, list], order: list[str], target: int) -> list:
    out, depth = [], 0
    while len(out) < target and any(depth < len(pools.get(k, [])) for k in order):
        for k in order:
            if depth < len(pools.get(k, [])) and len(out) < target:
                out.append(pools[k][depth])
        depth += 1
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet").filter(
        pl.col("description").is_not_null() & (pl.col("description").str.len_chars() >= 300) & pl.col("title").is_not_null()
    )
    rows = []
    seen: set[str] = set()
    for jid, title, desc, lvl, wt in df.select("job_id", "title", "description", "formatted_experience_level", "formatted_work_type").rows():
        key = " ".join(desc.split()).lower()[:500]
        if key in seen:
            continue
        seen.add(key)
        rows.append((str(jid), title, desc, lvl, wt))
    rows = hash_order(rows, lambda x: x[0], "linkedin.v1")
    lvl_pools: dict[str, list] = defaultdict(list)
    for r in rows:
        if r[3] in LEVELS:
            lvl_pools[r[3]].append(r)
    lvl_items = _round_robin(lvl_pools, list(LEVELS), TARGET_LEVEL)
    used = {r[0] for r in lvl_items}
    type_pools: dict[str, list] = defaultdict(list)
    for r in rows:
        if r[0] not in used and r[4] in TYPES:
            type_pools[r[4]].append(r)
    type_items = _round_robin(type_pools, list(TYPES), TARGET_TYPE)

    for jid, title, desc, lvl, wt in sorted(lvl_items, key=lambda x: int(x[0])):
        yield Question(
            text=LEVEL_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={k: d for k, d in LEVELS.values()},
            state={"job_posting": _posting(title, desc)},
            shape="classify",
            node_hint="machine.people",
            template_id="linkedin_jobs.seniority",
            source_item_id=jid,
            license=LICENSE,
            truth=LEVELS[lvl][0],
            meta={"work_type": wt, "truncated": len(desc) > MAX_CHARS},
        )
    for jid, title, desc, lvl, wt in sorted(type_items, key=lambda x: int(x[0])):
        yield Question(
            text=TYPE_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={k: d for k, d in TYPES.values()},
            state={"job_posting": _posting(title, desc)},
            shape="classify",
            node_hint="machine.people",
            template_id="linkedin_jobs.work_type",
            source_item_id=jid,
            license=LICENSE,
            truth=TYPES[wt][0],
            meta={"experience_level": lvl, "truncated": len(desc) > MAX_CHARS},
        )
