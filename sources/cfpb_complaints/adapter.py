"""CFPB Consumer Complaint Database: complaints US consumers filed with the Consumer Financial Protection
Bureau about financial products, with the consumer-written narrative (published with consent, scrubbed of
personal data) and the product and issue the consumer selected when filing.

Templates:
- "cfpb_complaints.product": Choice "Which financial product is `complaint` about?" over the 11 products of
  the current CFPB taxonomy, truth = the product on the complaint. Balanced across products.
- "cfpb_complaints.issue": Choice "Which issue does `complaint` raise about `product`?"; options = the
  issues the CFPB form offers for that product (those with >= 2% of its complaints), truth = the issue chosen.

Source: the CFPB bulk CSV no longer carries narratives (checked 2026-09: the column is gone from both the
CSV and the search API), so this uses BEE-spoke-data's CC0 HF mirror of the database taken while narratives
were published ("has-text" config, first shard: 563k complaints, 2015-2024). Product names changed over the
years; older names are mapped onto the current 11 products (sub-product decides the split ones).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "cfpb_complaints"
URL = "https://huggingface.co/datasets/BEE-spoke-data/consumer-finance-complaints/resolve/main/has-text/train-00000-of-00003.parquet"
TARGET_PRODUCT = env_int("TARGET_CFPB_PRODUCT", 2500)
TARGET_ISSUE = env_int("TARGET_CFPB_ISSUE", 2000)
MIN_ISSUE_SHARE = 0.02
MAX_CHARS = 1500
LICENSE = "Public domain (US Government work, CFPB Consumer Complaint Database); mirror BEE-spoke-data CC0-1.0"

PRODUCTS = {
    "credit_reporting": "Credit reports, credit scores or other consumer reports",
    "debt_collection": "A debt collector or the collection of a debt",
    "credit_card": "A credit card or store card account",
    "bank_account": "A checking or savings account",
    "money_transfer": "Money transfers, payment apps, virtual currency or money orders",
    "mortgage": "A mortgage",
    "vehicle_loan": "A car or other vehicle loan or lease",
    "student_loan": "A federal or private student loan",
    "personal_loan": "A payday loan, title loan, installment or personal loan, or cash advance",
    "prepaid_card": "A prepaid card, gift card, payroll card or government benefit card",
    "debt_management": "Debt settlement, credit repair or credit counseling services",
}
LEGACY = {
    "Debt collection": "debt_collection",
    "Credit card": "credit_card",
    "Checking or savings account": "bank_account",
    "Bank account or service": "bank_account",
    "Money transfer, virtual currency, or money service": "money_transfer",
    "Money transfers": "money_transfer",
    "Virtual currency": "money_transfer",
    "Mortgage": "mortgage",
    "Vehicle loan or lease": "vehicle_loan",
    "Student loan": "student_loan",
    "Payday loan, title loan, personal loan, or advance loan": "personal_loan",
    "Payday loan, title loan, or personal loan": "personal_loan",
    "Payday loan": "personal_loan",
    "Prepaid card": "prepaid_card",
    "Debt or credit management": "debt_management",
}
TAXONOMY_DATE = "2017-04-24"  # CFPB's product/issue taxonomy changed; the issue template uses only later complaints
ISSUE_MIN_PRODUCT_ROWS = 5000  # the issue template only uses raw product names with this many complaints
PRODUCT_TEXT = "Which financial product is `complaint` about?"
ISSUE_TEXT = "Which issue does `complaint` raise about `product`?"


def _slug(s: str) -> str:
    s = s.lower().replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "has_text_0.parquet"
    if out.exists():
        return
    with httpx.stream("GET", URL, follow_redirects=True, timeout=1200) as r, open(out.with_suffix(".tmp"), "wb") as fh:
        r.raise_for_status()
        for chunk in r.iter_bytes(1 << 20):
            fh.write(chunk)
    out.with_suffix(".tmp").rename(out)


def _product(prod: str, sub: str | None) -> str | None:
    """Map a (possibly legacy) CFPB product + sub-product onto one of the current 11 product keys."""
    sub = sub or ""
    if prod.startswith("Credit reporting"):
        if sub == "Credit repair services":
            return "debt_management"
        return "credit_reporting" if sub in ("", "Credit reporting", "Other personal consumer report") else None
    if prod == "Credit card or prepaid card":
        return "credit_card" if "credit card" in sub.lower() else "prepaid_card"
    if prod == "Consumer Loan":
        return "vehicle_loan" if sub.startswith("Vehicle") else "personal_loan"
    return LEGACY.get(prod)


def _clean(narr: str) -> str:
    t = " ".join(narr.split())
    t = re.sub(r"(X{2,}[/ ]?)+", "XXXX ", t).strip()  # CFPB redaction marks
    return t


def normalize(raw_dir: Path) -> Iterator[Question]:
    cols = ["Complaint ID", "Date received", "Product", "Sub-product", "Issue", "Consumer complaint narrative"]
    df = pl.read_parquet(raw_dir / "has_text_0.parquet", columns=cols)
    raw_counts = Counter(df["Product"].to_list())
    items = []  # (cid, date, raw_product, product_key, issue, text)
    seen: set[str] = set()
    for cid, date, prod, sub, issue, narr in df.rows():
        key = _product(prod, sub)
        if key is None or not narr:
            continue
        t = _clean(narr)
        if len(t) < 150 or len(t.split()) < 30 or t.lower()[:300] in seen:
            continue
        seen.add(t.lower()[:300])
        if len(t) > MAX_CHARS:
            t = t[:MAX_CHARS].rsplit(" ", 1)[0] + " ..."
        items.append((str(cid), date, prod, key, issue, t))
    items = hash_order(items, lambda x: x[0], "cfpb.v1")

    # Product template: round-robin across the 11 products.
    by_key: dict[str, list] = defaultdict(list)
    for it in items:
        by_key[it[3]].append(it)
    used: set[str] = set()
    prod_items = []
    cursor = {p: 0 for p in PRODUCTS}
    while len(prod_items) < TARGET_PRODUCT:
        progressed = False
        for p in PRODUCTS:
            if len(prod_items) >= TARGET_PRODUCT:
                break
            if cursor[p] < len(by_key[p]):
                it = by_key[p][cursor[p]]
                cursor[p] += 1
                prod_items.append(it)
                used.add(it[0])
                progressed = True
        if not progressed:
            break
    for cid, date, prod, key, issue, t in sorted(prod_items, key=lambda x: int(x[0])):
        yield Question(
            text=PRODUCT_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=PRODUCTS,
            state={"complaint": t},
            shape="classify",
            node_hint="machine.finance",
            template_id="cfpb_complaints.product",
            source_item_id=cid,
            license=LICENSE,
            truth=key,
            meta={"product_raw": prod, "issue": issue, "date_received": date},
        )

    # Issue template (complaints on/after TAXONOMY_DATE only, so old and new issue names never mix): options = the issues filed under the same raw product name (>= MIN_ISSUE_SHARE of it),
    # complaints disjoint from the product template, round-robin over raw products, at most 40% of a
    # product's picks from one issue.
    by_raw: dict[str, list] = defaultdict(list)
    for it in items:
        if it[0] not in used and it[1] >= TAXONOMY_DATE and raw_counts[it[2]] >= ISSUE_MIN_PRODUCT_ROWS:
            by_raw[it[2]].append(it)
    issue_opts: dict[str, dict[str, str]] = {}
    for p, its in by_raw.items():
        c = Counter(it[4] for it in its)
        tot = sum(c.values())
        issue_opts[p] = {_slug(i): i for i in sorted(i for i, n in c.items() if n / tot >= MIN_ISSUE_SHARE)}
    raws = sorted(p for p in by_raw if len(issue_opts[p]) >= 2)
    quota_each = -(-TARGET_ISSUE // len(raws))
    issue_items = []
    for p in raws:
        cap = max(1, int(quota_each * 0.4))
        cnt: Counter = Counter()
        take = []
        for it in by_raw[p]:
            if len(take) >= quota_each:
                break
            if _slug(it[4]) in issue_opts[p] and cnt[it[4]] < cap:
                cnt[it[4]] += 1
                take.append(it)
        issue_items += take
    issue_items = hash_order(issue_items, lambda x: x[0], "cfpb.issue")[:TARGET_ISSUE]
    for cid, date, prod, key, issue, t in sorted(issue_items, key=lambda x: int(x[0])):
        yield Question(
            text=ISSUE_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=issue_opts[prod],
            state={"product": PRODUCTS[key], "complaint": t},
            shape="classify",
            node_hint="machine.finance",
            template_id="cfpb_complaints.issue",
            source_item_id=cid,
            license=LICENSE,
            truth=_slug(issue),
            meta={"product_raw": prod, "issue": issue, "date_received": date},
        )
