"""After adding children to a node, re-place the questions sitting directly on it (start the Jev walk at that node)."""
import asyncio
import sys

from askjev import db
from askjev.place import place_many

parents = sys.argv[1:]
with db.connect() as conn:
    rows = conn.execute("select id, text, options, state, node_id from questions where node_id = any(%s)", (parents,)).fetchall()
res = asyncio.run(place_many(rows, {r["id"]: r["node_id"] for r in rows}))
moved = 0
with db.connect() as conn:
    for r in rows:
        x = res.get(r["id"], {})
        node = x.get("node")
        if not node or node == r["node_id"] or "error" in x:
            continue
        conn.execute("update questions set node_id=%s, path=(select path from nodes where id=%s) where id=%s", (node, node, r["id"]))
        conn.execute("insert into placements (question_id, node_id, node_version, method, confidence, separation, path_probs) values (%s,%s,1,'reroute',%s,%s,%s)",
                     (r["id"], node, x.get("confidence"), x.get("separation"), db.Jsonb(x.get("path_probs"))))
        moved += 1
    conn.commit()
print(f"re-placed {len(rows)} questions on {parents}; moved {moved}")
