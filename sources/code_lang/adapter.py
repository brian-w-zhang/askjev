"""Rosetta Code (via the christopher/rosetta-code HF dump): solutions to the same programming tasks in
hundreds of languages, each tagged with the language it is written in.

Template "code.language": one Choice per snippet: which language is it written in? Options are six
common languages plus `other`; truth = the Rosetta Code language heading (lowercased; languages outside
the six map to `other`). 25 per named language and the rest `other`, drawn round-robin from a fixed
list of mainstream languages (C, C++, C#, Kotlin, Ruby, PHP, Swift, Scala, ...), seeded.

Filters: 120-1,500 chars; one snippet per (task, language); snippets that name their own language
(e.g. "python" in a comment) are dropped so the name is not a giveaway. TypeScript snippets must use
TypeScript-only syntax (a type annotation, interface or type alias), since untyped TypeScript is
indistinguishable from JavaScript.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question

NAME = "code_lang"
URL = "https://huggingface.co/api/datasets/christopher/rosetta-code/parquet/default/train/0.parquet"
TARGET = 200
PER_NAMED = 25
SEED = 1337
LICENSE = "GFDL-1.2"
TEXT = "What programming language is `code` written in?"
OPTIONS = {
    "python": None,
    "javascript": None,
    "typescript": None,
    "go": None,
    "rust": None,
    "java": None,
    "other": "Any other programming language",
}
NAMED = [k for k in OPTIONS if k != "other"]
OTHER = ["c", "c++", "c#", "kotlin", "ruby", "php", "swift", "scala", "perl", "haskell", "lua", "julia", "dart", "r"]
# Words that give a snippet's language away if they appear in it.
LEAK = {
    "python": r"python",
    "javascript": r"javascript|\bnode(js)?\b",
    "typescript": r"typescript",
    "go": r"golang",
    "rust": r"\brust",
    "java": r"\bjava\b",
    "c": r"\bC\b",
    "c++": r"c\+\+",
    "c#": r"c#|csharp",
    "kotlin": r"kotlin",
    "ruby": r"\bruby\b",
    "php": r"\bphp\b(?!\s*$)",
    "swift": r"\bswift\b",
    "scala": r"\bscala\b",
    "perl": r"\bperl\b",
    "haskell": r"haskell",
    "lua": r"\blua\b",
    "julia": r"\bjulia\b",
    "dart": r"\bdart\b",
    "r": r"\bR language\b",
}
TS_SYNTAX = re.compile(r":\s*(number|string|boolean|void|any|unknown|never)\b|\binterface\s+\w+|\btype\s+\w+\s*=|<\w+>\(")


def _clean(code: str) -> str:
    code = code.replace("\xa0", " ").replace("\r\n", "\n")
    lines = [ln.rstrip() for ln in code.split("\n")]
    return "\n".join(lines).strip("\n")


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "rosetta.parquet"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    df = pl.read_parquet(raw_dir / "rosetta.parquet").with_row_index("row")
    wanted = set(NAMED) | set(OTHER)
    pools: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    seen_code: set[str] = set()
    for row, task, lang, code in df.select("row", "task_name", "language_name", "code").iter_rows():
        lang = lang.strip().lower()
        if lang not in wanted or (task, lang) in seen:
            continue
        code = _clean(code)
        if not (120 <= len(code) <= 1500) or code in seen_code:
            continue
        flags = 0 if lang in ("c", "r") else re.I
        if re.search(LEAK[lang], code, flags):
            continue
        if lang == "typescript" and not TS_SYNTAX.search(code):
            continue
        seen.add((task, lang))
        seen_code.add(code)
        pools[lang].append((row, task, code))

    rng = random.Random(SEED)
    items: list[tuple[str, str, int, str, str]] = []
    for lang in NAMED:
        pool = pools[lang]
        items += [(lang, lang, *x) for x in rng.sample(pool, min(PER_NAMED, len(pool)))]
    others = {lang: rng.sample(pools[lang], len(pools[lang])) for lang in OTHER}
    cursor = 0
    while len(items) < TARGET:
        lang = OTHER[cursor % len(OTHER)]
        k = cursor // len(OTHER)
        if k < len(others[lang]):
            items.append(("other", lang, *others[lang][k]))
        cursor += 1
    items.sort(key=lambda x: x[2])

    for key, lang, row, task, code in items:
        yield Question(
            text=TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=OPTIONS,
            state={"code": code},
            shape="classify",
            node_hint="machine.code.code_review",
            template_id="code.language",
            source_item_id=f"train:{row}",
            license=LICENSE,
            truth=key,
            meta={"language": lang, "task": task},
        )
