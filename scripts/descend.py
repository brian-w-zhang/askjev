"""Descend (docs/10-expansion.md §3 gate): questions that an adapter hint placed deterministically on a node that has
children, where that node is over the node cap, are handed back to Jev's beam walk *starting from that node*, so they
settle into the right child (or stay, via `here`). Ids, answers and the node itself don't change. Then run
`uv run askjev place`.

  uv run python scripts/descend.py [--cap 1500] [--dry-run]
"""

import argparse

from askjev import db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=1500)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sql = """with over as (select node_id from questions where display_ok group by 1 having count(*) > %(cap)s),
                  parents as (select distinct parent_id from nodes where status='active')
             select q.id, q.node_id from questions q
             join placements p on p.question_id=q.id and p.method='deterministic' and p.node_id=q.node_id
             where q.node_id in (select node_id from over) and q.node_id in (select parent_id from parents)"""
    with db.connect() as conn:
        rows = conn.execute(sql, {"cap": a.cap}).fetchall()
        by = {}
        for r in rows:
            by[r["node_id"]] = by.get(r["node_id"], 0) + 1
        print(f"{len(rows)} questions on {len(by)} nodes: {by}")
        if a.dry_run or not rows:
            return
        ids = [r["id"] for r in rows]
        # keep the node as the walk's start (the hint) and clear the placement so `askjev place` picks them up
        conn.execute(
            """update questions set meta = meta || jsonb_build_object('node_hint', node_id, 'descended_from', node_id),
                                   node_id = null, path = null where id = any(%s)""", (ids,))
        conn.commit()
        print("cleared; now run: uv run askjev place (touch data/logs/place.lock first so the Jev lane skips placement)")


if __name__ == "__main__":
    main()
