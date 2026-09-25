"""Template split (docs/10-expansion.md §4; decisions log: high-volume Machine templates become topic nodes).

A node over the node cap whose load comes from templates (Machine datasets, pairwise taste sets...) gets one
grown child per template
(>= MIN_TEMPLATE rows), with the label and description authored in authored/template_nodes.yaml:

  <template_id>: {key: short_snake_key, label: "...", description: "Questions a program asks ...", examples: [...]}

The move is deterministic (a question's template decides its child), so no Jev routing is needed. Existing
node ids and paths never change; only questions move down. Every split is logged in tree_events.
"""

from __future__ import annotations

import yaml

from . import db
from .config import AUTHORED
from .embed import embed, to_pg

NODE_CAP = 1500
MIN_TEMPLATE = 100
SPEC = AUTHORED / "template_nodes.yaml"


def candidates() -> list[dict]:
    """Templates (>= MIN_TEMPLATE rows) sitting directly on a node that is over the cap."""
    with db.connect() as conn:
        return conn.execute(
            """with over as (select node_id, count(*) total from questions where display_ok group by 1 having count(*) > %s)
               select q.node_id, q.template_id, count(*) c, max(f.total) total from questions q join over f on f.node_id=q.node_id
               join nodes n on n.id=q.node_id
               where q.template_id is not null and n.depth >= 2  -- never add children to the root or a hemisphere
               group by 1,2 having count(*) >= %s order by 1, 3 desc""",
            (NODE_CAP, MIN_TEMPLATE),
        ).fetchall()


def split(dry_run: bool = False) -> str:
    rows = candidates()
    by_node: dict[str, list[dict]] = {}
    for r in rows:
        by_node.setdefault(r["node_id"], []).append(r)
    spec = yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}
    # only templates with an authored label split out (a label is the judgment that the template is a topic)
    missing = sorted({r["template_id"] for v in by_node.values() for r in v if r["template_id"] not in spec})
    # labeled templates only, and never one already sitting in its own template node
    by_node = {k: [t for t in v if t["template_id"] in spec and not k.endswith("." + spec[t["template_id"]]["key"])]
               for k, v in by_node.items()}
    by_node = {k: v for k, v in by_node.items() if v}
    if dry_run:
        lines = [f"{n}: " + ", ".join(f"{r['template_id']}={r['c']}" for r in v) for n, v in by_node.items()]
        return "\n".join(lines + ([f"unlabeled (stay put): {missing}"] if missing else []))
    out = []
    with db.connect() as conn:
        for node, temps in by_node.items():
            parent = conn.execute("select * from nodes where id=%s", (node,)).fetchone()
            taken = {r["id"] for r in conn.execute("select id from nodes where parent_id=%s", (node,))}
            specs = [spec[t["template_id"]] for t in temps]
            vecs = embed([f"{s['label']}: {s['description']}" for s in specs])
            moved = {}
            for i, (t, s, v) in enumerate(zip(temps, specs, vecs)):
                cid = f"{node}.{s['key']}"
                if cid not in taken:
                    card = {"label": s["label"], "what": s["description"]}
                    if s.get("examples"):
                        card["examples"] = s["examples"][:3]
                    conn.execute(
                        """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, not_for, examples,
                             source, locked, ord, choice_card, embedding)
                           values (%s,%s,(select path from nodes where id=%s) || %s::ltree,%s,%s,%s,%s,%s,%s,'grown',false,%s,%s,%s)""",
                        (cid, node, node, s["key"], parent["depth"] + 1, parent["hemisphere"], s["label"], s["description"],
                         s.get("not_for"), s.get("examples") or [], 300 + i, db.Jsonb(card), to_pg(v)),
                    )
                cur = conn.execute(
                    "update questions set node_id=%s, path=(select path from nodes where id=%s) where node_id=%s and template_id=%s",
                    (cid, cid, node, t["template_id"]),
                )
                moved[cid] = cur.rowcount
                conn.execute(
                    """insert into placements (question_id, node_id, node_version, method, confidence)
                       select id, %s, 1, 'template_split', 1.0 from questions where node_id=%s and template_id=%s""",
                    (cid, cid, t["template_id"]),
                )
            conn.execute(
                "insert into tree_events (type, node_ids, proposal, metrics, accepted) values ('template_split',%s,%s,%s,true)",
                ([node], db.Jsonb({t["template_id"]: spec[t["template_id"]] for t in temps}), db.Jsonb({"moved": moved})),
            )
            out.append(f"{node}: {moved}")
        conn.commit()
    return "\n".join(out) or "nothing to split"
