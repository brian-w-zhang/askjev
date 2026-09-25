"""Google Natural Questions yes/no subset: real Google search queries whose annotated answer is YES or NO.

Source: google-research-datasets/natural_questions (CC BY-SA 3.0, ungated), the full train (287 files) and
validation (7 files) parquet. The Wikipedia documents are ~55 GB, so fetch() reads only the small columns over
HTTP range requests (question text, document title, the annotators' yes_no_answer and short-answer strings) and
stores them per file. Train has one annotation per query; validation has five (a majority of the five must say
the same YES/NO, and the split is kept in meta).

Queries are lowercase without a question mark; casing is restored from a corpus-wide map (multi-word names and
single words written capitalized in Wikipedia titles and short-answer strings across all ~315k NQ rows, never common
English words from Brysbaert et al.'s 40k lemmas, which Title Case work titles would otherwise capitalize) plus the
row's own title, with BoolQ's word lists. BoolQ's standalone filter drops queries that need unseen context (a
show's plot, "still", digits, fictional-universe titles). Deduped on normalized text, and against BoolQ. Noul
with truth, kind factual, no state, no node_hint (BoolQ's title rules misfire without the passage: "Utah Jazz" ->
music), so the beam walk places them.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator

import orjson
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "natural_questions_yn"
REPO = "https://huggingface.co/datasets/google-research-datasets/natural_questions/resolve/main/default"
FILES = [f"train-{i:05d}-of-00287" for i in range(287)] + [f"validation-{i:05d}-of-00007" for i in range(7)]
LICENSE = "CC BY-SA 3.0 (Google Natural Questions)"
TARGET = env_int("TARGET_NATURAL_QUESTIONS_YN", 100000)  # all that survive
SALT = "natural_questions_yn-20260925"
FUNNEL: Counter = Counter()

_spec = importlib.util.spec_from_file_location("nq_boolq", Path(__file__).parents[1] / "boolq" / "adapter.py")
B = importlib.util.module_from_spec(_spec)
sys.modules["nq_boolq"] = B
_spec.loader.exec_module(B)
_cspec = importlib.util.spec_from_file_location("nq_concreteness",
                                                Path(__file__).parents[1] / "concreteness" / "adapter.py")
C = importlib.util.module_from_spec(_cspec)
sys.modules["nq_concreteness"] = C
_cspec.loader.exec_module(C)
DICT: set[str] = set()  # Brysbaert et al. 2014 English lemmas: common words are never capitalized from the name tables

# Queries that are not a question at all ("salto ángel is the tallest waterfall"), or open with a non-closed word.
OPENER = re.compile(r"^(is|are|was|were|do|does|did|can|could|has|have|had|will|would|should|shall|may|might|must)\b",
                    re.I)
NOT_ASCII = re.compile(r"[^\x20-\x7e]")
REPEAT = re.compile(r"\b(\w+) \1\b", re.I)
# Visa-requirement queries (~15% of the pool) are dated facts that change with policy: capped.
VISA = re.compile(r"\bvisas?\b", re.I)
VISA_CAP = env_int("NATURAL_QUESTIONS_YN_VISA_CAP", 40)


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    C.fetch_brysbaert(raw_dir)
    for f in FILES:
        out = raw_dir / f"{f}.parquet"
        if out.exists():
            continue
        ann = pl.col("annotations").struct
        df = pl.scan_parquet(f"{REPO}/{f}.parquet").select(
            pl.col("id"),
            pl.col("question").struct.field("text").alias("q"),
            pl.col("document").struct.field("title").alias("title"),
            ann.field("yes_no_answer").alias("yn"),
            ann.field("short_answers").list.eval(pl.element().struct.field("text")).list.eval(
                pl.element().list.join(" | ")).alias("sa"),
        ).collect()
        tmp = out.with_suffix(".tmp")
        df.write_parquet(tmp)
        tmp.rename(out)


# --- casing ----------------------------------------------------------------------------------------------------
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9'.&-]*[A-Za-z0-9]|[A-Za-z0-9]")


def _common(w: str) -> bool:
    w = w.lower().strip("'.")
    if w in DICT:
        return True
    for suf in ("s", "es", "ed", "d", "ing", "er", "est", "ly", "'s"):
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            b = w[: -len(suf)]
            if b in DICT or b + "e" in DICT or (len(b) >= 3 and b[-1] == b[-2] and b[:-1] in DICT):
                return True
    return any(w.endswith(suf) and w[: -len(suf)] + "y" in DICT for suf in ("ies", "ied"))


def _case_tables(df: pl.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    """Multi-word names (lowercase -> cased) and single words written capitalized mid-text at least twice as often as
    lowercase (and at least 3 times), from every NQ Wikipedia title (first word skipped) and short-answer string."""
    names: Counter = Counter()
    upper: Counter = Counter()
    lower: Counter = Counter()
    forms: dict[str, Counter] = {}
    titles = [re.sub(r"\s*\([^)]*\)$", "", t or "") for t in df["title"].to_list()]
    answers = [a for sa in df["sa"].to_list() for a in (sa or []) if a for a in a.split(" | ")]
    for text, skip_first in [(t, True) for t in titles] + [(a, False) for a in answers if len(a) <= 80]:
        for m in B.RUN.finditer(text):
            words = m.group(0).split()
            while words and words[0].lower() in B.LEAD:
                words = words[1:]
            if len(words) >= 2:
                names[" ".join(words)] += 1
        for i, m in enumerate(TOKEN.finditer(text)):
            w, lw = m.group(0), m.group(0).lower()
            if i == 0 and skip_first:
                continue
            if w == lw:
                lower[lw] += 1
            elif w[0].isupper():
                upper[lw] += 1
                forms.setdefault(lw, Counter())[w] += 1
    by_low: dict[str, Counter] = {}
    for n, c in names.items():
        by_low.setdefault(n.lower(), Counter())[n] += c
    # A corpus name is applied only if one of its words is not a common English word ("Utah Jazz", "Hot Topic" is
    # skipped): Title Case work titles would otherwise capitalize "Need a Visa" or "There Is".
    name_map = {low: c.most_common(1)[0][0] for low, c in by_low.items()
                if not all(_common(w) for w in low.split())}
    name_map.update({n.lower(): n for n in B.NAMES})
    single = {lw: forms[lw].most_common(1)[0][0] for lw in upper
              if lw not in B.STAY and not _common(lw) and upper[lw] >= 3 and upper[lw] >= 2 * lower[lw]}
    return name_map, single


def restore_case(q: str, title: str, name_map: dict[str, str], single: dict[str, str]) -> str:
    own = {}
    for m in B.RUN.finditer(re.sub(r"\s*\([^)]*\)$", "", title or "")):
        words = m.group(0).split()
        while words and words[0].lower() in B.LEAD:
            words = words[1:]
        if len(words) >= 2:
            own[" ".join(words).lower()] = " ".join(words)
    words = " ".join(q.split()).rstrip(" ?").split(" ")
    out, i = [], 0
    while i < len(words):
        for n in range(min(6, len(words) - i), 1, -1):  # longest multi-word name first
            low = " ".join(words[i:i + n]).lower()
            cased = own.get(low) or name_map.get(low)
            if cased:
                out.append(cased)
                i += n
                break
        else:
            w = words[i]
            lw = w.lower()
            out.append(B.ALWAYS.get(lw) or single.get(lw) or w)
            i += 1
    t = " ".join(out)
    t = re.sub(r"\bthe us\b", "the US", t)
    return t[0].upper() + t[1:] + "?"


# --- normalize -------------------------------------------------------------------------------------------------
def _answer(yn: list[int], split: str) -> bool | None:
    """1 = YES, 0 = NO, -1 = none. Train: the one annotation; validation: a majority (>= 3 of 5) for YES or NO."""
    votes = [v for v in (yn or []) if v in (0, 1)]
    if split == "train":
        return bool(votes[0]) if len(yn or []) == 1 and votes else None
    for v in (0, 1):
        if votes.count(v) >= 3:
            return bool(v)
    return None


def _norm_key(q: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", q.lower()).strip()


def _pool(raw_dir: Path) -> tuple[list[dict], pl.DataFrame]:
    df = pl.concat([pl.read_parquet(raw_dir / f"{f}.parquet").with_columns(pl.lit(f.split("-")[0]).alias("split"))
                    for f in FILES])
    FUNNEL["0_rows"] = df.height
    boolq = set()
    bq_dir = raw_dir.parent / "boolq"
    for f in ("train.parquet", "validation.parquet"):
        if (bq_dir / f).exists():
            boolq |= {_norm_key(q) for q in pl.read_parquet(bq_dir / f, columns=["question"])["question"].to_list()}
    FUNNEL["boolq_questions_loaded"] = len(boolq)
    kept: dict[str, dict] = {}
    for rid, q, title, yn, split in df.filter(pl.col("yn").list.eval(pl.element() >= 0).list.any()).select(
            "id", "q", "title", "yn", "split").iter_rows():
        FUNNEL["1_yes_no_annotated"] += 1
        ans = _answer(yn, split)
        if ans is None:
            FUNNEL["2_no_majority"] += 1
            continue
        q = " ".join((q or "").split())
        if not OPENER.match(q) or NOT_ASCII.search(q) or REPEAT.search(q) or not B.keep(q, title or ""):
            FUNNEL["3_not_standalone_closed_question"] += 1
            continue
        if B.SLUR.search(q):
            FUNNEL["4_slur"] += 1
            continue
        k = _norm_key(q)
        if k in boolq:
            FUNNEL["5_in_boolq"] += 1
            continue
        if k in kept:
            FUNNEL["6_duplicate"] += 1
            continue
        kept[k] = {"id": f"{split}:{rid}", "q": q, "title": title or "", "answer": ans, "split": split,
                   "yn": [int(v) for v in yn]}
    FUNNEL["7_pool"] = len(kept)
    return list(kept.values()), df


def normalize(raw_dir: Path) -> Iterator[Question]:
    DICT.update(w for w in C.read_brysbaert(raw_dir / C.FILE) if " " not in w)
    pool, df = _pool(raw_dir)
    name_map, single = _case_tables(df)
    picked, visa = [], 0
    for it in hash_order(pool, lambda x: x["id"], SALT):
        if len(picked) >= TARGET:
            break
        if VISA.search(it["q"]):
            if visa >= VISA_CAP:
                FUNNEL["7_visa_capped"] += 1
                continue
            visa += 1
        picked.append(it)
    FUNNEL["8_picked"] = len(picked)
    FUNNEL["8_picked_true"] = sum(x["answer"] for x in picked)
    for it in sorted(picked, key=lambda x: x["id"]):
        text = restore_case(it["q"], it["title"], name_map, single)
        flags = [f for f, rx in (("political", B.POLITICAL), ("sensitive", B.SENSITIVE)) if rx.search(it["q"])]
        meta = {"wikipedia_title": it["title"], "query": it["q"], "split": it["split"]}
        if it["split"] != "train":
            meta["annotator_yes_no"] = it["yn"]
        if flags:
            meta["flags"] = flags
        yield Question(
            text=text,
            primitive="noul",
            hemisphere="world",
            kind="factual",
            origin="dataset",
            source=NAME,
            source_item_id=it["id"],
            license=LICENSE,
            truth=it["answer"],
            meta=meta,
        )
    print("natural_questions_yn funnel:", dict(sorted(FUNNEL.items())))
