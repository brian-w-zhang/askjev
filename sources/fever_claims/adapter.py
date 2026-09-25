"""FEVER (Thorne et al. 2018) claim verification, via copenlu/fever_gold_evidence: claims written from
Wikipedia, each with evidence sentences and a SUPPORTS / REFUTES / NOT ENOUGH INFO label. For the verifiable
claims the evidence is the annotators' gold sentences; for NOT ENOUGH INFO claims copenlu attached retrieved
Wikipedia sentences (which, per the label, do not settle the claim).

Template "fever_claims.verdict": Choice over supports / refutes / not_enough_info, truth = the label.
The question text differs from SciFact's (whose options differ) so the two stay separate templates.
One row per claim (the first evidence set in salted-hash order); evidence is detokenized (-LRB- -> "(", " ,"
-> ",") and prefixed with the Wikipedia page title. Balanced across the three labels, validation split.
Flags: political by keyword (parties, elections, named politicians, hot-button issues).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "fever_claims"
URL = "https://huggingface.co/api/datasets/copenlu/fever_gold_evidence/parquet/default/validation/0.parquet"
LICENSE = "CC-BY-SA-3.0"
NODE = "machine.research.claim_support"
TARGET = env_int("TARGET_FEVER_CLAIMS", 2500)
MAX_CHARS = 1500
TEXT = "What do the Wikipedia sentences in `evidence` say about `claim`?"
OPTIONS = {
    "supports": "The evidence shows the claim is true",
    "refutes": "The evidence shows the claim is false",
    "not_enough_info": "The evidence neither confirms nor contradicts the claim",
}
LABELS = {"SUPPORTS": "supports", "REFUTES": "refutes", "NOT ENOUGH INFO": "not_enough_info"}
POLITICAL = re.compile(
    r"\b(trump\w*|clinton\w*|hillary|obama\w*|biden|sanders|pelosi|putin|mcconnell|romney|pence|"
    r"republican\w*|democrat(s|ic)?\b|gop|election\w*|abortion\w*|pro-life|pro-choice|gun control|"
    r"second amendment|immigra\w*|brexit|conservative party|labour party|tea party|alt-right|"
    r"white nationalis\w*|israel\w*|palestin\w*|erdo\w*|netanyahu|modi|bolsonaro|maduro|kim jong)\b",
    re.I,
)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "validation.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


_TOK = [("-LRB-", "("), ("-RRB-", ")"), ("-LSB-", "["), ("-RSB-", "]"), ("-LCB-", "{"), ("-RCB-", "}"),
        ("-COLON-", ":"), ("``", '"'), ("''", '"')]


def _detok(s: str) -> str:
    for a, b in _TOK:
        s = s.replace(a, b)
    s = s.replace("_", " ").replace(" -- ", "–")
    s = re.sub(r"\s+([,.;:!?%)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    s = re.sub(r"\s+('s|'re|'ve|'d|'ll|n't|')\b", r"\1", s)
    s = re.sub(r'"\s+(.*?)\s+"', r'"\1"', s)
    return " ".join(s.split())


def _evidence(ev: list[list[str]]) -> str:
    parts = []
    for page, _line, sent in ev:
        t = f"{_detok(page)}: {_detok(sent)}"
        if t not in parts:
            parts.append(t)
    return "\n".join(parts)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "validation.parquet")
    by_claim: dict[str, list] = {}
    for claim, label, ev, rid, oid in df.select("claim", "label", "evidence", "id", "original_id").iter_rows():
        c = " ".join((claim or "").split())
        if not c or not ev or label not in LABELS:
            continue
        e = _evidence(ev)
        if len(c) + len(e) > MAX_CHARS or len(e) < 20:
            continue
        by_claim.setdefault(c.lower(), []).append((rid, oid, c, LABELS[label], e))
    pools: dict[str, list] = {k: [] for k in OPTIONS}
    for rows in by_claim.values():
        if len({r[3] for r in rows}) > 1:  # contradictory labels for one claim text
            continue
        pick = hash_order(rows, lambda r: r[0], "fever.evset")[0]
        pools[pick[3]].append(pick)
    picked = []
    for i, k in enumerate(OPTIONS):
        n = TARGET // 3 + (1 if i < TARGET % 3 else 0)
        picked += hash_order(pools[k], lambda r: r[0], f"fever.{k}")[:n]
    for rid, oid, c, lab, e in sorted(picked, key=lambda r: r[0]):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"claim": c, "evidence": e},
            shape="verify",
            node_hint=NODE,
            template_id="fever_claims.verdict",
            source_item_id=f"validation:{rid}",
            license=LICENSE,
            truth=lab,
            meta={"fever_id": oid, **({"flags": ["political"]} if POLITICAL.search(f"{c} {e}") else {})},
        )
