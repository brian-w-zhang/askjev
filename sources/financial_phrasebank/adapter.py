"""Financial PhraseBank (Malo et al. 2014): sentences from English financial news about Finnish listed
companies, each labelled positive / neutral / negative for investors by 5-8 annotators with finance
background. The Sentences_AllAgree file keeps only sentences all annotators agreed on (2,264).

Template "fpb.investor_sentiment": one Choice per sentence, truth = the unanimous label.
Balanced across the 3 labels, seeded. Source file: the zip in the HF repo (script-based, no parquet).
"""

from __future__ import annotations

import random
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "financial_phrasebank"
URL = "https://huggingface.co/datasets/takala/financial_phrasebank/resolve/main/data/FinancialPhraseBank-v1.0.zip"
MEMBER = "FinancialPhraseBank-v1.0/Sentences_AllAgree.txt"
TARGET = 200
SEED = 2014
LICENSE = "CC-BY-NC-SA-3.0"
TEXT = "What is the sentiment of `sentence` for the company's investors?"
OPTIONS = {
    "positive": "Good news for the company's investors",
    "neutral": "Neither good nor bad news for the company's investors",
    "negative": "Bad news for the company's investors",
}


def _detok(s: str) -> str:
    s = " ".join(s.split())
    for a, b in ((" ,", ","), (" .", "."), (" ;", ";"), (" :", ":"), (" )", ")"), ("( ", "("), (" 's", "'s"), (" %", "%")):
        s = s.replace(a, b)
    return s


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "FinancialPhraseBank-v1.0.zip"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    with zipfile.ZipFile(raw_dir / "FinancialPhraseBank-v1.0.zip") as z:
        lines = z.read(MEMBER).decode("latin-1").splitlines()

    pools: dict[str, list[tuple[int, str]]] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for i, line in enumerate(lines):
        if "@" not in line:
            continue
        raw, label = line.rsplit("@", 1)
        sentence = _detok(raw)
        if not sentence or sentence.lower() in seen or len(sentence) > 1500:
            continue
        seen.add(sentence.lower())
        pools[label.strip()].append((i, sentence))

    rng = random.Random(SEED)
    labels = sorted(pools)
    per = {lab: TARGET // len(labels) for lab in labels}
    for lab in labels[: TARGET - sum(per.values())]:
        per[lab] += 1
    items = [(lab, *x) for lab in labels for x in rng.sample(pools[lab], per[lab])]
    items.sort(key=lambda x: x[1])

    for lab, i, sentence in items:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"sentence": sentence},
            shape="classify",
            node_hint="machine.finance.risk_scoring",
            template_id="fpb.investor_sentiment",
            source_item_id=f"allagree:{i}",
            license=LICENSE,
            truth=lab,
            meta={"agreement": "all", "label_raw": lab},
        )
