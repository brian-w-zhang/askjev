"""CORD v2 (Park et al. 2019, NAVER Clova): 1,000 Indonesian shop and restaurant receipts with OCR words,
their boxes, and a ground-truth parse (menu lines, subtotal, tax, service, total, cash, change).

The receipt text Jev sees is the labelled OCR words re-assembled in reading order (grouped by OCR row,
rows top to bottom, words left to right), at most 1,500 chars. Images are never downloaded: only the
`ground_truth` column is read from the parquet shards.

Templates:
- "receipts_extract.total" (Choice): "Which amount is the total in `receipt`?" Options = the total plus 2-3
  other amounts printed on the same receipt (numerically different), plus `none_of_these`. Truth = total.
- "receipts_extract.field_match" (Noul): "Does `extracted_value` match the `field` in `receipt`?" Up to three
  per receipt on different fields; one gets the true value and the other an amount from another field
  of the same receipt (numerically different), alternating so the set is 50/50.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import Question
from askjev.sampling import env_int

NAME = "receipts_extract"
BASE = "https://huggingface.co/api/datasets/naver-clova-ix/cord-v2/parquet/default"
SHARDS = {"train": 4, "validation": 1, "test": 1}
TARGET_TOTAL = env_int("TARGET_RECEIPTS_TOTAL", 1000)
TARGET_MATCH = env_int("TARGET_RECEIPTS_MATCH", 2000)
SEED = 1000
PER_RECEIPT = 3  # field_match questions per receipt
MAX_CHARS = 1500
LICENSE = "CC-BY-4.0"
TOTAL_TEXT = "Which amount is the total in `receipt`?"
MATCH_TEXT = "Does `extracted_value` match the `field` in `receipt`?"
MATCH = {
    "true": "The receipt shows exactly this value for that field",
    "false": "The receipt shows a different value for that field, or none",
}
NONE_KEY = "none_of_these"

# gt_parse path -> field description (what a extraction schema would call it)
FIELDS = {
    ("total", "total_price"): "total amount due",
    ("sub_total", "subtotal_price"): "subtotal before tax, service and discounts",
    ("sub_total", "tax_price"): "tax amount",
    ("sub_total", "service_price"): "service charge",
    ("sub_total", "discount_price"): "discount amount",
    ("total", "cashprice"): "cash handed over by the customer",
    ("total", "changeprice"): "change given back to the customer",
    ("total", "creditcardprice"): "amount paid by credit card",
    ("total", "emoneyprice"): "amount paid by e-money",
}
MENU_AMOUNTS = ("price", "unitprice", "discountprice")


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "ground_truth.parquet"
    if out.exists():
        return
    parts = []
    for split, n in SHARDS.items():
        for i in range(n):
            gt = pl.scan_parquet(f"{BASE}/{split}/{i}.parquet").select("ground_truth").collect()
            parts.append(gt.with_columns(pl.lit(split).alias("split"), pl.lit(i).alias("shard")))
    pl.concat(parts).write_parquet(out)


def _digits(v: str) -> str:
    return re.sub(r"\D", "", v).lstrip("0")


def _clean(v) -> str | None:
    if not isinstance(v, str):
        return None
    v = v.strip().rstrip(".,").strip()
    return v if _digits(v) else None


def _receipt_text(gt: dict) -> str:
    rows: dict[int, list[tuple[float, float, str]]] = {}
    for line in gt["valid_line"]:
        for w in line["words"]:
            q = w["quad"]
            rows.setdefault(w["row_id"], []).append(((q["y1"] + q["y3"]) / 2, q["x1"], w["text"]))
    ordered = sorted(rows.values(), key=lambda ws: sum(y for y, _, _ in ws) / len(ws))
    text = "\n".join(" ".join(t for _, _, t in sorted(ws, key=lambda w: w[1])) for ws in ordered)
    return text


def _menu(parse: dict) -> list[dict]:
    m = parse.get("menu")
    if isinstance(m, dict):
        return [m]
    return [x for x in m if isinstance(x, dict)] if isinstance(m, list) else []


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "ground_truth.parquet")
    receipts = []
    seen: set[str] = set()
    for gt_raw, split, shard in df.iter_rows():
        gt = json.loads(gt_raw)
        parse = gt["gt_parse"]
        rid = f"{split}:{gt['meta']['image_id']}"
        text = _receipt_text(gt)
        if len(text) > MAX_CHARS or text in seen:
            continue
        seen.add(text)
        fields: dict[str, str] = {}
        for (sec, key), desc in FIELDS.items():
            v = _clean((parse.get(sec) or {}).get(key)) if isinstance(parse.get(sec), dict) else None
            if v:
                fields[desc] = v
        menu = _menu(parse)
        names = [(it.get("nm") or "").strip() if isinstance(it.get("nm"), str) else "" for it in menu]
        amounts = list(fields.values())
        for it, nm in zip(menu, names):
            for k in MENU_AMOUNTS:
                v = _clean(it.get(k))
                if v:
                    amounts.append(v)
            p = _clean(it.get("price"))
            if nm and p and names.count(nm) == 1 and len(nm) >= 3:
                fields[f'price of the line "{nm}"'] = p
        # keep only amounts that are actually printed in the receipt text
        amounts = [a for a in dict.fromkeys(amounts) if a in text]
        fields = {f: v for f, v in fields.items() if v in text}
        receipts.append((rid, text, fields, amounts))

    rng = random.Random(SEED)
    rng.shuffle(receipts)

    # Template 1: which amount is the total (Choice).
    n_total = 0
    total_qs = []
    for rid, text, fields, amounts in receipts:
        if n_total >= TARGET_TOTAL:
            break
        total = fields.get("total amount due")
        if not total:
            continue
        others, used = [], {_digits(total)}
        for a in rng.sample(amounts, len(amounts)):
            if _digits(a) not in used:
                used.add(_digits(a))
                others.append(a)
        if len(others) < 2:
            continue
        opts = [total] + others[:3]
        rng.shuffle(opts)
        total_qs.append((rid, text, opts, total))
        n_total += 1

    # Template 2: extracted value matches field (Noul), two fields per receipt, alternating correct/wrong.
    match_qs = []
    flip = False
    for rid, text, fields, amounts in receipts:
        if len(match_qs) >= TARGET_MATCH:
            break
        names = sorted(fields)
        if len(names) < 2:
            continue
        for field in rng.sample(names, min(PER_RECEIPT, len(names))):
            truth_v = fields[field]
            wrong = [a for a in amounts if _digits(a) != _digits(truth_v)]
            correct = flip
            if not correct and not wrong:
                continue
            value = truth_v if correct else rng.choice(wrong)
            match_qs.append((rid, text, field, value, correct, truth_v))
            flip = not flip
            if len(match_qs) >= TARGET_MATCH:
                break

    for rid, text, opts, total in sorted(total_qs):
        yield Question(
            text=TOTAL_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options={**{o: None for o in opts}, NONE_KEY: "None of these amounts is the total"},
            state={"receipt": text},
            shape="extract",
            node_hint="machine.documents.structured_extraction",
            template_id="receipts_extract.total",
            source_item_id=rid,
            license=LICENSE,
            truth=total,
            meta={"language": "id", "currency": "IDR"},
        )
    for rid, text, field, value, correct, truth_v in sorted(match_qs, key=lambda x: (x[0], x[2])):
        yield Question(
            text=MATCH_TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=MATCH,
            state={"receipt": text, "field": field, "extracted_value": value},
            shape="verify",
            node_hint="machine.ai_systems.extraction_verification",
            template_id="receipts_extract.field_match",
            source_item_id=f"{rid}:{field}",
            license=LICENSE,
            truth=correct,
            meta={"true_value": truth_v, "language": "id", "currency": "IDR"},
        )
