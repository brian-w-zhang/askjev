"""Run experiments and write their results and docs (docs/16-experiments-plan.md, pass 3).

  uv run python scripts/experiments/run.py                 # every experiment
  uv run python scripts/experiments/run.py taste humor     # families or ids
  uv run python scripts/experiments/run.py --list          # what's registered
Then `scripts/experiments/evaluate.py new` and `scripts/experiments/index.py`.
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from registry import EXPERIMENTS  # noqa: E402
from lib import save  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    todo = [(s, f) for s, f in EXPERIMENTS if not args or s.id in args or s.family in args]
    if "--list" in sys.argv:
        for s, _ in todo:
            print(f"{s.family:14} {s.id}")
        print(len(todo), "experiments")
        return
    ok = bad = 0
    for s, f in todo:
        t = time.time()
        try:
            res = f()
            if res is None:
                print(f"skip {s.id}: no result")
                continue
            save(s, res)
            ok += 1
            print(f"ok   {s.id} ({time.time() - t:.1f}s): {res.result[:120]}")
        except Exception as e:  # one broken experiment shouldn't stop the others
            bad += 1
            print(f"FAIL {s.id}: {e}")
            traceback.print_exc(limit=2)
    print(f"{ok} ok, {bad} failed")


if __name__ == "__main__":
    main()
