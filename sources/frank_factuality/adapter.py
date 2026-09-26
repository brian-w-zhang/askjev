"""FRANK (Pagnoni, Balachandran & Tsvetkov, NAACL 2021): 2,246 machine-written summaries of CNN/DailyMail
and XSum news articles from nine summarization systems, each summary sentence annotated by three crowd
annotators with a typology of factual errors (majority vote per sentence).

Template "frank.faithful" (Noul, verify): is every statement in the summary supported by the article?
Truth = FRANK's Factuality == 1.0 (no summary sentence has an error), false otherwise. Only articles of at
most 3,000 characters (so the whole article is shown, never truncated). All faithful summaries plus 1.5x as
many unfaithful ones, seeded. XSum article text in the release lacks spaces after sentence full stops (restored) and
starts with BBC share-widget text (removed); escaped apostrophes in summaries are unescaped.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "frank_factuality"
BASE = "https://raw.githubusercontent.com/artidoro/frank/main/data/{file}"
FILES = ("benchmark_data.json", "human_annotations.json")
LICENSE = "MIT"
MAX_ARTICLE = 3000
RATIO = 1.5
TARGET = env_int("TARGET_FRANK_FACTUALITY", 3000)
TEXT = "Is every statement in `summary`, a machine-written summary of `article`, supported by the article?"
OPTIONS = {
    "true": "Everything the summary says is stated in or follows from the article.",
    "false": "The summary gets something wrong or adds something the article does not say: a wrong entity, "
    "number, relation, time or place, or an unsupported detail.",
}


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if not out.exists():
            r = httpx.get(BASE.format(file=f), follow_redirects=True, timeout=300)
            r.raise_for_status()
            out.write_bytes(r.content)


SHARE = re.compile(r"^Share this with.*?Copy this link", re.S)


def _clean(article: str) -> str:
    article = SHARE.sub("", article.strip())
    return re.sub(r"((?:[a-z0-9\)\"'])|(?:[A-Z]{2}))\.(?=[A-Z\"'])", r"\1. ", article).strip()


def normalize(raw_dir: Path) -> Iterator[Question]:
    bench = json.loads((raw_dir / "benchmark_data.json").read_text())
    human = {(h["hash"], h["model_name"]): h for h in json.loads((raw_dir / "human_annotations.json").read_text())}
    rows = {True: [], False: []}
    seen: dict[tuple[str, str], bool] = {}
    for b in bench:
        h = human.get((b["hash"], b["model_name"]))
        article = _clean(b["article"])
        if h is None or len(article) > MAX_ARTICLE or not b["summary"].strip():
            continue
        label = h["Factuality"] == 1.0
        key = (article, b["summary"].strip().replace("\\'", "'"))
        if key in seen:  # two systems produced the same summary: keep the first (drop if labels disagree)
            continue
        seen[key] = label
        rows[label].append({"id": f"{b['hash']}:{b['model_name']}", "article": article, "summary": b["summary"].strip().replace("\\'", "'"),
                            "label": label, "dataset": h["dataset"], "model": b["model_name"],
                            "factuality": h["Factuality"], "split": b["split"]})
    n_true = min(len(rows[True]), int(TARGET / (1 + RATIO)))
    pick = hash_order(rows[True], lambda r: r["id"], NAME)[:n_true] + \
        hash_order(rows[False], lambda r: r["id"], NAME)[: int(n_true * RATIO)]
    for r in hash_order(pick, lambda r: r["id"], NAME + ".order"):
        yield Question(
            text=TEXT, primitive="noul", hemisphere="machine", origin="dataset", source=NAME, options=OPTIONS,
            state={"article": r["article"], "summary": r["summary"]}, shape="verify",
            node_hint="machine.ai_systems.hallucination_citation", template_id="frank.faithful",
            source_item_id=r["id"], license=LICENSE, truth=r["label"],
            meta={"dataset": r["dataset"], "system": r["model"], "sentence_factuality": r["factuality"],
                  "split": r["split"]},
        )
