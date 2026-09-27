"""Build the production copy of the database (docs/07-ui.md, Deployment) and, optionally, upload the star snapshot.

    uv run python scripts/sync_prod.py [TARGET_URL]      # default: PROD_DATABASE_URL from .env
    uv run python scripts/sync_prod.py --stars-only       # just upload data/stars (+ semantic layout) to Blob
    uv run python scripts/sync_prod.py --delta            # only the questions added or hidden since the last sync
    add --deploy to point the Vercel project at the new snapshot and redeploy

The site reads a trimmed, read-mostly copy, not the pipeline's database:
- only the tables the site reads, only displayable questions and the rows that belong to them;
- embeddings as half precision (`halfvec`) with a 1-bit HNSW index for search (292 MB instead of 1.85 GB;
  #1 result matches exact search 97% of the time on 200 test queries), no trigram indexes (search no longer
  uses them), no foreign keys (nothing writes to it but the Jev call cache);
- the Jev call log without its raw responses (the cards only show which version answered, and timing).
Everything loads into a `stage` schema while the site keeps serving the current copy, then one transaction swaps
the tables in (a failed sync leaves the live copy untouched). Each big copy waits for the target's write-ahead log
to drain first: a sync writes the whole database once more as log, and on a small disk an unthrottled load filled it
and turned the branch read-only. Jev calls the site cached since the last sync are carried over.
Read-only on the source database. Needs Postgres 17 client tools.
"""

from __future__ import annotations

import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PGBIN = next((p for p in ["/opt/homebrew/opt/postgresql@17/bin"] if Path(p, "pg_dump").exists()), None)
PG_DUMP = str(Path(PGBIN, "pg_dump")) if PGBIN else shutil.which("pg_dump")
PSQL = str(Path(PGBIN, "psql")) if PGBIN else shutil.which("psql")

VISIBLE = "select id from questions where display_ok and embedding is not null"
# table -> the rows the site needs (a SELECT over the source)
COPY = {
    "universes": "select * from universes",
    "nodes": "select * from nodes",
    "node_stats": "select * from node_stats",
    "questions": None,  # every column but the embedding (see qvec)
    "qvec": f"select id, embedding::halfvec(384) from questions where id in ({VISIBLE})",
    "question_meta": f"select * from question_meta where question_id in ({VISIBLE})",
    "probes": f"select * from probes where question_id in ({VISIBLE})",
    "answers": f"select a.* from answers a join probes p on p.id = a.probe_id where p.question_id in ({VISIBLE})",
    "human_dists": f"select * from human_dists where question_id in ({VISIBLE})",
    "placements": f"select * from placements where question_id in ({VISIBLE})",
    "question_links": f"select * from question_links where from_id in ({VISIBLE}) and to_id in ({VISIBLE})",
    "calls": (
        "select request_hash, kind, model_served, generation_id, null, latency_ms, input_tokens, created_at, null from calls "
        f"where request_hash in (select a.request_hash from answers a join probes p on p.id = a.probe_id where p.question_id in ({VISIBLE}))"
    ),
}
DROP_INDEXES = {"q_emb", "q_trgm", "q_trgm_gist"}
WAL_LIMIT = 1 << 30  # wait before each copy until the target's log backlog is under this


def staged(sql: str) -> str:
    """The schema dump's table references, pointed at the stage schema (types like public.vector stay)."""
    return re.sub(r"\bpublic\.(" + "|".join(COPY) + r")\b", r"stage.\1", sql)


def env(key: str) -> str | None:
    if os.environ.get(key):
        return os.environ[key]
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def psql(url: str, sql: str) -> None:
    subprocess.run([PSQL, url, "-v", "ON_ERROR_STOP=1", "-q", "-c", sql], check=True)


def schema(src: str, section: str) -> str:
    args = [PG_DUMP, src, "--schema-only", "--no-owner", "--no-privileges", f"--section={section}"]
    for t in COPY:
        if t != "qvec":  # made here, not in the source
            args += ["-t", f"public.{t}"]
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def pre_data(src: str) -> str:
    sql = schema(src, "pre-data")
    # Search vectors live in their own narrow table (qvec), so re-ranking 400 candidates reads ~800-byte rows,
    # not full questions, and search's working set is the index + vectors (~1.1 GB), not the 2 GB table.
    sql = re.sub(r"(CREATE TABLE public\.questions \(.*?),\n\s*embedding public\.vector\(384\)", r"\1", sql, flags=re.S)
    return sql + "\nCREATE TABLE public.qvec (id text PRIMARY KEY, embedding public.halfvec(384) NOT NULL);\n"


