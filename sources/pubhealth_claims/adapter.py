"""PUBHEALTH (Kotonya & Toni, EMNLP 2020): 11.8k public-health claims with fact-checker verdicts
(true / false / mixture / unproven) from Snopes, PolitiFact, FactCheck.org, Reuters, AP and Health News
Review. Source: the BigBIO parquet export (`pubhealth_source`, all splits).

Template "pubhealth_claims.verdict" (Noul): "Would a fact-checker rate `claim` as true?" on viral claims
checked by fact-checkers (Snopes staff writers, or subjects tagged as fact checks / junk news / fake news),
excluding claims whose subjects mention politics; truth = true / false verdict (mixture and unproven
dropped). News headlines from the AP / Reuters health feeds are excluded (they are labelled "true" only
because they are news, not checked claims). ~40% true.
Flags: political on politics words that survive the subject filter; sensitive on sexual words.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "pubhealth_claims"
BASE = "https://huggingface.co/api/datasets/bigbio/pubhealth/parquet/pubhealth_source/{split}/0.parquet"
SPLITS = ["train", "validation", "test"]
LICENSE = "MIT"
NODE = "machine.trust_safety"
TARGET = env_int("TARGET_PUBHEALTH_CLAIMS", 1000)
LABEL = {0: True, 1: False}  # 2 unproven, 3 mixture: dropped

TEXT = "Would a professional fact-checker rate `claim` as true?"
OPTIONS = {
    "true": "The claim is accurate as stated",
    "false": "The claim is false, fabricated or a hoax",
}
SNOPES = {
    "David Mikkelson", "Kim LaCapria", "Dan Evon", "Rich Buhler & Staff", "Dan MacGuill", "Alex Kasprak",
    "Bethania Palma", "Arturo Garcia", "Brooke Binkowski", "Jordan Liles", "Snopes Staff", "Barbara Mikkelson",
    "Bond Huberman", "Jessica Lee", "Madison Dapcevich", "Nur Ibrahim", "Liz Donaldson", "Emery Winter",
}
FACTCHECK_SUBJ = re.compile(r"(?i)\b(fact checks|junk news|fake news|fauxtography|viral content|facebook fact-checks)\b")
POLITICS_SUBJ = re.compile(r"(?i)politic|election|congress|legislat")
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|obamacare|biden|pelosi|sanders|gop|republican\w*|democrat\w*|"
    r"liberals?|conservatives?|election\w*|vot(e|es|ed|ers|ing)|congress\w*|senat\w*|governor|abortion\w*|"
    r"planned parenthood|immigra\w*|migrants?|refugees?|illegals?|border|islam\w*|muslims?|deport\w*|guns?|nra|president\w*)\b",
    re.I,
)
SEXUAL = re.compile(r"\b(sex|sexual\w*|porn\w*|nude\w*|naked|anal|rape\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for s in SPLITS:
        out = raw_dir / f"{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=s), follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(c: str) -> str:
    c = " ".join(c.replace('"""', '"').replace('""', '"').split()).strip()
    if len(c) > 1 and c.startswith('"') and c.endswith('"') and c.count('"') == 2:
        c = c[1:-1].strip()
    elif c.startswith('"') and c.count('"') % 2 == 1:
        c = c[1:].strip()
    elif c.endswith('"') and c.count('"') % 2 == 1:
        c = c[:-1].strip()
    return c


def normalize(raw_dir: Path) -> Iterator[Question]:
    d = pl.concat([pl.read_parquet(raw_dir / f"{s}.parquet").with_columns(pl.lit(s).alias("split")) for s in SPLITS])
    items = []
    seen: set[str] = set()
    for r in d.iter_rows(named=True):
        if r["label"] not in LABEL:
            continue
        checkers = {x.strip() for x in (r["fact_checkers"] or "").split(",") if x.strip()}
        subj = r["subjects"] or ""
        if not (checkers & SNOPES or FACTCHECK_SUBJ.search(subj)) or POLITICS_SUBJ.search(subj):
            continue
        c = _clean(r["claim"] or "")
        if len(c) < 20 or len(c) > 1000 or c.lower() in seen:
            continue
        seen.add(c.lower())
        items.append((r["claim_id"], c, LABEL[r["label"]], r))
    pos = [x for x in items if x[2]]
    neg = [x for x in items if not x[2]]
    n_pos = min(len(pos), round(TARGET * 0.4))
    picked = hash_order(pos, lambda x: x[0], "pubhealth.true")[:n_pos]
    picked += hash_order(neg, lambda x: x[0], "pubhealth.false")[: TARGET - n_pos]
    for cid, c, truth, r in sorted(picked, key=lambda x: x[0]):
        flags = []
        if SEXUAL.search(c):
            flags.append("sensitive")
        if POLITICAL.search(c):
            flags.append("political")
        yield Question(
            text=TEXT, primitive="noul", hemisphere="machine", origin="dataset", source=NAME,
            options=OPTIONS, state={"claim": c}, shape="verify", node_hint=NODE,
            template_id="pubhealth_claims.verdict", source_item_id=str(cid), license=LICENSE, truth=truth,
            meta={"split": r["split"], "fact_checkers": r["fact_checkers"], "subjects": r["subjects"],
                  "date_published": r["date_published"], **({"flags": flags} if flags else {})},
        )
