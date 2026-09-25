"""Amazon Shopping Queries Dataset (ESCI, Reddy et al. 2022): the product catalog side. Each US product has
a title, bullet points and seller-entered attribute fields, including color.

Template "esci.color": Choice "What color is the product in `listing`?" over 16 base colors (plus other).
Truth = the listing's own color field, mapped to a base color. The listing shown is title, brand and
bullet points (the color field itself is withheld). To keep the label answerable and unambiguous, a
product is used only when its color word appears in the shown text and the title names no other base
color. Unique US products from the test shard that esci_rerank already uses; equal quotas per color
(small colors take what they have, the rest spread over the others), salted hash order.
"""

from __future__ import annotations

import html
import os
import re
import shutil
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "esci_attributes"
URL = "https://huggingface.co/api/datasets/tasksource/esci/parquet/default/test/0.parquet"
TARGET = env_int("TARGET_ESCI_ATTRIBUTES", 2500)
LICENSE = "Apache-2.0"
TEXT = "What color is the product in `listing`?"
OPTIONS = {
    "black": None, "white": None, "gray": "Gray, grey or charcoal", "silver": None, "gold": None,
    "brown": None, "beige": None, "red": None, "pink": None, "orange": None, "yellow": None,
    "green": None, "blue": "Any blue, including navy", "purple": "Purple or violet",
    "clear": "Clear or transparent", "multicolor": "Several colors or multicolored",
    "other": "Another color, or the listing does not say",
}
# listing color field (lowercased) -> base color
FIELD = {
    "black": "black", "white": "white", "grey": "gray", "gray": "gray", "dark grey": "gray", "dark gray": "gray",
    "light grey": "gray", "light gray": "gray", "charcoal": "gray", "silver": "silver", "gold": "gold",
    "brown": "brown", "beige": "beige", "red": "red", "pink": "pink", "orange": "orange", "yellow": "yellow",
    "green": "green", "blue": "blue", "navy": "blue", "navy blue": "blue", "dark blue": "blue",
    "light blue": "blue", "royal blue": "blue", "sky blue": "blue", "purple": "purple", "violet": "purple",
    "clear": "clear", "transparent": "clear", "multicolor": "multicolor", "multicolored": "multicolor",
    "multi-color": "multicolor", "multi-colored": "multicolor", "multicolour": "multicolor", "multi": "multicolor",
}
# words that show the base color in the listing text
WORDS = {
    "black": r"black", "white": r"white", "gray": r"gr[ae]y|charcoal", "silver": r"silver", "gold": r"gold",
    "brown": r"brown", "beige": r"beige", "red": r"red", "pink": r"pink", "orange": r"orange",
    "yellow": r"yellow", "green": r"green", "blue": r"blue|navy", "purple": r"purple|violet",
    "clear": r"clear|transparent", "multicolor": r"multi-?colou?r(ed)?|multi-colored|assorted colou?rs|rainbow",
}
WORD_RE = {k: re.compile(rf"\b({v})\b", re.I) for k, v in WORDS.items()}
SENSITIVE = re.compile(
    r"\b(sex|sexy|porn\w*|nude\w*|naked|erotic\w*|dildo\w*|vibrator\w*|lingerie|condom\w*|lube|bdsm|"
    r"fetish\w*|thong\w*|masturbat\w*|suicid\w*)\b",
    re.I,
)
TAG = re.compile(r"<[^>]+>")


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "test_0.parquet"
    if out.exists():
        return
    sib = raw_dir.parent / "esci_rerank" / "test_0.parquet"
    if sib.exists():
        try:
            os.link(sib, out)
        except OSError:
            shutil.copy(sib, out)
        return
    r = httpx.get(URL, follow_redirects=True, timeout=600)
    r.raise_for_status()
    out.write_bytes(r.content)


def _clean(s: str | None) -> str:
    return " ".join(html.unescape(TAG.sub(" ", s)).split()) if s else ""


def _listing(title: str, brand: str, bullets: list[str], desc: str, limit: int = 900) -> str:
    parts = [title]
    if brand:
        parts.append(f"Brand: {brand}")
    if bullets:
        parts.append("Features: " + " | ".join(bullets))
    elif desc:
        parts.append("Description: " + desc)
    text = "\n".join(parts)
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return text


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = (
        pl.read_parquet(raw_dir / "test_0.parquet")
        .filter(pl.col("product_locale") == "us")
        .unique("product_id", keep="first", maintain_order=True)
        .drop_nulls(["product_color", "product_title"])
    )
    pools: dict[str, list[tuple[str, str]]] = {k: [] for k in WORDS}
    seen: set[str] = set()
    for pid, title, brand, bullet, desc, color in df.select(
        "product_id", "product_title", "product_brand", "product_bullet_point", "product_description", "product_color"
    ).iter_rows():
        base = FIELD.get(color.strip().lower())
        if not base:
            continue
        title = _clean(title)
        bullets = [_clean(b) for b in (bullet or "").split("\n") if _clean(b)]
        listing = _listing(title, _clean(brand), bullets, _clean(desc))
        if not WORD_RE[base].search(listing) or title.lower() in seen:
            continue
        if any(WORD_RE[o].search(title) for o in WORDS if o != base):
            continue
        seen.add(title.lower())
        pools[base].append((pid, listing))

    # Equal quotas; colors short of their quota give the remainder to the others.
    order = {k: hash_order(v, lambda x: x[0], f"esci.color.{k}") for k, v in pools.items()}
    quota: dict[str, int] = {k: 0 for k in pools}
    left = TARGET
    open_ = [k for k in pools if pools[k]]
    while left > 0 and open_:
        share = max(1, left // len(open_))
        for k in list(open_):
            take = min(share, len(order[k]) - quota[k], left)
            quota[k] += take
            left -= take
            if quota[k] >= len(order[k]):
                open_.remove(k)
            if left <= 0:
                break
    picked = sorted((pid, k, listing) for k in pools for pid, listing in order[k][: quota[k]])

    for pid, base, listing in picked:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"listing": listing},
            shape="extract",
            node_hint="machine.commerce.attribute_extraction",
            template_id="esci.color",
            source_item_id=f"us:{pid}",
            license=LICENSE,
            truth=base,
            meta={"color_field_base": base, **({"flags": ["sensitive"]} if SENSITIVE.search(listing) else {})},
        )