def post_data(src: str) -> str:
    out, keep = [], True
    for stmt in re.split(r";\n", schema(src, "post-data")):
        s = stmt.strip()
        if not s or s.startswith("--") and "\n" not in s:
            continue
        body = "\n".join(l for l in s.splitlines() if not l.startswith("--")).strip()
        if not body:
            continue
        if "FOREIGN KEY" in body:
            continue
        m = re.search(r"CREATE (?:UNIQUE )?INDEX (\w+)", body)
        if m and m.group(1) in DROP_INDEXES:
            continue
        out.append(body + ";")
    return "\n".join(out)


def wal_bytes(dst: str) -> int:
    """The target's log beyond what it keeps anyway: Postgres holds min_wal_size (2 GB on PlanetScale) of recycled
    segments for good, so only the excess is backlog that can grow the disk."""
    out = subprocess.run([PSQL, dst, "-At", "-c", "select coalesce(sum(size), 0) - pg_size_bytes(current_setting('min_wal_size')) "
                          "from pg_ls_waldir()"], capture_output=True, text=True)
    return max(0, int(out.stdout.strip() or 0)) if out.returncode == 0 else 0


def wait_for_wal(dst: str, limit: int = WAL_LIMIT, patience: int = 1200) -> None:
    waited = 0
    while (b := wal_bytes(dst)) > limit and waited < patience:
        if not waited:
            print(f"  waiting for the log to drain ({b / 1e9:.1f} GB)")
        time.sleep(20)
        waited += 20


# The upload is the slow part (~0.5 MB/s from a home connection). Vectors as text are ~3 KB a row, in binary 768
# bytes, which takes the whole copy from 8.0 GB to 3.7 GB; for the other tables binary is no smaller.
BINARY = {"questions", "qvec"}


