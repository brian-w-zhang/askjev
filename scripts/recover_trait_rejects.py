"""Recover round-trip rejects from trait banks (src/askjev/authored.py TRAIT_BANKS; docs/10-expansion.md §7): the
walk's placement is already in authored/rejected/round_trip_rejects.jsonl, so this ingests each reject whose placement
is in Self at that node with meta.measures = the intended trait, and back-fills meta.measures on the bank's accepted
rows. No Jev calls.

  uv run python scripts/recover_trait_rejects.py authored/g5_w9_self_b.jsonl
"""

import sys
from pathlib import Path

import orjson

from askjev import db
from askjev.authored import AUTHORED, load_g5, trait_placement_ok
from askjev.ingest import ingest_questions

bank = Path(sys.argv[1])
by_text = {q.text: (q, node) for q, node in load_g5([bank])}
with db.connect() as c:
    have = {r["id"] for r in c.execute("select id from questions where source=%s", (bank.stem,))}
    n = 0
    for q, node in by_text.values():
        if q.id in have:
            n += c.execute("update questions set meta = meta || jsonb_build_object('measures', %s::text) where id=%s",
                           (node, q.id)).rowcount
    c.commit()
print(f"back-filled measures on {n} accepted rows")
out = []
for line in (AUTHORED / "rejected" / "round_trip_rejects.jsonl").read_bytes().splitlines():
    r = orjson.loads(line)
    if r.get("file") != bank.name or not trait_placement_ok(r["placed"]) or r["text"] not in by_text:
        continue
    q, node = by_text[r["text"]]
    if q.id in have:
        continue
    q.node_hint = r["placed"]
    q.meta.update({"round_trip": {"placed": r["placed"], "recovered": True}, "measures": node})
    out.append(q)
    have.add(q.id)
print(f"recovered {ingest_questions(out)} rejects at the walk's Self placement")
