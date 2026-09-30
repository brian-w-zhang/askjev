"""Export the corpus as a Hugging Face dataset: one Parquet folder per table, plus the dataset card.

Writes data/hf/askjev/ (gitignored). Reads Postgres, data/analysis/experiments.json, docs/experiments/*.md and a
sample of data/calls. No Jev calls. The card is scripts/hf/card.md; the /publish-dataset skill exports, checks and uploads.

What ships and what doesn't:
- Hidden questions (display_ok false: contested politics, sensitive, thinned) are left out of every table, the same
  rule as the map.
- Yahoo Answers (Webscope terms forbid redistribution): the question's own words are withheld. yahoo_closed blanks
  `text` (Jev was asked the Yahoo title), yahoo_topics blanks `state` (the post it classified; the instruction is
  ours). `restore_ref` points at the row in community-datasets/yahoo_answers_topics; restore_yahoo.py puts it back.
- MovieLens and Last.fm human data: their licenses forbid redistributing the ratings, so those human_dists rows are
  dropped. The questions (our templates around titles/artist names) and Jev's answers ship.
- Not exported: question_links (every link is a hidden duplicate pointing at its kept twin), embeddings (regenerate with BAAI/bge-small-en-v1.5), map layout, the raw call log (a sample ships).

  uv run python scripts/export_hf.py            # everything
  uv run python scripts/export_hf.py --only tree,experiments
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "portrait"))
from askjev.config import CALLS, DATA, RAW, ROOT  # noqa: E402
from askjev.db import connect  # noqa: E402
from jev_jobs import job_of  # noqa: E402

OUT = DATA / "hf" / "askjev"  # exactly what gets uploaded
COUNTS = DATA / "hf" / "counts.json"
HF_DIR = Path(__file__).resolve().parent / "hf"
LICENSE = "cc-by-nc-sa-4.0"
ROWS_PER_FILE = 1_000_000
BATCH = 50_000

WITHHOLD = {"yahoo_closed": "text", "yahoo_topics": "state"}  # source -> field whose words are Yahoo's
STRIP_META = {"yahoo_title"}  # copies of withheld words
NO_HUMAN = re.compile(r"MovieLens|Last\.fm", re.I)  # human_dists.source whose data may not be redistributed
UPSTREAM = "community-datasets/yahoo_answers_topics"
SECRETISH = re.compile(r"authorization|bearer|api[_-]?key|sk-[A-Za-z0-9]{16}|password", re.I)
CALLS_PER_JOB = 20

VISIBLE = "select id from questions where display_ok"


def js(v) -> str | None:
    return None if v is None else json.dumps(v, ensure_ascii=False)


class Sink:
    """Rows -> data/<config>/part-NNNNN.parquet, a new file every ROWS_PER_FILE rows."""

    def __init__(self, config: str, schema: pa.Schema):
        self.dir = OUT / "data" / config
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        self.schema, self.part, self.in_file, self.n, self.w = schema, 0, 0, 0, None

    def write(self, rows: list[dict]) -> None:
        while rows:
            if self.w is None:
                self.w = pq.ParquetWriter(self.dir / f"part-{self.part:05d}.parquet", self.schema, compression="zstd")
            take = rows[: ROWS_PER_FILE - self.in_file]
            rows = rows[len(take):]
            self.w.write_table(pa.Table.from_pylist(take, schema=self.schema))
            self.in_file += len(take)
            self.n += len(take)
            if self.in_file >= ROWS_PER_FILE:
                self.w.close()
                self.w, self.part, self.in_file = None, self.part + 1, 0

    def close(self) -> int:
        if self.w:
            self.w.close()
        return self.n


def stream(conn, sql: str, config: str, schema: pa.Schema, fix=lambda r: r) -> int:
    sink = Sink(config, schema)
    with conn.cursor(name=f"x_{config}") as cur:
        cur.itersize = BATCH
        cur.execute(sql)
        while rows := cur.fetchmany(BATCH):
            sink.write([r for r in map(fix, rows) if r is not None])
    n = sink.close()
    print(f"{config}: {n:,} rows")
    return n


def S(*cols: tuple[str, pa.DataType]) -> pa.Schema:
    return pa.schema(list(cols))


STR, F32, I32, BOOL, TS = pa.string(), pa.float32(), pa.int32(), pa.bool_(), pa.timestamp("us", tz="UTC")


# ---------------------------------------------------------------- tables

def yahoo_refs() -> dict[str, str]:
    """yahoo_closed source_item_id (sha1 of the cleaned title) -> upstream train row id, recomputed from the raw
    parquet the adapter read."""
    refs = {}
    for fn in ("train_0.parquet", "train_1.parquet"):
        df = pl.read_parquet(RAW / "yahoo_closed" / fn, columns=["id", "question_title"])
        for rid, title in df.iter_rows():
            t = " ".join(html.unescape(title or "").replace("\\n", " ").split())
            if t:
                refs.setdefault(hashlib.sha1(t.encode()).hexdigest()[:16], f"{UPSTREAM}:train:{rid}")
    return refs


def questions(conn, human_withheld: set[str]) -> tuple[int, set[str]]:
    refs = yahoo_refs()
    withheld_words: set[str] = set()  # for scrubbing the calls sample
    schema = S(("id", STR), ("node_id", STR), ("path", STR), ("hemisphere", STR), ("kind", STR), ("shape", STR),
               ("primitive", STR), ("text", STR), ("options", STR), ("state", STR), ("template_id", STR),
               ("origin", STR), ("source", STR), ("source_item_id", STR), ("license", STR), ("truth", STR),
               ("flags", pa.list_(STR)), ("meta", STR), ("redistribution", STR), ("restore_ref", STR),
               ("human_data_withheld", BOOL), ("created_at", TS))

    def fix(r):
        field = WITHHOLD.get(r["source"])
        ref = None
        if field == "text":
            withheld_words.add(r["text"])
            r["text"] = None
            ref = refs.get(r["source_item_id"])
        elif field == "state":
            withheld_words.update(v for v in (r["state"] or {}).values() if isinstance(v, str))
            r["state"] = None
            ref = f"{UPSTREAM}:{r['source_item_id']}"  # "test:<id>"
        meta = {k: v for k, v in (r["meta"] or {}).items() if k not in STRIP_META}
        return {**r, "path": str(r["path"]) if r["path"] else None, "options": js(r["options"]),
                "state": js(r["state"]), "truth": js(r["truth"]), "meta": js(meta),
                "redistribution": "text_withheld" if field else "full", "restore_ref": ref,
                "human_data_withheld": r["id"] in human_withheld}

    n = stream(conn, """select id, node_id, path::text path, hemisphere, kind, shape, primitive, text, options, state,
                               template_id, origin, source, source_item_id, license, truth, flags, meta, created_at
                        from questions where display_ok order by id""", "questions", schema, fix)
    return n, withheld_words


def human_withheld_ids(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(f"select distinct question_id, source from human_dists where question_id in ({VISIBLE})")
        return {r["question_id"] for r in cur if NO_HUMAN.search(r["source"] or "")}


def human_dists(conn) -> int:
    schema = S(("question_id", STR), ("population", STR), ("n", I32), ("distribution", STR), ("source", STR),
               ("wave", STR))
    fix = lambda r: None if NO_HUMAN.search(r["source"] or "") else {**r, "distribution": js(r["distribution"])}
    return stream(conn, f"select * from human_dists where question_id in ({VISIBLE}) order by question_id",
                  "human_dists", schema, fix)


def answers(conn) -> int:
    schema = S(("probe_id", STR), ("question_id", STR), ("universe_id", STR), ("frame", STR), ("variant_kind", STR),
               ("variant_params", STR), ("option_order", STR), ("distribution", STR), ("confidence", F32),
               ("score_scalar", F32), ("model_served", STR), ("request_hash", STR), ("created_at", TS))
    fix = lambda r: {**r, "variant_params": js(r["variant_params"]), "option_order": js(r["option_order"]),
                     "distribution": js(r["distribution"])}
    return stream(conn, f"""select p.id probe_id, p.question_id, p.universe_id, p.frame, p.variant_kind,
                                   p.variant_params, a.option_order, a.distribution, a.confidence, a.score_scalar,
                                   a.model_served, a.request_hash, a.created_at
                            from probes p join answers a on a.probe_id = p.id
                            where p.question_id in ({VISIBLE}) order by p.question_id, p.id""",
                  "answers", schema, fix)


def question_meta(conn) -> int:
    real = ["p_top", "margin", "entropy", "confidence", "p_top_h", "objective", "disagreement", "ambiguous",
            "reveals_self", "stability", "universe_invariance", "noise", "frame_gap", "human_gap", "brier",
            "placement_conf", "separation"]
    schema = S(("question_id", STR), ("model_served", STR), ("top", STR), ("top_h", STR), ("correct", BOOL),
               *[(c, F32) for c in real])
    return stream(conn, f"""select question_id, model_served, top, top_h, correct, {', '.join(real)}
                            from question_meta where question_id in ({VISIBLE}) order by question_id""",
                  "question_meta", schema)


def placements(conn) -> int:
    schema = S(("question_id", STR), ("node_id", STR), ("node_version", I32), ("method", STR), ("confidence", F32),
               ("separation", F32), ("path_probs", STR), ("runner_up", STR), ("created_at", TS))
    fix = lambda r: {**r, "path_probs": js(r["path_probs"])}
    return stream(conn, f"""select question_id, node_id, node_version, method, confidence, separation, path_probs,
                                   runner_up::text runner_up, created_at
                            from placements where question_id in ({VISIBLE}) order by question_id, created_at""",
                  "placements", schema, fix)


def tree(conn) -> int:
    schema = S(("id", STR), ("parent_id", STR), ("path", STR), ("depth", I32), ("hemisphere", STR), ("label", STR),
               ("description", STR), ("not_for", STR), ("examples", pa.list_(STR)), ("source", STR),
               ("status", STR), ("version", I32), ("ord", I32), ("share", F32), ("wikidata_qid", STR),
               ("sitelinks", I32), ("pageviews", pa.int64()), ("choice_card", STR))
    fix = lambda r: {**r, "choice_card": js(r["choice_card"])}
    return stream(conn, """select id, parent_id, path::text path, depth, hemisphere, label, description, not_for,
                                  examples, source, status, version, ord, share, qid wikidata_qid, sitelinks,
                                  pageviews, choice_card
                           from nodes order by path""", "tree", schema, fix)


def experiments(conn, withheld_words: set[str]) -> int:
    with conn.cursor() as cur:
        cur.execute(VISIBLE)
        visible = {r["id"] for r in cur}
    d = json.loads((DATA / "analysis" / "experiments.json").read_text())
    fam = dict(d["families"]) if isinstance(d["families"], list) else d["families"]
    text_cols = ["title", "question", "why", "sourcing", "collection", "scoring", "compared_with", "limits",
                 "result", "evidence", "robustness"]
    json_cols = ["evaluation", "take", "chart", "topics", "sources", "case"]
    rows, dropped, leaks = [], 0, []
    quoted = sorted((w for w in withheld_words if len(w) > 20), key=len, reverse=True)
    for e in d["experiments"]:
        ids = [r["id"] for r in e.get("rows") or []]
        keep = [i for i in ids if i in visible]
        dropped += len(ids) - len(keep)
        md = ROOT / "docs" / "experiments" / f"{e['id']}.md"
        row = {"id": e["id"], "family": e["family"], "family_label": fam.get(e["family"], e.get("family_label")),
               **{c: e.get(c) or None for c in text_cols}, **{c: js(e.get(c)) for c in json_cols},
               "question_ids": keep, "n_questions": len(keep),
               "writeup": md.read_text() if md.exists() else None}
        for c, v in row.items():  # an example quoted in a write-up: withheld here too, the doc keeps it
            if isinstance(v, str):
                for w in quoted:
                    if w in v:
                        v = v.replace(w, "[Yahoo Answers question withheld]")
                        leaks.append(e["id"])
                row[c] = v
        rows.append(row)
    schema = S(("id", STR), ("family", STR), ("family_label", STR), *[(c, STR) for c in text_cols],
               *[(c, STR) for c in json_cols], ("question_ids", pa.list_(STR)), ("n_questions", I32),
               ("writeup", STR))
    sink = Sink("experiments", schema)
    sink.write(rows)
    print(f"experiments: {sink.close():,} rows ({dropped} hidden question ids dropped; Yahoo quotes withheld in "
          f"{sorted(set(leaks))})")
    return len(rows)


def calls_sample(conn, withheld_words: set[str]) -> int:
    """A few raw calls per job, exactly as sent and returned, so readers can see what Jev read. A call is skipped if
    any string in its request is a hidden question or withheld Yahoo text, or if it looks like it holds a secret."""
    banned, shipped = set(withheld_words), set()
    with conn.cursor() as cur:
        cur.execute("select text, state, display_ok from questions")
        for r in cur:
            ws = {r["text"], *(v for v in (r["state"] or {}).values() if isinstance(v, str))}
            (shipped if r["display_ok"] else banned).update(ws)
    # a hidden duplicate shares its words with the kept twin; short strings are option labels and the like
    banned = [w for w in banned - (shipped - withheld_words) if w and len(w) > 25]

    files = sorted(CALLS.rglob("*.jsonl"))
    random.Random("askjev-hf").shuffle(files)
    got: dict[str, list[dict]] = defaultdict(list)
    skipped = Counter()
    for f in files:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if SECRETISH.search(line):
                    skipped["secret-like"] += 1
                    continue
                try:
                    c = json.loads(line)
                except ValueError:
                    continue
                qq = (c.get("request") or {}).get("questions") or {}
                if c.get("repeat") or not qq or "response" not in c:
                    continue
                job = Counter(job_of(k, v) for k, v in qq.items()).most_common(1)[0][0]
                if len(got[job]) >= CALLS_PER_JOB:
                    continue
                req = json.dumps(c["request"], ensure_ascii=False)  # words can sit inside instructions or longer text
                if any(w in req for w in banned):
                    skipped["hidden or withheld"] += 1
                    continue
                got[job].append({"request_hash": c["hash"], "job": job, "latency_ms": c.get("latency_ms"),
                                 "request": js(c["request"]), "response": js(c["response"])})
        if len(got) >= 10 and all(len(v) >= CALLS_PER_JOB for v in got.values()) and len(files) > 50:
            break
    schema = S(("request_hash", STR), ("job", STR), ("latency_ms", I32), ("request", STR), ("response", STR))
    sink = Sink("calls_sample", schema)
    sink.write([r for v in got.values() for r in v])
    n = sink.close()
    print(f"calls_sample: {n} calls over {len(got)} jobs; skipped {dict(skipped)}")
    return n


# ---------------------------------------------------------------- card

def card(counts: dict[str, int]) -> str:
    """scripts/hf/card.md with {{license}}, {{configs}} and {{n_<config>}} filled in."""
    configs = "\n".join(f"- config_name: {c}\n  data_files: data/{c}/*.parquet" for c in counts)
    fill = {"license": LICENSE, "configs": configs, **{f"n_{k}": f"{v:,}" for k, v in counts.items()}}
    return re.sub(r"\{\{(\w+)\}\}", lambda m: fill.get(m.group(1), "(not built)"), (HF_DIR / "card.md").read_text())




# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated configs to (re)build; the card always rebuilds")
    only = set(filter(None, ap.parse_args().only.split(",")))
    want = lambda c: not only or c in only
    OUT.mkdir(parents=True, exist_ok=True)
    withheld: set[str] = set()
    with connect() as conn:
        hw = human_withheld_ids(conn)
        if want("questions") or want("experiments") or want("calls_sample"):
            _, withheld = questions(conn, hw)
        for name, fn in [("answers", answers), ("question_meta", question_meta), ("placements", placements),
                         ("tree", tree), ("human_dists", human_dists)]:
            if want(name):
                fn(conn)
        if want("experiments"):
            experiments(conn, withheld)
        if want("calls_sample"):
            calls_sample(conn, withheld)
    order = ["questions", "answers", "question_meta", "tree", "placements", "human_dists",
             "experiments", "calls_sample"]
    counts = {k: sum(pq.ParquetFile(f).metadata.num_rows for f in (OUT / "data" / k).glob("*.parquet"))
              for k in order if (OUT / "data" / k).exists()}  # from what's on disk, so partial runs stay right
    COUNTS.write_text(json.dumps(counts, indent=1))
    (OUT / "README.md").write_text(card(counts))
    shutil.copy(HF_DIR / "restore_yahoo.py", OUT / "restore_yahoo.py")
    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"wrote {OUT} ({size / 1e9:.2f} GB)")


if __name__ == "__main__":
    main()
