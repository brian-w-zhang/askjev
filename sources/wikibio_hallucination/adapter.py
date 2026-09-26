"""WikiBio GPT-3 hallucination set (Manakul, Liusie & Gales, EMNLP 2023, "SelfCheckGPT"): GPT-3
(text-davinci-003) wrote Wikipedia-style passages about 238 people from the WikiBio test set; every sentence
was hand-annotated as accurate, minor_inaccurate (related but with some non-factual detail) or
major_inaccurate (made up or about the wrong person).

Template "wikibio.sentence_accuracy" (Score, verify): how wrong is one generated sentence, given the
person's real Wikipedia introduction? Levels low -> high error; truth = annotation index. Only people whose
Wikipedia text is at most 2,500 characters (shown whole). All annotated sentences are kept (their mix is
27% accurate / 33% minor / 40% major).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question

NAME = "wikibio_hallucination"
URL = "https://huggingface.co/api/datasets/potsawee/wiki_bio_gpt3_hallucination/parquet/default/evaluation/0.parquet"
LICENSE = "CC-BY-SA-3.0"
MAX_REF = 2500
TEXT = (
    "How wrong is `sentence`, taken from an AI-written biography of the person described in `wikipedia`, "
    "judged against what is true about that person?"
)
LEVELS = [
    "Everything the sentence says is correct for this person",
    "The sentence is about the right person and partly right, but includes a false detail such as a wrong "
    "date, place, title or event",
    "The sentence is made up or describes someone else: its main claims are false for this person",
]
INDEX = {"accurate": 0, "minor_inaccurate": 1, "major_inaccurate": 2}


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "evaluation.parquet"
    if not out.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "evaluation.parquet")
    seen = set()
    for r in df.iter_rows(named=True):
        ref = r["wiki_bio_text"].strip()
        if len(ref) > MAX_REF:
            continue
        for j, (sent, ann) in enumerate(zip(r["gpt3_sentences"], r["annotation"])):
            sent = sent.strip()
            if len(sent.split()) < 3 or (ref, sent) in seen:  # a passage can repeat a sentence
                continue
            seen.add((ref, sent))
            yield Question(
                text=TEXT, primitive="score", hemisphere="machine", origin="dataset", source=NAME, options=LEVELS,
                state={"wikipedia": ref, "sentence": sent}, shape="verify",
                node_hint="machine.ai_systems.hallucination_citation", template_id="wikibio.sentence_accuracy",
                source_item_id=f"{r['wiki_bio_test_idx']}:{j}", license=LICENSE, truth=INDEX[ann],
                meta={"annotation": ann, "sentence_index": j},
            )
