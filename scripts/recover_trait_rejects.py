"""Recover round-trip rejects (docs/10-expansion.md §7) from the reject log, with no Jev calls: the walk's placement is
already in authored/rejected/round_trip_rejects.jsonl.

  --at placed    trait banks: keep each reject whose placement is in Self at the walk's node, meta.measures = the
                 intended trait (optionally only rejects whose intended node starts with --prefix), and back-fill
                 meta.measures on the bank's accepted rows
  --at intended  format banks (memes, who-would-win, shower thoughts, ratings): keep each reject at the author's node

  uv run python scripts/recover_trait_rejects.py authored/g5_w9_self_b.jsonl
  uv run python scripts/recover_trait_rejects.py authored/g5_w2_personality.jsonl --prefix self.personality.
  uv run python scripts/recover_trait_rejects.py authored/g5_w11_internet.jsonl --at intended
"""

import argparse
from pathlib import Path

import orjson

from askjev import db
from askjev.authored import AUTHORED, load_g5, trait_placement_ok
from askjev.ingest import ingest_questions

ap = argparse.ArgumentParser()
ap.add_argument("bank")
ap.add_argument("--at", choices=("placed", "intended"), default="placed")
ap.add_argument("--prefix", default="")
a = ap.parse_args()
bank = Path(a.bank)
by_text = {q.text: (q, node) for q, node in load_g5([bank])}
with db.connect() as c:
    have = {r["id"] for r in c.execute("select id from questions where source=%s", (bank.stem,))}
    active = {r["id"] for r in c.execute("select id from nodes where status='active'")}
    if a.at == "placed":
        n = 0
        for q, node in by_text.values():
            if q.id in have and node.startswith(a.prefix):
                n += c.execute("update questions set meta = meta || jsonb_build_object('measures', %s::text) where id=%s",
                               (node, q.id)).rowcount
        c.commit()
        print(f"back-filled measures on {n} accepted rows")
out = []
for line in (AUTHORED / "rejected" / "round_trip_rejects.jsonl").read_bytes().splitlines():
    r = orjson.loads(line)
    if r.get("file") != bank.name or r["text"] not in by_text or not r["intended"].startswith(a.prefix):
        continue
    q, node = by_text[r["text"]]
    if q.id in have:
        continue
    if a.at == "placed":
        if not trait_placement_ok(r["placed"]):
            continue
        q.node_hint = r["placed"]
        q.meta.update({"round_trip": {"placed": r["placed"], "recovered": True}, "measures": node})
    else:
        if node not in active or r["placed"].count(".") < 1:
            continue
        q.node_hint = node
        q.meta["round_trip"] = {"placed": r["placed"], "recovered": True, "kept_at": "intended"}
    out.append(q)
    have.add(q.id)
print(f"recovered {ingest_questions(out)} rejects ({a.at})")
