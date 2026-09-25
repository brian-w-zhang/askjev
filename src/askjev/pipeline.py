"""Run the pipeline stages in order over everything pending (docs/06-pipeline.md §4).

Screen and answer run in chunks so progress is committed incrementally (a crash loses at most one chunk,
and even that is recovered from the request cache on rerun)."""
import time

from . import db
from .config import DATA
from .answer import answer_pending, screen_pending
from .dedupe import dedupe
from .measure import measure_all, rollup
from .mix import mix_report
from .place import place_pending

CHUNK = 5000


def _pending(sql: str) -> int:
    with db.connect() as conn:
        return conn.execute(sql).fetchone()["c"]


def run_all(limit: int | None = None):
    t = time.time()
    if (DATA / "logs" / "place.lock").exists():  # a separate placement job (e.g. scripts/descend.py) owns the unplaced rows
        print("[place] skipped: data/logs/place.lock present", flush=True)
    else:
        print(f"[place] {place_pending(limit=limit)} ({time.time() - t:.0f}s)", flush=True)
    for name, fn, sql in [
        ("screen", screen_pending,
         "select count(*) c from questions q left join question_meta m on m.question_id=q.id where m.objective is null"),
        ("answer", answer_pending,
         "select count(*) c from questions q where not exists (select 1 from probes p join answers a on a.probe_id=p.id where p.question_id=q.id)"),
    ]:
        last = None
        while True:
            n = _pending(sql)
            if n == 0 or n == last:  # nothing left, or only permanently failing items remain
                break
            last = n
            t = time.time()
            print(f"[{name}] {n} pending → {fn(limit=min(CHUNK, limit or CHUNK))} ({time.time() - t:.0f}s)", flush=True)
            if limit:
                break
    import os
    if os.environ.get("ASKJEV_LIGHT"):  # Jev lane: corpus-wide stages run at wave gates instead of every pass
        print("[light] skipped dedupe/measure/rollup/mix (run them at the gate)", flush=True)
        return
    for name, fn in [("dedupe", dedupe), ("measure", measure_all), ("rollup", rollup)]:
        t = time.time()
        print(f"[{name}] {fn()} ({time.time() - t:.0f}s)", flush=True)
    print(mix_report())
