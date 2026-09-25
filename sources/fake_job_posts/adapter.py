"""EMSCAD, the Employment Scam Aegean Dataset (Vidros et al. 2017, University of the Aegean): 17,880 real
job ads from the Workable applicant-tracking system, 866 of them labelled fraudulent by Workable staff.
HF copy victor/real-or-fake-fake-jobposting-prediction (the Kaggle "Real or Fake" release).

Template "fake_job_posts.fraudulent" (Noul, node trust_safety.spam_phishing): is the posting a
fraudulent listing. The posting is rebuilt from its text fields (title, location, department, salary,
employment type, company profile, description, requirements, benefits); empty fields are left out, as a
reader of the ad would see them. Truth = fraudulent. All unique fraudulent posts are kept (653, ~33%), the
rest are real posts in salted hash order.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "fake_job_posts"
URL = "https://huggingface.co/api/datasets/victor/real-or-fake-fake-jobposting-prediction/parquet/default/train/0.parquet"
TARGET = env_int("TARGET_FAKE_JOB_POSTS", 2000)
LICENSE = "CC0-1.0 (Kaggle/HF release of EMSCAD)"
TEXT = "Is `job_posting` a fraudulent listing?"
CRITERIA = {
    "true": "The posting is a scam or fake job ad, not a genuine opening at a real employer",
    "false": "The posting is a genuine job opening",
}
# (field, label, max chars)
FIELDS = [
    ("title", "Title", 150), ("location", "Location", 100), ("department", "Department", 80),
    ("salary_range", "Salary range", 40), ("employment_type", "Employment type", 40),
    ("required_experience", "Experience", 40), ("company_profile", "Company profile", 300),
    ("description", "Description", 650), ("requirements", "Requirements", 300), ("benefits", "Benefits", 200),
]
PLACEHOLDER = re.compile(r"#(URL|EMAIL|PHONE)_[0-9a-f]+#")
GLUE = re.compile(r"([.!?:;)])([A-Z])")
SENSITIVE = re.compile(r"\b(sex|sexual\w*|porn\w*|nude\w*|escort\w*|adult entertainment)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "train.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(s) -> str:
    if s is None:
        return ""
    s = html.unescape(str(s))
    s = PLACEHOLDER.sub(lambda m: f"[{m.group(1).lower()} removed]", s)  # the release's anonymised links
    s = GLUE.sub(r"\1 \2", s)  # the release strips line breaks, gluing sentences together
    return " ".join(s.split())


def _cut(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def _posting(r: dict) -> str:
    lines = []
    for field, label, n in FIELDS:
        v = _clean(r[field])
        if v and v.lower() not in ("other", "not applicable"):
            lines.append(f"{label}: {_cut(v, n)}")
    return "\n".join(lines)[:1500]


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "train.parquet")
    seen: set[str] = set()
    pools = {True: [], False: []}
    for r in df.iter_rows(named=True):
        post = _posting(r)
        body = _clean(r["description"])
        key = " ".join((_clean(r["title"]) + " " + body).lower().split())
        if len(body) < 50 or key in seen or post in seen:
            continue
        seen.update((key, post))
        pools[r["fraudulent"] == 1].append((r["job_id"], post))
    n_fraud = min(len(pools[True]), TARGET // 2)
    picked = [(True, x) for x in hash_order(pools[True], lambda x: x[0], "jobs.fraud")[:n_fraud]]
    picked += [(False, x) for x in hash_order(pools[False], lambda x: x[0], "jobs.real")[: TARGET - n_fraud]]
    picked.sort(key=lambda x: x[1][0])
    for fraud, (job_id, post) in picked:
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"job_posting": post},
            shape="detect",
            node_hint="machine.trust_safety.spam_phishing",
            template_id="fake_job_posts.fraudulent",
            source_item_id=f"job:{job_id}",
            license=LICENSE,
            truth=fraud,
            meta={"label_raw": int(fraud), **({"flags": ["sensitive"]} if SENSITIVE.search(post) else {})},
        )
