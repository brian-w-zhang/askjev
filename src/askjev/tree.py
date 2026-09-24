"""Load hand-written tree YAML (tree/*.yaml) into `nodes`, build choice cards + embeddings.

Node id = dot path without the root (e.g. "world.sports.basketball.nba"); ltree path = "root." + id.
Each node's `choice_card` is the entry Jev sees when this node is an option among its siblings
(TypeSafe's contrastive-criteria shape): {what, not_for, examples, includes}.
"""

from __future__ import annotations

import yaml

from . import db
from .config import TREE_DIR
from .embed import embed, to_pg

HEMISPHERES = ["world", "self", "machine"]

ROOT = {
    "id": "root",
    "label": "Everything Asked",
    "description": "Every closed question a human or a program could ask.",
    "not_for": None,
    "examples": [],
}


def option_key(node_id: str) -> str:
    return node_id.rsplit(".", 1)[-1]


def card(node: dict) -> dict:
    c = {"label": node["label"], "what": node["description"]}
    if node.get("not_for"):
        c["not_for"] = node["not_for"]
    if node.get("examples"):
        c["examples"] = node["examples"][:3]
    kids = [k["label"] for k in node.get("children") or []]
    if kids:
        c["includes"] = kids[:10]
    return c


def flatten(node: dict, parent: str | None, depth: int, out: list, ord_: int = 0):
    nid = node["id"]
    out.append(
        {
            "id": nid,
            "parent_id": parent,
            "path": "root" if nid == "root" else "root." + nid,
            "depth": depth,
            "hemisphere": "root" if nid == "root" else nid.split(".")[0],
            "label": node["label"],
            "description": node["description"],
            "not_for": node.get("not_for"),
            "examples": node.get("examples") or [],
            "share": node.get("share"),
            "ord": ord_,
            "card": card(node),
        }
    )
    for i, ch in enumerate(node.get("children") or []):
        flatten(ch, nid, depth + 1, out, i)


def read_tree() -> dict:
    root = dict(ROOT, children=[])
    for h in HEMISPHERES:
        with open(TREE_DIR / f"{h}.yaml") as fh:
            root["children"].append(yaml.safe_load(fh))
    return root


def load_tree() -> str:
    rows: list[dict] = []
    flatten(read_tree(), None, 0, rows)
    vecs = embed([f"{r['label']}: {r['description']}" for r in rows])
    with db.connect() as conn:
        existing = {r["id"]: r for r in conn.execute("select id, description, not_for, examples, label from nodes")}
        for r, v in zip(rows, vecs):
            old = existing.get(r["id"])
            changed = old is not None and (
                old["description"] != r["description"] or old["label"] != r["label"]
                or old["not_for"] != r["not_for"] or list(old["examples"]) != r["examples"]
            )
            conn.execute(
                """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, not_for, examples,
                                      source, locked, ord, share, choice_card, embedding)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,'hand',true,%s,%s,%s,%s)
                   on conflict (id) do update set parent_id=excluded.parent_id, path=excluded.path,
                     depth=excluded.depth, label=excluded.label, description=excluded.description,
                     not_for=excluded.not_for, examples=excluded.examples, ord=excluded.ord, share=excluded.share,
                     choice_card=excluded.choice_card, embedding=excluded.embedding, status='active',
                     version = nodes.version + (case when %s then 1 else 0 end), updated_at=now()""",
                (r["id"], r["parent_id"], r["path"], r["depth"], r["hemisphere"], r["label"], r["description"],
                 r["not_for"], r["examples"], r["ord"], r["share"], db.Jsonb(r["card"]), to_pg(v), changed),
            )
        # retire hand nodes that disappeared from the YAML
        ids = [r["id"] for r in rows]
        gone = conn.execute(
            "update nodes set status='retired' where source='hand' and not (id = any(%s)) and status='active' returning id",
            (ids,),
        ).fetchall()
        conn.commit()
    by_depth: dict[int, int] = {}
    for r in rows:
        by_depth[r["depth"]] = by_depth.get(r["depth"], 0) + 1
    return f"loaded {len(rows)} nodes by depth {dict(sorted(by_depth.items()))}; retired {len(gone)}"


def children(conn, node_id: str) -> list[dict]:
    return conn.execute(
        "select id, label, choice_card from nodes where parent_id=%s and status='active' order by ord",
        (node_id,),
    ).fetchall()
