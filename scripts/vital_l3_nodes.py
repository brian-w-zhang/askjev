"""Add Wikipedia Vital Articles Level 3 (~1,000 most important topics) as topic nodes under their World L2
(docs/02-tree.md §5), then move that topic's entity questions (sources/vital4, state.topic) into the node.
Section → L2 mapping reuses sources/vital4 (via each article's Level-4 record); excluded sections are skipped."""
import importlib.util
import re

import orjson

from askjev import db
from askjev.config import RAW, SOURCES
from askjev.embed import embed, to_pg

spec = importlib.util.spec_from_file_location("vital4", SOURCES / "vital4" / "adapter.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

l4 = {}
for line in (RAW / "vital" / "level4.jsonl").read_bytes().splitlines():
    r = orjson.loads(line)
    l4[r["title"]] = r
l3 = [orjson.loads(line) for line in (RAW / "vital" / "level3.jsonl").read_bytes().splitlines()]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


rows, skipped = [], 0
with db.connect() as conn:
    nodes = {r["id"]: r for r in conn.execute("select id, label, depth, path::text path from nodes where status='active'")}
    for a in l3:
        rec = l4.get(a["title"])
        section = (rec or a)["section"]
        if v4._starts(section, v4.EXCLUDE):
            skipped += 1
            continue
        m = v4.lookup(section)
        if not m or m[0] not in nodes:
            skipped += 1
            continue
        parent = m[0]
        nid = f"{parent}.{slug(a['title'])}"
        if nid in nodes:
            continue
        desc = f"Questions specifically about {a['title']}" + (f" ({a['shortdesc']})." if a.get("shortdesc") else ".")
        rows.append({"id": nid, "parent": parent, "label": a["title"], "desc": desc,
                     "not_for": f"General questions about {nodes[parent]['label']} stay at {nodes[parent]['label']}.",
                     "depth": nodes[parent]["depth"] + 1, "qid": a.get("qid"), "sitelinks": a.get("sitelinks"),
                     "title": a["title"]})
    vecs = embed([f"{r['label']}: {r['desc']}" for r in rows])
    for i, (r, v) in enumerate(zip(rows, vecs)):
        card = {"label": r["label"], "what": r["desc"], "not_for": r["not_for"]}
        conn.execute(
            """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, not_for, examples, source,
                 locked, ord, qid, sitelinks, choice_card, embedding)
               values (%s,%s,(select path from nodes where id=%s) || %s::ltree,%s,'world',%s,%s,%s,'{}','vital',false,%s,%s,%s,%s,%s)
               on conflict (id) do nothing""",
            (r["id"], r["parent"], r["parent"], r["id"].rsplit(".", 1)[-1], r["depth"], r["label"], r["desc"], r["not_for"],
             1000 + i, r["qid"], r["sitelinks"], db.Jsonb(card), to_pg(v)))
    # move entity questions about this topic into the new node
    moved = 0
    for r in rows:
        cur = conn.execute(
            """update questions set node_id=%s, path=(select path from nodes where id=%s)
               where source='vital4' and state->>'topic' = %s and node_id = %s returning id""",
            (r["id"], r["id"], r["title"], r["parent"]))
        ids = [x["id"] for x in cur.fetchall()]
        for qid in ids:
            conn.execute("insert into placements (question_id, node_id, node_version, method, confidence) values (%s,%s,1,'vital_topic',1.0)", (qid, r["id"]))
        moved += len(ids)
    conn.commit()
print(f"vital L3 nodes added: {len(rows)} (skipped {skipped}); vital4 questions moved into them: {moved}")
