"""askjev CLI: `uv run askjev <command> [args]`."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(prog="askjev")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate")
    sub.add_parser("tree")
    s = sub.add_parser("source"); s.add_argument("names", nargs="+")
    s = sub.add_parser("ingest"); s.add_argument("names", nargs="+")
    s = sub.add_parser("authored"); s.add_argument("paths", nargs="*")
    s = sub.add_parser("place"); s.add_argument("--limit", type=int, default=None)
    s = sub.add_parser("screen"); s.add_argument("--limit", type=int, default=None)
    s = sub.add_parser("answer"); s.add_argument("--limit", type=int, default=None)
    sub.add_parser("measure")
    sub.add_parser("rollup")
    sub.add_parser("mix")
    s = sub.add_parser("restructure"); s.add_argument("--dry-run", action="store_true"); s.add_argument("--apply", default=None)
    s = sub.add_parser("pipeline"); s.add_argument("--limit", type=int, default=None)
    s = sub.add_parser("walk"); s.add_argument("--json", action="store_true"); s.add_argument("text")
    s = sub.add_parser("ask"); s.add_argument("--json", action="store_true"); s.add_argument("payload")
    a = p.parse_args(argv)

    if a.cmd == "migrate":
        from .migrate import migrate
        migrate()
    elif a.cmd == "tree":
        from .tree import load_tree
        print(load_tree())
    elif a.cmd == "source":
        from .ingest import run_source
        for n in a.names:
            ok, bad = run_source(n)
            print(f"{n}: {ok} questions ({bad} rejected)")
    elif a.cmd == "ingest":
        from .ingest import ingest_source
        for n in a.names:
            print(f"{n}: {ingest_source(n)} new questions")
    elif a.cmd == "authored":
        from .authored import ingest_authored
        print(ingest_authored(a.paths))
    elif a.cmd == "place":
        from .place import place_pending
        print(place_pending(limit=a.limit))
    elif a.cmd == "screen":
        from .answer import screen_pending
        print(screen_pending(limit=a.limit))
    elif a.cmd == "answer":
        from .answer import answer_pending
        print(answer_pending(limit=a.limit))
    elif a.cmd == "measure":
        from .measure import measure_all
        print(measure_all())
    elif a.cmd == "rollup":
        from .measure import rollup
        print(rollup())
    elif a.cmd == "mix":
        from .mix import mix_report
        print(mix_report())
    elif a.cmd == "restructure":
        from .restructure import restructure
        print(restructure(dry_run=a.dry_run, apply_path=a.apply))
    elif a.cmd == "walk":
        import json
        from .ask import walk
        print(json.dumps(walk(a.text)))
    elif a.cmd == "ask":
        import json
        from .ask import ask
        print(json.dumps(ask(json.loads(a.payload)), default=str))
    elif a.cmd == "pipeline":
        from .pipeline import run_all
        run_all(limit=a.limit)


if __name__ == "__main__":
    sys.exit(main())
