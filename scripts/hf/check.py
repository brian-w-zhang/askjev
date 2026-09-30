"""Check data/hf/askjev before it's uploaded. Exits non-zero on any failure; prints one line per check.

- only the expected files are there (Parquet under data/<config>/, README.md, restore_yahoo.py)
- no hidden question appears anywhere, and every answer/meta/placement/human row points at a shipped question
- Yahoo words are blank, restore_ref is set on those rows, and no copy survives in meta or the calls sample
- no MovieLens/Last.fm human rows
- none of this project's own credentials (gateway key, database password, HF token) in any string column
- the card has no unfilled placeholders

  uv run python scripts/hf/check.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from askjev.config import DATA  # noqa: E402
from askjev.db import connect  # noqa: E402

OUT = DATA / "hf" / "askjev"

def own_secrets() -> list[str]:
    """This project's real credentials (gateway key, database password, HF token), to search for verbatim. Patterns
    can't tell a leak from the public code in machine questions, which is full of example keys and URLs. Never
    printed."""
    from urllib.parse import urlparse

    from huggingface_hub import get_token
    vals = [os.environ.get("AI_GATEWAY_API_KEY"), urlparse(os.environ.get("DATABASE_URL", "")).password, get_token()]
    return [v for v in vals if v and len(v) >= 8]
fails = 0


def check(ok: bool, what: str) -> None:
    global fails
    fails += not ok
    print(("ok    " if ok else "FAIL  ") + what)


def t(config: str) -> pl.LazyFrame:
    return pl.scan_parquet(OUT / "data" / config / "*.parquet")


files = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file())
stray = [f for f in files if not (re.fullmatch(r"data/\w+/part-\d{5}\.parquet", f)
                                  or f in ("README.md", "restore_yahoo.py"))]
check(not stray, f"only dataset files ({len(files)} files){': stray ' + str(stray[:5]) if stray else ''}")
configs = sorted({f.split("/")[1] for f in files if f.startswith("data/")})

with connect() as conn, conn.cursor() as cur:
    cur.execute("select id from questions where not display_ok")
    hidden = pl.Series("id", [r["id"] for r in cur])

qids = t("questions").select("id").collect()["id"]
check(qids.n_unique() == len(qids), f"questions: {len(qids):,} unique ids")
check(not qids.is_in(hidden.implode()).any(), "questions: no hidden question")
for config in ("answers", "question_meta", "placements", "human_dists"):
    if config in configs:
        ids = t(config).select("question_id").unique().collect()["question_id"]
        check(ids.is_in(qids.implode()).all(), f"{config}: every row points at a shipped question")

q = t("questions")
y = q.filter(pl.col("source").is_in(["yahoo_closed", "yahoo_topics"])).collect()
check(y.filter(pl.col("source") == "yahoo_closed")["text"].null_count() == (y["source"] == "yahoo_closed").sum(),
      "yahoo_closed: text blank")
check(y.filter(pl.col("source") == "yahoo_topics")["state"].null_count() == (y["source"] == "yahoo_topics").sum(),
      "yahoo_topics: state blank")
check((y["redistribution"] == "text_withheld").all(), f"yahoo: {len(y):,} rows marked text_withheld")
check(y["restore_ref"].null_count() == 0, "yahoo: every row has a restore_ref")
check(not y["meta"].str.contains("yahoo_title").any(), "yahoo: no yahoo_title in meta")
other = q.filter(~pl.col("source").is_in(["yahoo_closed", "yahoo_topics"]))
check(other.filter(pl.col("redistribution") != "full").select(pl.len()).collect().item() == 0,
      "every other row ships in full")

if "human_dists" in configs:
    bad = t("human_dists").filter(pl.col("source").str.contains("(?i)movielens|last\\.fm")).select(pl.len())
    check(bad.collect().item() == 0, "human_dists: no MovieLens/Last.fm rows")

if "calls_sample" in configs:
    calls = t("calls_sample").collect()
    with connect() as conn, conn.cursor() as cur:
        words, shipped = set(), set()
        cur.execute("select text, state, display_ok and source not like 'yahoo%' ships from questions")
        for r in cur:
            ws = {r["text"], *((v for v in (r["state"] or {}).values() if isinstance(v, str)))}
            (shipped if r["ships"] else words).update(ws)
    # a hidden duplicate shares its words with the kept twin, and templated instructions are ours
    words = [w for w in words - shipped if w and len(w) > 25]
    blob = "\n".join(calls["request"].to_list())
    leaked = [w for w in words if w in blob]
    check(not leaked, f"calls_sample: no hidden or Yahoo words ({len(calls)} calls){': ' + leaked[0][:60] if leaked else ''}")

secrets = own_secrets()
check(len(secrets) >= 2, f"found {len(secrets)} of this project's credentials to search for")
for config in configs:
    lf = t(config)
    cols = [c for c, d in lf.collect_schema().items() if d == pl.String]
    found = lf.select([pl.any_horizontal([pl.col(c).str.contains(v, literal=True) for v in secrets]).sum().alias(c)
                       for c in cols]).collect().row(0, named=True)
    found = [c for c, n in found.items() if n]
    check(not found, f"{config}: none of this project's credentials{' (in ' + ', '.join(found) + ')' if found else ''}")

card = (OUT / "README.md").read_text()
check("{{" not in card and "(not built)" not in card, "card: every placeholder filled")

size = sum((OUT / f).stat().st_size for f in files)
print(f"\n{len(configs)} tables, {size / 1e9:.2f} GB, {fails} failure(s)")
sys.exit(1 if fails else 0)
