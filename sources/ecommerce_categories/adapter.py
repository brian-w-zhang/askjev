"""E-commerce text dataset (Gautam 2019, Zenodo 10.5281/zenodo.3355823): ~50k real product listings (title +
description) scraped from Indian e-commerce sites, labelled Household / Books / Electronics / Clothing &
Accessories.

Template "ecommerce_categories.department": one Choice per listing over the 4 departments, truth = the label.
Case-insensitive exact dedup (the file has many repeated listings), listings under 40 chars dropped, long ones
cut at a word boundary near 800 chars (the title and first lines decide the department). Balanced 500 per
department in salted-hash order.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "ecommerce_categories"
URL = "https://zenodo.org/records/3355823/files/ecommerceDataset.csv"
LICENSE = "CC-BY-4.0"
NODE = "machine.commerce.listing_categorization"
TARGET = env_int("TARGET_ECOMMERCE_CATEGORIES", 2000)
MAX_CHARS = 800
TEXT = "Which store department does the product in `listing` belong in?"
LABELS = {
    "Household": ("household", "Home, kitchen, furniture, decor, cleaning, tools, and other everyday goods such as sports gear, "
                  "personal care and pet supplies"),
    "Books": ("books", "Printed books, textbooks and other reading material"),
    "Electronics": ("electronics", "Electronic devices, gadgets, computer and phone accessories"),
    "Clothing & Accessories": ("clothing_accessories", "Clothing, footwear, bags, jewellery and fashion accessories"),
}
OPTIONS = {k: d for k, d in LABELS.values()}
SEXUAL = re.compile(r"\b(sex|sexual\w*|porn\w*|nude\w*|erotic\w*|vibrator\w*|dildo\w*|condoms?|lingerie)\b", re.I)


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "ecommerceDataset.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _cut(t: str) -> str:
    if len(t) <= MAX_CHARS:
        return t
    return t[:MAX_CHARS].rsplit(" ", 1)[0] + " …"


def normalize(raw_dir: Path) -> Iterator[Question]:
    seen: set[str] = set()
    pools: dict[str, list] = {k: [] for k, _ in LABELS.values()}
    with open(raw_dir / "ecommerceDataset.csv", newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.reader(fh)):
            if len(row) < 2 or row[0] not in LABELS:
                continue
            t = " ".join(",".join(row[1:]).split()).strip(" ,")
            key = t.lower()
            if len(t) < 40 or key in seen:
                continue
            seen.add(key)
            pools[LABELS[row[0]][0]].append((i, _cut(t), row[0]))
    n = len(pools)
    picked = []
    for j, (k, pool) in enumerate(pools.items()):
        picked += [(k, x) for x in hash_order(pool, lambda x: x[0], f"ecom.{k}")[: TARGET // n + (j < TARGET % n)]]
    for k, (i, t, raw) in sorted(picked, key=lambda z: z[1][0]):
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"listing": t},
            shape="classify",
            node_hint=NODE,
            template_id="ecommerce_categories.department",
            source_item_id=f"row:{i}",
            license=LICENSE,
            truth=k,
            meta={"label_raw": raw, **({"flags": ["sensitive"]} if SEXUAL.search(t) else {})},
        )
