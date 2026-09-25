"""PubMedQA (Jin et al. 2019, HF qiaojin/PubMedQA): research questions (from article titles) answered
yes / no / maybe from the PubMed abstract without its conclusion.

Template "pubmedqa.answer" (Choice, node research.claim_support): given the abstract (structured
sections minus the conclusion, which is what the label was derived from), what is the answer to the
question. Truth = final_decision.
- pqa_labeled: all 1,000 expert-annotated items (yes 552 / no 338 / maybe 110), meta.split = "labeled".
- pqa_artificial: a 1,500 sample (750 yes / 750 no; this set has no "maybe") whose labels were generated
  heuristically from the conclusion, meta.split = "artificial". Only abstracts <= 1,800 chars are used.
Labeled abstracts over 2,000 chars are cut at a sentence boundary (meta.truncated).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pubmedqa"
URLS = {
    "labeled.parquet": "https://huggingface.co/api/datasets/qiaojin/PubMedQA/parquet/pqa_labeled/train/0.parquet",
    "artificial.parquet": "https://huggingface.co/api/datasets/qiaojin/PubMedQA/parquet/pqa_artificial/train/0.parquet",
}
TARGET_ARTIFICIAL = env_int("TARGET_PUBMEDQA_ARTIFICIAL", 1500)
LICENSE = "MIT"
TEXT = "Based on `abstract`, what is the answer to `question`?"
OPTIONS = {
    "yes": "The results in the abstract support answering yes",
    "no": "The results in the abstract support answering no",
    "maybe": "The results are mixed, inconclusive, or only support a yes under some conditions",
}
LABELED_MAX = 2000
ARTIFICIAL_MAX = 1800
SENSITIVE = re.compile(r"\b(suicid\w*|self-harm|self-injur\w*|sexual abuse|rape)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for name, url in URLS.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)


def _abstract(ctx: dict) -> str:
    parts = []
    for label, text in zip(ctx["labels"], ctx["contexts"]):
        text = " ".join(text.split())
        parts.append(f"{label.strip().upper()}: {text}" if label else text)
    return "\n".join(parts)


def _cut(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    head = text[:limit]
    m = max(head.rfind(". "), head.rfind(".\n"))
    return (head[: m + 1] if m > limit // 2 else head.rsplit(" ", 1)[0]) + " […]"


def _q(pubid, question, abstract, label, split, truncated=False) -> Question:
    flags = {"flags": ["sensitive"]} if SENSITIVE.search(question + " " + abstract) else {}
    return Question(
        text=TEXT,
        primitive="choice",
        hemisphere="machine",
        origin="dataset",
        source=NAME,
        options=OPTIONS,
        state={"question": question, "abstract": abstract},
        shape="verify",
        node_hint="machine.research.claim_support",
        template_id="pubmedqa.answer",
        source_item_id=f"{split}:{pubid}",
        license=LICENSE,
        truth=label,
        meta={"split": split, "pubid": pubid, **({"truncated": True} if truncated else {}), **flags},
    )


def normalize(raw_dir: Path) -> Iterator[Question]:
    lab = pl.read_parquet(raw_dir / "labeled.parquet")
    labeled_ids = set()
    for pubid, question, ctx, decision in lab.select("pubid", "question", "context", "final_decision").iter_rows():
        labeled_ids.add(pubid)
        full = _abstract(ctx)
        abstract = _cut(full, LABELED_MAX)
        yield _q(pubid, " ".join(question.split()), abstract, decision, "labeled", abstract != full)

    art = pl.read_parquet(raw_dir / "artificial.parquet", columns=["pubid", "question", "context", "final_decision"])
    pools = {"yes": [], "no": []}
    for pubid, question, ctx, decision in art.iter_rows():
        if pubid in labeled_ids or decision not in pools:
            continue
        abstract = _abstract(ctx)
        if 300 <= len(abstract) <= ARTIFICIAL_MAX:
            pools[decision].append((pubid, " ".join(question.split()), abstract, decision))
    picked = []
    for d in ("yes", "no"):
        k = TARGET_ARTIFICIAL // 2 if d == "yes" else TARGET_ARTIFICIAL - TARGET_ARTIFICIAL // 2
        picked += hash_order(pools[d], lambda x: x[0], f"pubmedqa.art.{d}")[:k]
    for pubid, question, abstract, decision in sorted(picked):
        yield _q(pubid, question, abstract, decision, "artificial")
