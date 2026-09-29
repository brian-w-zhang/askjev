"""Hide most of a templated source from display, keeping a fixed random sample per topic (docs/08, 2026-09-28).

A template filled in thousands of ways (the Moral Machine's self-driving-car dilemma: 26,020 scenarios) crowds its
topics without adding much past the first thousand or so. This keeps the first `--per-node` shown questions of each
topic in the source's own salted-hash order (the order its waves were drawn in) and hides the rest: display_ok=false
plus the 'thinned' flag. Nothing is deleted; the answers stay; `--undo` shows them again.

  uv run python scripts/thin_source.py --source moral_machine --per-node 1000           # dry run
  uv run python scripts/thin_source.py --source moral_machine --per-node 1000 --apply
  uv run python scripts/thin_source.py --source moral_machine --undo --apply
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from collections import defaultdict
from pathlib import Path

from askjev import db


def salt(source: str) -> str:
    spec = importlib.util.spec_from_file_location("adapter", Path("sources") / source / "adapter.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.SALT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--per-node", type=int, default=1000)
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    with db.connect() as c:
        if a.undo:
            n = c.execute("select count(*) as n from questions where source=%s and 'thinned' = any(flags)", (a.source,)).fetchone()["n"]
            print(f"{n} thinned questions to show again")
            if a.apply:
                c.execute("""update questions set display_ok = true, flags = array_remove(flags, 'thinned'),
                               meta = meta - 'thin_reason' where source=%s and 'thinned' = any(flags)""", (a.source,))
                c.commit()
            return
        s = salt(a.source)
        rows = c.execute("select id, node_id, source_item_id from questions where source=%s and display_ok", (a.source,)).fetchall()
        by = defaultdict(list)
        for r in rows:
            by[r["node_id"]].append(r)
        hide = []
        for node, rs in sorted(by.items()):
            rs.sort(key=lambda r: hashlib.sha256(f"{s}|{r['source_item_id']}".encode()).hexdigest())
            hide += [r["id"] for r in rs[a.per_node:]]
            print(f"{node}: {len(rs)} shown -> {min(len(rs), a.per_node)}")
        print(f"hide {len(hide)} of {len(rows)}")
        if a.apply and hide:
            why = f"thinned to {a.per_node} per topic: a template filled in many ways crowds its topics"
            c.execute("""update questions set display_ok = false, flags = array_append(flags, 'thinned'),
                           meta = meta || jsonb_build_object('thin_reason', %s::text)
                         where id = any(%s) and not ('thinned' = any(flags))""", (why, hide))
            c.commit()
            print("applied")


if __name__ == "__main__":
    main()
