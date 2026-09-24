"""Run the pipeline stages in order over everything pending (docs/06-pipeline.md §4)."""
import time

from .answer import answer_pending, screen_pending
from .measure import measure_all, rollup
from .mix import mix_report
from .place import place_pending


def run_all(limit: int | None = None):
    for name, fn in [("place", place_pending), ("screen", screen_pending), ("answer", answer_pending)]:
        t = time.time()
        print(f"[{name}] {fn(limit=limit)} ({time.time() - t:.0f}s)", flush=True)
    for name, fn in [("measure", measure_all), ("rollup", rollup)]:
        t = time.time()
        print(f"[{name}] {fn()} ({time.time() - t:.0f}s)", flush=True)
    print(mix_report())
