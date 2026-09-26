"""DDI Extraction 2013 corpus (Herrero-Zazo et al. 2013, HF `bigbio/ddi_corpus`, source config): DrugBank
texts and MEDLINE abstracts with expert-annotated drug mentions and, for every pair of drugs in a sentence,
the drug-drug interaction type (mechanism, effect, advise, int) or none.

Template "ddi.interaction_type": one Choice per drug pair within one sentence: what does the sentence say
about how the two drugs interact? Truth = the annotated type; pairs in a sentence with no annotated
relation are "none" (the corpus annotates every in-sentence pair). The bigbio source config is
document-level, so sentences are recovered with a conservative splitter that never cuts inside a drug
mention. Stratified: up to 560 per type (all 285 "int" pairs are fewer), the rest none.
"""

from __future__ import annotations

import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "ddi_interactions"
URL = "https://huggingface.co/api/datasets/bigbio/ddi_corpus/parquet/ddi_corpus_source/{split}/0.parquet"
SPLITS = ("train", "test")
TARGET = env_int("TARGET_DDI_INTERACTIONS", 2500)
PER_TYPE = 560
LICENSE = "CC-BY-NC-4.0"
TEXT = "What does `sentence` say about how `drug_1` and `drug_2` interact when used together?"
OPTIONS = {
    "mechanism": "A pharmacokinetic interaction: one drug changes the other's absorption, metabolism, "
    "levels or excretion",
    "effect": "An effect or clinical outcome of taking them together (a stronger or weaker effect, a side "
    "effect, a toxicity)",
    "advise": "A recommendation or warning about using them together (avoid, adjust the dose, monitor)",
    "interaction": "Only that the two drugs interact, with no further detail",
    "none": "The sentence does not describe an interaction between these two drugs",
}
TYPE_KEY = {"MECHANISM": "mechanism", "EFFECT": "effect", "ADVISE": "advise", "INT": "interaction"}
SPLIT_RE = re.compile(r"(?<=[.;?!])\s+(?=[A-Z(\[])")


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(URL.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _sentences(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    cuts = [0]
    for m in SPLIT_RE.finditer(text):
        p = m.start()
        if any(a <= p < b for a, b in spans):
            continue
        cuts.append(m.end())
    cuts.append(len(text))
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for split in SPLITS:
        for doc in pl.read_parquet(raw_dir / f"{split}.parquet").iter_rows(named=True):
            text = doc["text"]
            ents = {}
            for e in doc["entities"]:
                off = e["offsets"]
                if len(off) != 2:  # discontinuous mentions: skip
                    continue
                a, b = off
                if text[a:b] != e["text"]:
                    continue
                ents[e["id"]] = (a, b, e["text"])
            rel = {}
            for r in doc["relations"]:
                h, t = r["head"]["ref_id"], r["tail"]["ref_id"]
                rel[frozenset((h, t))] = TYPE_KEY[r["type"]]
            spans = [(a, b) for a, b, _ in ents.values()]
            for sa, sb in _sentences(text, spans):
                sent = text[sa:sb].strip()
                inside = sorted(
                    ((i, v) for i, v in ents.items() if sa <= v[0] and v[1] <= sb), key=lambda x: x[1][0]
                )
                if not (40 <= len(sent) <= 700) or len(inside) < 2:
                    continue
                for (i1, v1), (i2, v2) in combinations(inside, 2):
                    n1, n2 = v1[2].strip(), v2[2].strip()
                    if n1.lower() == n2.lower():
                        continue
                    lab = rel.get(frozenset((i1, i2)), "none")
                    k = (sent, n1.lower(), n2.lower())
                    if k in seen:  # same sentence + names twice (repeated mention): keep the first
                        continue
                    seen.add(k)
                    pools[lab].append((f"{doc['document_id']}:{i1}:{i2}", sent, n1, n2, lab, split))
    picked = []
    for lab in ("mechanism", "effect", "advise", "interaction"):
        picked += hash_order(pools[lab], lambda x: x[0], NAME)[:PER_TYPE]
    rest = TARGET - len(picked)
    # at most 2 "none" pairs per sentence so negatives are not dominated by long drug lists
    per_sent = defaultdict(int)
    for x in hash_order(pools["none"], lambda x: x[0], NAME):
        if rest <= 0:
            break
        if per_sent[x[1]] >= 2:
            continue
        per_sent[x[1]] += 1
        picked.append(x)
        rest -= 1
    for sid, sent, n1, n2, lab, split in sorted(picked, key=lambda x: x[0]):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"sentence": sent, "drug_1": n1, "drug_2": n2},
            shape="classify",
            node_hint="machine.research.entity_relation",
            template_id="ddi.interaction_type",
            source_item_id=f"{split}:{sid}",
            license=LICENSE,
            truth=lab,
            meta={"split": split},
        )
