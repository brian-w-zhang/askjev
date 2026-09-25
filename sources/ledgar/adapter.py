"""LEDGAR (LexGLUE): contract provisions from SEC filings, each labelled with its section heading type.

Template "ledgar.provision_type": Choice "What type of provision is `clause`?" over 34 curated provision
types. The 100 LEDGAR labels contain near-synonyms (Indemnifications/Indemnity, Waivers/No Waivers,
four jurisdiction labels...) and catch-alls (General, Terms, Miscellaneous), so synonyms are merged into
one key and catch-all or heavily overlapping labels (Binding Effects vs Successors vs Assignments,
Payments vs Fees, Representations vs Warranties...) are left out entirely: only provisions whose label
maps to a kept key are sampled, so the truth is always one of the options and no `other` is needed.
Rows: test + validation splits, 40-1,500 chars (no truncation), case-insensitive dedup, balanced
round-robin across keys in salted hash order.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "ledgar"
BASE = "https://huggingface.co/api/datasets/coastalcph/lex_glue/parquet/ledgar/{split}/0.parquet"
SPLITS = ("test", "validation")
TARGET = env_int("TARGET_LEDGAR", 2500)
SALT = "ledgar.v1"
TEXT = "What type of provision is `clause`?"
LICENSE = "CC-BY-4.0"

# LEDGAR ClassLabel names, in label-index order (datasets-server /info for coastalcph/lex_glue ledgar).
LABELS = [
    "Adjustments", "Agreements", "Amendments", "Anti-Corruption Laws", "Applicable Laws", "Approvals",
    "Arbitration", "Assignments", "Assigns", "Authority", "Authorizations", "Base Salary", "Benefits",
    "Binding Effects", "Books", "Brokers", "Capitalization", "Change In Control", "Closings",
    "Compliance With Laws", "Confidentiality", "Consent To Jurisdiction", "Consents", "Construction",
    "Cooperation", "Costs", "Counterparts", "Death", "Defined Terms", "Definitions", "Disability",
    "Disclosures", "Duties", "Effective Dates", "Effectiveness", "Employment", "Enforceability",
    "Enforcements", "Entire Agreements", "Erisa", "Existence", "Expenses", "Fees", "Financial Statements",
    "Forfeitures", "Further Assurances", "General", "Governing Laws", "Headings", "Indemnifications",
    "Indemnity", "Insurances", "Integration", "Intellectual Property", "Interests", "Interpretations",
    "Jurisdictions", "Liens", "Litigations", "Miscellaneous", "Modifications", "No Conflicts", "No Defaults",
    "No Waivers", "Non-Disparagement", "Notices", "Organizations", "Participations", "Payments", "Positions",
    "Powers", "Publicity", "Qualifications", "Records", "Releases", "Remedies", "Representations", "Sales",
    "Sanctions", "Severability", "Solvency", "Specific Performance", "Submission To Jurisdiction",
    "Subsidiaries", "Successors", "Survival", "Tax Withholdings", "Taxes", "Terminations", "Terms", "Titles",
    "Transactions With Affiliates", "Use Of Proceeds", "Vacations", "Venues", "Vesting", "Waiver Of Jury Trials",
    "Waivers", "Warranties", "Withholdings",
]
assert len(LABELS) == 100

# key (Jev sees it) -> (description, LEDGAR labels merged into it)
KEYS: dict[str, tuple[str, tuple[str, ...]]] = {
    "governing_law": ("Which jurisdiction's law governs the agreement", ("Governing Laws",)),
    "counterparts": ("The agreement may be signed in separate counterparts or electronically", ("Counterparts",)),
    "notices": ("How and where formal notices must be delivered", ("Notices",)),
    "entire_agreement": ("The agreement is the parties' whole deal and supersedes prior ones",
                         ("Entire Agreements", "Integration")),
    "severability": ("An invalid provision does not void the rest of the agreement", ("Severability",)),
    "survival": ("Which obligations continue after the agreement ends", ("Survival",)),
    "amendments": ("How the agreement may be amended or modified", ("Amendments", "Modifications")),
    "assignment": ("Whether and how a party may assign its rights or obligations", ("Assignments",)),
    "taxes": ("Who bears or pays taxes", ("Taxes",)),
    "tax_withholding": ("Amounts may be withheld for taxes from payments",
                        ("Withholdings", "Tax Withholdings")),
    "compliance_with_laws": ("A party complies with applicable laws and regulations", ("Compliance With Laws",)),
    "expenses": ("Who pays costs and expenses", ("Expenses", "Costs")),
    "headings": ("Section headings are for convenience and do not affect meaning", ("Headings",)),
    "insurance": ("Insurance a party must carry or maintain", ("Insurances",)),
    "waivers": ("How rights may be waived, and that failing to enforce is not a waiver", ("Waivers", "No Waivers")),
    "confidentiality": ("Keeping information confidential", ("Confidentiality",)),
    "termination": ("How and when the agreement or employment can be terminated", ("Terminations",)),
    "further_assurances": ("Parties will sign further documents and take further actions as needed",
                           ("Further Assurances",)),
    "litigation": ("Statements about pending or threatened lawsuits and proceedings", ("Litigations",)),
    "indemnification": ("One party covers another's losses or claims", ("Indemnifications", "Indemnity")),
    "jury_trial_waiver": ("The parties waive the right to a jury trial", ("Waiver Of Jury Trials",)),
    "jurisdiction_and_venue": ("Which courts or venue hear disputes",
                               ("Consent To Jurisdiction", "Submission To Jurisdiction", "Jurisdictions", "Venues")),
    "arbitration": ("Disputes go to arbitration", ("Arbitration",)),
    "use_of_proceeds": ("How loan or offering proceeds may be used", ("Use Of Proceeds",)),
    "remedies": ("Remedies available on breach, and whether they are cumulative", ("Remedies",)),
    "base_salary": ("An employee's base salary", ("Base Salary",)),
    "no_conflicts": ("The agreement does not conflict with other agreements, charters or laws", ("No Conflicts",)),
    "definitions": ("Defines terms used in the agreement", ("Definitions", "Defined Terms")),
    "financial_statements": ("Delivery or accuracy of financial statements", ("Financial Statements",)),
    "vesting": ("When equity awards or benefits vest", ("Vesting",)),
    "releases": ("A party releases claims against another", ("Releases",)),
    "intellectual_property": ("Ownership or licensing of intellectual property", ("Intellectual Property",)),
    "brokers": ("No broker or finder is owed a fee, or who pays one", ("Brokers",)),
    "solvency": ("A party is solvent", ("Solvency",)),
    "non_disparagement": ("A party will not disparage the other", ("Non-Disparagement",)),
}
LABEL_TO_KEY = {lab: k for k, (_, labs) in KEYS.items() for lab in labs}
OPTIONS = {k: desc for k, (desc, _) in KEYS.items()}


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    by_key: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet")
        for i, (text, label) in enumerate(df.select("text", "label").iter_rows()):
            lab = LABELS[label]
            key = LABEL_TO_KEY.get(lab)
            if key is None:
                continue
            clean = re.sub(r"\s+", " ", text).strip()
            norm = clean.lower()
            if not (40 <= len(clean) <= 1500) or norm in seen:
                continue
            seen.add(norm)
            by_key[key].append((f"{split}:{i}", clean, lab))
    assert set(by_key) == set(KEYS), set(KEYS) - set(by_key)

    pools = {k: hash_order(v, lambda x: x[0], f"{SALT}|{k}") for k, v in by_key.items()}
    picked: list[tuple[str, str, str, str]] = []
    depth = 0
    while len(picked) < TARGET:
        progressed = False
        for k in KEYS:
            if len(picked) >= TARGET:
                break
            if depth < len(pools[k]):
                sid, clause, lab = pools[k][depth]
                picked.append((k, sid, clause, lab))
                progressed = True
        depth += 1
        if not progressed:
            break

    for key, sid, clause, lab in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"clause": clause},
            shape="classify",
            node_hint="machine.legal.clause_detection",
            template_id="ledgar.provision_type",
            source_item_id=sid,
            license=LICENSE,
            truth=key,
            meta={"label_raw": lab},
        )
