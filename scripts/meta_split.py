"""Meta split (docs/10-expansion.md §7): move a source's questions into grown children named by a meta field, when the
field is a real topic (e.g. character_traits by `work`: "Game of Thrones characters"). One child per (current node, value)
group with >= --min questions; smaller groups stay put. Deterministic; logged in tree_events.

  uv run python scripts/meta_split.py --source character_traits --key work --min 50 \
      --label "{value} Characters" --desc "How crowds of fans describe characters from {value}: which of two traits fits each one better."
"""

import argparse
import re

from askjev import db
from askjev.embed import embed, to_pg


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "x"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--min", type=int, default=50)
    ap.add_argument("--label", required=True)
    ap.add_argument("--desc", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    with db.connect() as c:
        groups = c.execute(
            """select q.node_id, q.meta->>%s v, count(*) n from questions q join nodes n on n.id=q.node_id
               where q.source=%s and n.depth >= 2 and q.meta ? %s group by 1,2 having count(*) >= %s order by 3 desc""",
            (a.key, a.source, a.key, a.min),
        ).fetchall()
        print(f"{len(groups)} groups, {sum(g['n'] for g in groups)} questions")
        if a.dry_run:
            for g in groups[:15]:
                print(g["node_id"], "|", g["v"], g["n"])
            return
        moved = {}
        for i, g in enumerate(groups):
            parent = c.execute("select depth, hemisphere from nodes where id=%s", (g["node_id"],)).fetchone()
            key = slug(g["v"])
            cid = f"{g['node_id']}.{key}"
            label, desc = a.label.format(value=g["v"]), a.desc.format(value=g["v"])
            card = {"label": label, "what": desc}
            c.execute(
                """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, examples, source, locked, ord,
                     choice_card, embedding)
                   values (%s,%s,(select path from nodes where id=%s) || %s::ltree,%s,%s,%s,%s,'{}','grown',false,%s,%s,%s)
                   on conflict (id) do nothing""",
                (cid, g["node_id"], g["node_id"], key, parent["depth"] + 1, parent["hemisphere"], label, desc, 600 + i,
                 db.Jsonb(card), to_pg(embed([f"{label}: {desc}"])[0])),
            )
            n = c.execute(
                """update questions set node_id=%s, path=(select path from nodes where id=%s)
                   where source=%s and node_id=%s and meta->>%s=%s""",
                (cid, cid, a.source, g["node_id"], a.key, g["v"]),
            ).rowcount
            c.execute("""insert into placements (question_id, node_id, node_version, method, confidence)
                         select id, %s, 1, 'meta_split', 1.0 from questions where node_id=%s and source=%s""", (cid, cid, a.source))
            moved[cid] = n
        c.execute(
            "insert into tree_events (type, node_ids, proposal, metrics, accepted) values ('meta_split', %s, %s, %s, true)",
            (sorted({g["node_id"] for g in groups}), db.Jsonb({"source": a.source, "key": a.key, "min": a.min}), db.Jsonb({"moved": moved})),
        )
        c.commit()
        print(f"created/filled {len(moved)} children, moved {sum(moved.values())}")


if __name__ == "__main__":
    main()
