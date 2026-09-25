"""SciCite (Cohan et al. 2019, AllenAI): citation sentences from scientific papers (medicine and computer
science, Semantic Scholar) labelled with the citation's intent: background, method, or result comparison.

Template "scicite.intent": Choice "Why does `sentence` cite the work at `citation`?" over the 3 intents,
truth = the dataset label. `citation` is the citation marker text (citeStart:citeEnd). Rows whose
crowd label_confidence is below 0.75 are skipped (rows without a confidence are kept). Balanced across
the three intents (results is the smallest class), salted hash order, all splits pooled.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "scicite"
URL = "https://s3-us-west-2.amazonaws.com/ai2-s2-research/scicite/scicite.tar.gz"
TARGET = env_int("TARGET_SCICITE", 2500)
LICENSE = "Apache-2.0"
SPLITS = ("train", "dev", "test")
TEXT = "Why does `sentence` from a scientific paper cite the work at `citation`?"
OPTIONS = {
    "background": "To give background: prior work, context, or information about a problem, concept or field",
    "method": "Because the paper uses the cited work's method, procedure, tool or dataset",
    "result_comparison": "To compare the paper's results or findings with the cited work's",
}
LABELS = {"background": "background", "method": "method", "result": "result_comparison"}


def fetch(raw_dir: Path) -> None:
    if (raw_dir / "scicite" / "test.jsonl").exists():
        return
    tar = raw_dir / "scicite.tar.gz"
    if not tar.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        tar.write_bytes(r.content)
    with tarfile.open(tar) as t:
        t.extractall(raw_dir, filter="data")


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[str, list[tuple]] = {k: [] for k in OPTIONS}
    seen: set[str] = set()
    for split in SPLITS:
        for line in open(raw_dir / "scicite" / f"{split}.jsonl", encoding="utf-8"):
            r = json.loads(line)
            conf = r.get("label_confidence")
            if conf is not None and conf == conf and conf < 0.75:
                continue
            raw = r["string"]
            try:
                s, e = int(r["citeStart"]), int(r["citeEnd"])
            except (TypeError, ValueError):
                continue
            cite = " ".join(raw[s:e].split())
            sent = " ".join(raw.split())
            if not cite or len(cite) < 2 or not (40 <= len(sent) <= 1500) or sent.lower() in seen:
                continue
            seen.add(sent.lower())
            pools[LABELS[r["label"]]].append((split, r["unique_id"], sent, cite, r.get("sectionName")))

    picked: list[tuple] = []
    small = sorted(pools, key=lambda k: len(pools[k]))
    for i, lab in enumerate(small):
        want = min(len(pools[lab]), (TARGET - len(picked)) // (len(small) - i))
        picked += [(lab, *x) for x in hash_order(pools[lab], lambda x: x[1], f"scicite|{lab}")[:want]]
    picked.sort(key=lambda x: (x[1], x[2]))

    for lab, split, uid, sent, cite, section in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"sentence": sent, "citation": cite},
            shape="classify",
            node_hint="machine.research.claim_support",
            template_id="scicite.intent",
            source_item_id=f"{split}:{uid}",
            license=LICENSE,
            truth=lab,
            meta={"split": split, "section": section},
        )
