"""PubMed 20k RCT (Dernoncourt & Lee 2017): sentences from ~20,000 randomized-controlled-trial abstracts on
PubMed, each labelled with the heading its authors put it under in the structured abstract
(BACKGROUND, OBJECTIVE, METHODS, RESULTS, CONCLUSIONS).

Template "pubmed_rct.section": Choice "Which section of a structured research abstract does `sentence`
belong to?" Truth = the author's heading. Uses the dev and test files of the numbers-kept version
(PubMed_20k_RCT, not the @-masked one). The released text is tokenized ("( ADHF ) ."), so spacing around
punctuation is restored. Sentences of 6-80 words; at most one sentence per abstract; one fifth per section.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pubmed_rct_sections"
BASE = "https://raw.githubusercontent.com/Franck-Dernoncourt/pubmed-rct/master/PubMed_20k_RCT/"
FILES = ("dev.txt", "test.txt")
TARGET = env_int("TARGET_PUBMED_RCT_SECTIONS", 2500)
LICENSE = "No license file; public research dataset (Franck-Dernoncourt/pubmed-rct), abstracts from PubMed/MEDLINE"
TEXT = "Which section of a structured research abstract does `sentence` belong to?"
OPTIONS = {
    "background": "Why the study was done: what is known and what gap or problem motivates it",
    "objective": "What the study set out to do: its aim, question or hypothesis",
    "methods": "How the study was done: design, participants, interventions, measurements and analysis",
    "results": "What the study found: the outcomes, numbers and comparisons observed",
    "conclusions": "What the authors take from the findings: interpretation, implications and recommendations",
}


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def detok(s: str) -> str:
    s = " ".join(s.split())
    s = re.sub(r"\s+([.,;:!?%)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    s = re.sub(r"\s+(n't|'s)\b", r"\1", s)
    return s


def normalize(raw_dir: Path) -> Iterator[Question]:
    # (sid, abstract_id, section, sentence)
    pools: dict[str, list[tuple[str, str, str]]] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for f in FILES:
        split = f.removesuffix(".txt")
        abstract, idx = None, 0
        for line in open(raw_dir / f, encoding="utf-8"):
            line = line.rstrip("\n")
            if line.startswith("###"):
                abstract, idx = line[3:].strip(), 0
                continue
            if not line.strip() or "\t" not in line:
                continue
            label, sent = line.split("\t", 1)
            idx += 1
            key = label.strip().lower()
            text = detok(sent)
            if key not in pools or not 6 <= len(text.split()) <= 80 or text.lower() in seen:
                continue
            seen.add(text.lower())
            pools[key].append((f"{split}:{abstract}:{idx}", abstract, text))

    per = TARGET // len(OPTIONS)
    used_abstracts: set[str] = set()
    picked = []
    for i, lab in enumerate(OPTIONS):
        k = per + (1 if i < TARGET - per * len(OPTIONS) else 0)
        n = 0
        for sid, abstract, text in hash_order(pools[lab], lambda x: x[0], f"pubmed_rct.{lab}"):
            if n >= k:
                break
            if abstract in used_abstracts:
                continue
            used_abstracts.add(abstract)
            picked.append((lab, sid, text))
            n += 1
    picked.sort(key=lambda x: x[1])

    for lab, sid, text in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"sentence": text[:1500]},
            shape="classify",
            node_hint="machine.documents.structure_recovery",
            template_id="pubmed_rct.section",
            source_item_id=sid,
            license=LICENSE,
            truth=lab,
            meta={"label_raw": lab.upper(), "pmid": sid.split(":")[1]},
        )