class Snapshot:
    """One view of the source for the whole sync. The copies take hours, and the pipeline keeps writing meanwhile:
    without this, a question hidden mid-sync stays in the tables copied before and drops out of the ones after."""

    def __init__(self, src: str):
        self.proc = subprocess.Popen([PSQL, src, "-At", "-q", "-v", "ON_ERROR_STOP=1"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        self.proc.stdin.write("begin isolation level repeatable read read only;\nselect pg_export_snapshot();\n")
        self.proc.stdin.flush()
        self.id = self.proc.stdout.readline().strip()
        if not self.id:
            raise SystemExit("could not export a source snapshot")

    def args(self) -> list[str]:
        return ["-c", "begin isolation level repeatable read read only", "-c", f"set transaction snapshot '{self.id}'"]

    def close(self) -> None:
        self.proc.stdin.write("commit;\n")
        self.proc.stdin.close()
        self.proc.wait()


def copy_table(src: str, dst: str, table: str, select: str, binary: bool = False, snap: Snapshot | None = None) -> None:
    fmt = " with (format binary)" if binary else ""
    out = subprocess.Popen([PSQL, src, "-q", "-v", "ON_ERROR_STOP=1", *(snap.args() if snap else []),
                            "-c", f"\\copy ({select}) to stdout{fmt}"], stdout=subprocess.PIPE)
    subprocess.run([PSQL, dst, "-v", "ON_ERROR_STOP=1", "-q", "-c", f"\\copy {table} from stdin{fmt}"], stdin=out.stdout, check=True)
    out.stdout.close()
    if out.wait() != 0:
        raise SystemExit(f"copy of {table} failed")


def exists_in_stage(dst: str, name: str) -> bool:
    """An index, or the index behind a primary key, already built in stage."""
    out = subprocess.run([PSQL, dst, "-At", "-c", f"select to_regclass('stage.{name}') is not null"], capture_output=True, text=True)
    return out.stdout.strip() == "t"


def loaded(dst: str, table: str) -> bool:
    out = subprocess.run([PSQL, dst, "-At", "-c", f"select exists (select 1 from stage.{table})"], capture_output=True, text=True)
    return out.stdout.strip() == "t"


def sync_db(src: str, dst: str, resume: bool = False) -> None:
    """resume: keep the tables an interrupted sync already loaded into stage and copy only the rest."""
    if not resume:
        print("schema")
        psql(dst, "create extension if not exists vector; create extension if not exists ltree;")
        psql(dst, "drop schema if exists stage cascade; drop schema if exists old cascade; create schema stage;")
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write(staged(pre_data(src)).replace("CREATE TABLE public.qvec", "CREATE TABLE stage.qvec"))
        subprocess.run([PSQL, dst, "-v", "ON_ERROR_STOP=1", "-q", "-f", f.name], check=True)
    cols = subprocess.run([PSQL, src, "-At", "-c", "select string_agg(quote_ident(column_name), ',' order by ordinal_position) "
                           "from information_schema.columns where table_schema = 'public' and table_name = 'questions' "
                           "and column_name <> 'embedding'"],
                          check=True, capture_output=True, text=True).stdout.strip()
    snap = Snapshot(src)
    for table, select in COPY.items():
        if resume and loaded(dst, table):
            print("have", table)
            continue
        wait_for_wal(dst)
        print("copy", table)
        if table == "questions":
            copy_table(src, dst, f"stage.questions ({cols})", f"select {cols} from questions where id in ({VISIBLE})", True, snap)
        else:
            copy_table(src, dst, f"stage.{table}", select, table in BINARY, snap)
    snap.close()
    # every question the site shows has a vector: drops rows a resumed or older sync copied before a hide
    psql(dst, "delete from stage.questions q where not exists (select 1 from stage.qvec v where v.id = q.id);")
    print("keys and indexes")
    for stmt in staged(post_data(src)).split(";\n"):
        # one statement at a time (the log drains between index builds); the dump's psql directives and
        # session SETs only matter for a whole-file run
        stmt = "\n".join(l for l in stmt.splitlines() if not l.startswith("\\")).strip()
        if stmt and not re.match(r"(SET|SELECT pg_catalog\.set_config)\b", stmt):
            name = re.search(r"(?:CONSTRAINT|INDEX) (\w+)", stmt)
            if resume and name and exists_in_stage(dst, name.group(1)):
                continue  # built before the interruption
            wait_for_wal(dst)
            psql(dst, stmt.rstrip(";") + ";")
    print("search index (1-bit HNSW)")
    wait_for_wal(dst)
    valid = subprocess.run([PSQL, dst, "-At", "-c", "select coalesce((select indisvalid from pg_index "
                            "where indexrelid = to_regclass('stage.q_bin')), false)"], capture_output=True, text=True)
    if not (resume and valid.stdout.strip() == "t"):  # a build that finished server-side after the client dropped counts
        psql(dst, "drop index if exists stage.q_bin;")  # one cut off mid-way can leave an invalid index
        # the server's own maintenance_work_mem: a 1 GB build on this instance size gets its connection killed
        psql(dst, "set max_parallel_maintenance_workers = 0; "
                  "create index q_bin on stage.qvec using hnsw ((binary_quantize(embedding)::bit(384)) bit_hamming_ops);")
    for t in COPY:
        psql(dst, f"analyze stage.{t};")
    print("swap")
    keep = ("insert into stage.calls select * from public.calls on conflict do nothing;"
            if subprocess.run([PSQL, dst, "-At", "-c", "select to_regclass('public.calls') is not null"],
                              capture_output=True, text=True).stdout.strip() == "t" else "")
    moves = ["create schema old;"]
    for t in COPY:
        moves.append(f"alter table if exists public.{t} set schema old;")
        moves.append(f"alter table stage.{t} set schema public;")
    psql(dst, "begin; " + keep + " ".join(moves) + " commit;")
    psql(dst, "drop schema old cascade; drop schema stage cascade;")
    subprocess.run([PSQL, dst, "-At", "-c",
                    "select pg_size_pretty(pg_database_size(current_database())), (select count(*) from questions)"], check=True)


SMALL = ("universes", "nodes", "node_stats")  # whole tables, small enough to replace on every delta


def sync_delta(src: str, dst: str) -> None:
    """Changed rows only: questions that became visible locally since the last sync are added with their rows, and
    questions no longer visible are removed. New rows load into a `delta` schema first; one transaction then applies
    the removals and additions and replaces the small whole tables, so the site never sees half a change."""
    q = lambda url, sql: subprocess.run([PSQL, url, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql], check=True,
                                        capture_output=True, text=True).stdout.split()
    local, prod = set(q(src, VISIBLE)), set(q(dst, "select id from questions"))
    added, removed = sorted(local - prod), sorted(prod - local)
    print(f"delta: {len(added)} to add, {len(removed)} to remove (local {len(local):,}, production {len(prod):,})")
    arr = lambda ids: "'{" + ",".join(ids) + "}'::text[]"
    psql(dst, "drop schema if exists delta cascade; create schema delta;")
    for t in list(COPY) + list(SMALL):
        if t in COPY or t in SMALL:
            psql(dst, f"create table if not exists delta.{t} (like public.{t});")
    if added:
        cols = subprocess.run([PSQL, src, "-At", "-c", "select string_agg(quote_ident(column_name), ',' order by ordinal_position) "
                               "from information_schema.columns where table_schema = 'public' and table_name = 'questions' "
                               "and column_name <> 'embedding'"], check=True, capture_output=True, text=True).stdout.strip()
        a = arr(added)
        sel = {
            "questions": f"select {cols} from questions where id = any({a})",
            "qvec": f"select id, embedding::halfvec(384) from questions where id = any({a})",
            "question_meta": f"select * from question_meta where question_id = any({a})",
            "probes": f"select * from probes where question_id = any({a})",
            "answers": f"select a.* from answers a join probes p on p.id = a.probe_id where p.question_id = any({a})",
            "human_dists": f"select * from human_dists where question_id = any({a})",
            "placements": f"select * from placements where question_id = any({a})",
            "question_links": f"select * from question_links where (from_id = any({a}) or to_id = any({a})) "
                              f"and from_id in ({VISIBLE}) and to_id in ({VISIBLE})",
            "calls": COPY["calls"].replace(f"p.question_id in ({VISIBLE})", f"p.question_id = any({a})"),
        }
        for t, select in sel.items():
            copy_table(src, dst, f"delta.{t}" + (f" ({cols})" if t == "questions" else ""), select, t in BINARY)
    for t in SMALL:
        copy_table(src, dst, f"delta.{t}", COPY[t])
    r = arr(removed) if removed else None
    stmts = ["begin;"]
    if r:
        stmts += [f"delete from answers where probe_id in (select id from probes where question_id = any({r}));",
                  *[f"delete from {t} where question_id = any({r});" for t in ("probes", "question_meta", "human_dists", "placements")],
                  f"delete from question_links where from_id = any({r}) or to_id = any({r});",
                  f"delete from qvec where id = any({r});", f"delete from questions where id = any({r});"]
    for t in COPY:
        stmts.append(f"insert into public.{t} select * from delta.{t} on conflict do nothing;")
    for t in SMALL:
        stmts += [f"delete from public.{t};", f"insert into public.{t} select * from delta.{t};"]
    stmts.append("commit;")
    psql(dst, " ".join(stmts))
    psql(dst, "drop schema delta cascade;")
    for t in list(COPY) + list(SMALL):
        psql(dst, f"analyze {t};")
    print("production now has", q(dst, "select count(*) from questions")[0], "questions")


def upload_stars() -> None:
    """data/stars + the precomputed Meaning layout → Vercel Blob (needs BLOB_READ_WRITE_TOKEN and the Vercel CLI)."""
    token = env("BLOB_READ_WRITE_TOKEN")
    if not token:
        print("no BLOB_READ_WRITE_TOKEN: skipping the snapshot upload")
        return
    stars = ROOT / "data" / "stars"
    sem = stars / "semantic.json"
    try:  # the Meaning layout, as the local dev server computes it from the same data
        import json, ssl
        ctx = ssl.create_default_context(cafile=str(Path.home() / ".portless" / "ca.pem"))
        with urllib.request.urlopen(env("SEMANTIC_URL") or "https://askjev.localhost/api/layout", context=ctx, timeout=120) as r:
            sem.write_text(json.dumps(json.load(r)["coords"]))
    except Exception as e:
        print("no Meaning layout from the dev server:", e)
    # a fresh unguessable folder per sync: nothing stale is ever served, and the files aren't listable
    folder = "stars-" + secrets.token_urlsafe(12)
    urls = {}
    # the read-write token only: an OIDC token left by `vercel env pull` makes the CLI demand a store id too
    blob_env = {k: v for k, v in os.environ.items() if k not in ("VERCEL_OIDC_TOKEN", "BLOB_STORE_ID")}
    blob_env["BLOB_READ_WRITE_TOKEN"] = token
    for f in ["nodes.json", "stars.bin", "ids.txt", "semantic.json"]:
        p = stars / f
        if not p.exists():
            continue
        out = subprocess.run(["vercel", "blob", "put", str(p), "--pathname", f"{folder}/{f}", "--access", "public"],
                             capture_output=True, text=True, env=blob_env)
        if out.returncode:
            raise SystemExit(f"upload of {f} failed: " + re.sub(r"vercel_blob_rw_\w+", "[redacted]", out.stderr.strip()[-400:]))
        m = re.search(r"https://\S+", out.stdout + out.stderr)
        if m:
            urls[f] = m.group(0)
    base = urls["nodes.json"].rsplit("/", 1)[0] if "nodes.json" in urls else None
    print("STARS_URL =", base)
    if base and "--deploy" in sys.argv:
        # point the site at the new snapshot and redeploy (which also clears the CDN's cached answers)
        subprocess.run(["vercel", "env", "rm", "STARS_URL", "production", "--yes"], cwd=ROOT / "web", capture_output=True)
        subprocess.run(["vercel", "env", "add", "STARS_URL", "production"], cwd=ROOT / "web", input=base, text=True, check=True)
        subprocess.run(["vercel", "deploy", "--prod", "--yes"], cwd=ROOT / "web", check=True)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--stars-only" in sys.argv:
        return upload_stars()
    src = env("DATABASE_URL")
    dst = args[0] if args else env("PROD_DATABASE_URL")
    if not src or not dst:
        raise SystemExit("need DATABASE_URL and a target (argument or PROD_DATABASE_URL)")
    if src == dst:
        raise SystemExit("target is the source database")
    if "--delta" in sys.argv:
        return sync_delta(src, dst)
    sync_db(src, dst, "--resume" in sys.argv)
    upload_stars()


if __name__ == "__main__":
    main()
