"""SciFact (Wadden et al. 2020): expert-written scientific claims paired with PubMed abstracts, each
pair labelled SUPPORT / CONTRADICT by annotators, with the cited abstracts of NOT-ENOUGH-INFO claims
serving as NOINFO pairs.

Template "scifact.claim_support": one Choice per (claim, abstract) pair: does the abstract support,
contradict, or say nothing about the claim? This is the citation-check pattern (does the cited source
back the sentence that cites it). Truth = the dataset label.

Source files: the HF repo is script-based (no parquet export from /parquet), so the files come from its
auto-converted `refs/convert/parquet` branch. Test claims have no labels; train + validation are used.
Only pairs whose claim + title + full abstract fit in ~1,500 chars are kept (the evidence is never
truncated, since truncation could drop the rationale sentences).
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "scifact"
BASE = "https://huggingface.co/datasets/allenai/scifact/resolve/refs%2Fconvert%2Fparquet"
FILES = {
    "claims_train.parquet": f"{BASE}/claims/train/0000.parquet",
    "claims_validation.parquet": f"{BASE}/claims/validation/0000.parquet",
    "corpus.parquet": f"{BASE}/corpus/train/0000.parquet",
}
TARGET_V1 = 200  # the original balanced seeded sample, kept as-is so its ids stay stable
TARGET = env_int("TARGET_SCIFACT", TARGET_V1)  # Phase 6: every pair that fits (set it high, e.g. 100000)
SEED = 2020
MAX_CHARS = 1500
LICENSE = "CC-BY-NC-2.0"
TEXT = "How does `evidence` relate to `claim`?"
OPTIONS = {
    "supports": "The evidence backs the claim",
    "contradicts": "The evidence goes against the claim",
    "says_nothing": "The evidence neither backs nor goes against the claim",
}
LABEL_KEY = {"SUPPORT": "supports", "CONTRADICT": "contradicts", "NOINFO": "says_nothing"}


def fetch(raw_dir: Path) -> None:
    for name, url in FILES.items():
        out = raw_dir / name
        if out.exists():
            continue
        r = httpx.get(url, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    corpus = {
        doc_id: (" ".join(title.split()), " ".join(" ".join(s.split()) for s in abstract))
        for doc_id, title, abstract in pl.read_parquet(raw_dir / "corpus.parquet")
        .select("doc_id", "title", "abstract")
        .iter_rows()
    }

    pools: dict[str, list[tuple[str, int, int, str, str]]] = {k: [] for k in LABEL_KEY}
    seen: set[tuple[int, int]] = set()
    for split in ("train", "validation"):
        df = pl.read_parquet(raw_dir / f"claims_{split}.parquet")
        for cid, claim, ev_doc, label, _sents, cited in df.iter_rows():
            claim = " ".join(claim.split())
            pairs = [(int(ev_doc), label)] if label else [(d, "NOINFO") for d in cited]
            for doc_id, lab in pairs:
                if (cid, doc_id) in seen or doc_id not in corpus:
                    continue
                seen.add((cid, doc_id))
                title, abstract = corpus[doc_id]
                evidence = f"{title}. {abstract}" if not title.endswith(".") else f"{title} {abstract}"
                if len(claim) + len(evidence) > MAX_CHARS:
                    continue
                pools[lab].append((split, cid, doc_id, claim, evidence))

    rng = random.Random(SEED)
    labels = sorted(pools)
    v1 = min(TARGET, TARGET_V1)
    per = {lab: v1 // len(labels) for lab in labels}
    for lab in labels[: v1 - sum(per.values())]:
        per[lab] += 1
    items = []
    for lab in labels:
        pool = sorted(pools[lab])
        items += [(lab, *x) for x in rng.sample(pool, min(per[lab], len(pool)))]
    # Phase 6 top-up across all labels (hash order, prefix-stable; unbalanced once a label runs out).
    everything = [(lab, *x) for lab in labels for x in sorted(pools[lab])]
    items += top_up(items, everything, TARGET - len(items), lambda x: (x[1], x[2], x[3]), "scifact")
    items.sort(key=lambda x: (x[1], x[2], x[3]))

    for lab, split, cid, doc_id, claim, evidence in items:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"claim": claim, "evidence": evidence},
            shape="verify",
            node_hint="machine.research.claim_support",
            template_id="scifact.claim_support",
            source_item_id=f"{split}:{cid}:{doc_id}",
            license=LICENSE,
            truth=LABEL_KEY[lab],
            meta={"split": split, "label_raw": lab, "claim_id": cid, "doc_id": doc_id},
        )
