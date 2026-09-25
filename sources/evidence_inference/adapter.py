"""Evidence Inference (Lehman et al. 2019; DeYoung et al. 2020): prompts over randomized controlled trial
reports in PubMed Central (intervention, comparator, outcome), each answered by medical-expert annotators
with the reported effect and the supporting evidence span from the article.

Template "evidence_inference.effect": Choice "According to `evidence`, how did `intervention` affect
`outcome` compared with `comparator`?" over significantly increased / significantly decreased / no
significant difference. Only prompts answered by >= 2 annotators whose labels all agree (valid label and
reasoning) are used; the evidence is the first such annotator's span (30-1,000 chars, no table rows).
Balanced over the 3 labels in salted hash order.
"""

from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "evidence_inference"
BASE = "https://raw.githubusercontent.com/jayded/evidence-inference/master/annotations/"
FILES = ("annotations_merged.csv", "prompts_merged.csv")
TARGET = env_int("TARGET_EVIDENCE_INFERENCE", 2500)
LICENSE = "MIT"
TEXT = "According to `evidence` from a clinical trial report, how did `intervention` affect `outcome` compared with `comparator`?"
OPTIONS = {
    "significantly_increased": "The outcome was significantly higher with the intervention than with the comparator",
    "significantly_decreased": "The outcome was significantly lower with the intervention than with the comparator",
    "no_significant_difference": "There was no significant difference between the intervention and the comparator",
}
LABELS = {
    "significantly increased": "significantly_increased",
    "significantly decreased": "significantly_decreased",
    "no significant difference": "no_significant_difference",
}


def fetch(raw_dir: Path) -> None:
    for f in FILES:
        out = raw_dir / f
        if out.exists():
            continue
        r = httpx.get(BASE + f, follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _clean(s: str | None) -> str:
    return " ".join(html.unescape(html.unescape(s or "")).split())


def normalize(raw_dir: Path) -> Iterator[Question]:
    ann = pl.read_csv(raw_dir / FILES[0], infer_schema_length=0)
    prompts = {r["PromptID"]: r for r in pl.read_csv(raw_dir / FILES[1], infer_schema_length=0).to_dicts()}
    by_prompt: dict[str, list[dict]] = defaultdict(list)
    for r in ann.to_dicts():
        if r["Valid Label"] == "True" and r["Valid Reasoning"] == "True" and r["Label"] in LABELS:
            by_prompt[r["PromptID"]].append(r)

    pools: dict[str, list[tuple]] = {k: [] for k in OPTIONS}
    seen: set[tuple] = set()
    for pid, rows in by_prompt.items():
        labs = {r["Label"] for r in rows}
        if len(rows) < 2 or len(labs) != 1 or pid not in prompts:
            continue
        p = prompts[pid]
        iv, cp, oc = _clean(p["Intervention"]), _clean(p["Comparator"]), _clean(p["Outcome"])
        if not (iv and cp and oc) or max(len(iv), len(cp), len(oc)) > 300:
            continue
        ev = None
        for r in sorted(rows, key=lambda r: int(r["UserID"])):
            raw = r["Annotations"] or ""
            if "\t" in raw:
                continue
            t = _clean(raw)
            if 30 <= len(t) <= 1000:
                ev = t
                break
        if ev is None or (ev.lower(), iv.lower(), oc.lower()) in seen:
            continue
        seen.add((ev.lower(), iv.lower(), oc.lower()))
        pools[LABELS[labs.pop()]].append((pid, p["PMCID"], ev, iv, cp, oc, len(rows)))

    picked: list[tuple] = []
    order = sorted(pools, key=lambda k: len(pools[k]))
    for n, lab in enumerate(order):
        want = min(len(pools[lab]), (TARGET - len(picked)) // (len(order) - n))
        picked += [(lab, *x) for x in hash_order(pools[lab], lambda x: x[0], f"evidence_inference|{lab}")[:want]]
    picked.sort(key=lambda x: int(x[1]))

    for lab, pid, pmcid, ev, iv, cp, oc, n in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"intervention": iv, "comparator": cp, "outcome": oc, "evidence": ev},
            shape="classify",
            node_hint="machine.research.claim_support",
            template_id="evidence_inference.effect",
            source_item_id=f"prompt:{pid}",
            license=LICENSE,
            truth=lab,
            meta={"pmcid": pmcid, "n_annotators": n},
        )
