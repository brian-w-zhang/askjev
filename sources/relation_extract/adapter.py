"""ChemProt (BioCreative VI, Krallinger et al. 2017): PubMed abstracts with chemical and gene/protein mentions
and expert-annotated chemical-protein relations (CPR groups), via bigbio/chemprot (chemprot_full_source).

Template "relation_extract.chem_protein": one Choice per (sentence, chemical, gene/protein) triple: what relation
does the sentence state between them? Options = the five evaluated CPR groups (activates, inhibits, agonist_of,
antagonist_of, substrate_or_product_of), `other_relation` (the non-evaluated groups CPR:1/2/7/8: part-of,
direction-less regulation, modulation, cofactor) and `none` (CPR:10 "not", and co-mentioned pairs with no
annotation, the standard ChemProt negative convention). Truth = the annotated group.
Abstracts are split into sentences on sentence-final punctuation; only relations whose two mentions sit in one
sentence are used. Triples are grouped by (sentence, chemical text, gene text); a triple whose mention pairs
carry different groups is dropped. Sentences over 600 chars are skipped. Water-filled across the five groups,
none ~20%, other_relation ~8%, all three splits.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "relation_extract"
BASE = "https://huggingface.co/api/datasets/bigbio/chemprot/parquet/chemprot_full_source"
SPLITS = ("train", "validation", "test")
LICENSE = "Public domain (bigbio: PUBLIC_DOMAIN_MARK_1p0)"
NODE = "machine.research.entity_relation"
TARGET = env_int("TARGET_RELATION_EXTRACT", 2000)
NONE_SHARE = 0.20
OTHER_SHARE = 0.08
MAX_SENT = 600
TEXT = "What relation does `sentence` state between the chemical `entity_a` and the gene or protein `entity_b`?"
OPTIONS = {
    "activates": "The chemical increases the activity or expression of the gene or protein (upregulator, activator)",
    "inhibits": "The chemical decreases the activity or expression of the gene or protein (downregulator, inhibitor, blocker)",
    "agonist_of": "The chemical is an agonist of the gene or protein (usually a receptor)",
    "antagonist_of": "The chemical is an antagonist of the gene or protein (usually a receptor)",
    "substrate_or_product_of": "The chemical is a substrate or a product of the gene or protein (usually an enzyme or transporter)",
    "other_relation": "Some other relation: the chemical is part of it, regulates it without a stated direction, "
    "modulates it, or is its cofactor",
    "none": "The sentence states no relation between the two",
}
CPR = {"CPR:3": "activates", "CPR:4": "inhibits", "CPR:5": "agonist_of", "CPR:6": "antagonist_of",
       "CPR:9": "substrate_or_product_of", "CPR:1": "other_relation", "CPR:2": "other_relation",
       "CPR:7": "other_relation", "CPR:8": "other_relation", "CPR:10": "none"}
MAIN = ["activates", "inhibits", "agonist_of", "antagonist_of", "substrate_or_product_of"]
SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])")


def fetch(raw_dir: Path) -> None:
    for s in SPLITS:
        out = raw_dir / f"{s}.parquet"
        if out.exists():
            continue
        r = httpx.get(f"{BASE}/{s}/0.parquet", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def _sentences(text: str) -> list[tuple[int, int]]:
    spans, start = [], 0
    for m in SENT_END.finditer(text):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    # the title is separated from the abstract by a newline
    out = []
    for a, b in spans:
        nl = text.find("\n", a, b)
        out += [(a, nl), (nl + 1, b)] if nl != -1 else [(a, b)]
    return out


def _triples(raw_dir: Path) -> dict[str, list]:
    pools: dict[str, list] = {k: [] for k in OPTIONS}
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for pmid, text, ents, rels in df.select("pmid", "text", "entities", "relations").iter_rows():
            sents = _sentences(text)
            ent = {}
            for eid, typ, etxt, off in zip(ents["id"], ents["type"], ents["text"], ents["offsets"]):
                s_idx = next((i for i, (a, b) in enumerate(sents) if a <= off[0] and off[1] <= b), None)
                if s_idx is not None:
                    ent[eid] = (typ, etxt, s_idx)
            rel = {}
            for typ, a1, a2 in zip(rels["type"], rels["arg1"], rels["arg2"]):
                if typ in CPR:
                    rel[(a1, a2)] = CPR[typ]
            groups: dict[tuple, set] = {}
            for c_id, (ct, ctext, cs) in ent.items():
                if ct != "CHEMICAL":
                    continue
                for g_id, (gt, gtext, gs) in ent.items():
                    if not gt.startswith("GENE") or gs != cs or ctext.lower() == gtext.lower():
                        continue
                    if ctext.lower() in gtext.lower() or gtext.lower() in ctext.lower():
                        continue  # nested mentions ("estradiol" in "estradiol receptor") make the pair ambiguous
                    key = (cs, ctext, gtext)
                    groups.setdefault(key, set()).add(rel.get((c_id, g_id), rel.get((g_id, c_id), "none")))
            for (cs, ctext, gtext), labs in groups.items():
                if len(labs) != 1:
                    continue
                a, b = sents[cs]
                sent = " ".join(text[a:b].split())
                if len(sent) > MAX_SENT or len(sent) < 30:
                    continue
                lab = next(iter(labs))
                pools[lab].append((f"{split}:{pmid}:{cs}:{ctext}|{gtext}", sent, ctext, gtext, lab))
    return pools


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools = _triples(raw_dir)
    ordered = {k: hash_order(v, lambda x: x[0], f"chemprot.{k}") for k, v in pools.items()}
    take = {k: 0 for k in OPTIONS}
    take["none"] = min(len(ordered["none"]), round(TARGET * NONE_SHARE))
    take["other_relation"] = min(len(ordered["other_relation"]), round(TARGET * OTHER_SHARE))
    quota = TARGET - take["none"] - take["other_relation"]
    while quota > 0:
        open_ = [k for k in MAIN if take[k] < len(ordered[k])]
        if not open_:
            break
        share = max(1, quota // len(open_))
        for k in open_:
            add = min(share, len(ordered[k]) - take[k], quota)
            take[k] += add
            quota -= add
            if quota == 0:
                break
    picked = [x for k in OPTIONS for x in ordered[k][: take[k]]]
    for item, sent, ca, gb, lab in sorted(picked):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"sentence": sent, "entity_a": ca, "entity_b": gb},
            shape="extract",
            node_hint=NODE,
            template_id="relation_extract.chem_protein",
            source_item_id=item,
            license=LICENSE,
            truth=lab,
            meta={"dataset": "ChemProt"},
        )
