"""Restructure job: split / group / grow (docs/02-tree.md §8).

Two steps, because naming new nodes is an authoring ("LLM") step done by Claude Code or a subagent, never a gateway model:
  1. `propose`: find overfull nodes (split), over-wide nodes (group), and low-confidence pools (grow); cluster
     their questions with local embeddings; write authored/restructure/<node>.json with cluster samples and
     empty child slots to fill in (label, description, not_for, examples).
  2. `apply <file>`: create the proposed children, have Jev re-route the node's questions AND a sample of sibling
     questions, and accept only if: each new child gets >= MIN_CHILD questions, median separation >= 1.5,
     and < 10% of sibling-sample questions move. Otherwise it is rejected and nothing changes. Every attempt is
     logged in tree_events; moves are logged in placements.
Locked (hand-written) nodes are never edited or moved; new children may be added *below* them.
"""

from __future__ import annotations

import asyncio
import statistics
from pathlib import Path

import numpy as np
import orjson

from . import db
from .config import AUTHORED
from .embed import embed, to_pg
from .jev import JevClient, Request, answers, gateway_question
from .place import question_state

SPLIT_MIN_DIRECT = 150
GROUP_MAX_CHILDREN = 30
GROW_MIN_POOL = 20
MIN_CHILD = 20
PROPOSALS = AUTHORED / "restructure"


def _vec(s) -> np.ndarray:
    if isinstance(s, str):
        return np.array([float(x) for x in s.strip("[]").split(",")], dtype=np.float32)
    return np.asarray(s, dtype=np.float32)


def cluster(vecs: np.ndarray, kmax: int = 6, min_size: int = MIN_CHILD) -> list[list[int]] | None:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    best, best_s = None, 0.05
    for k in range(2, min(kmax, len(vecs) // min_size) + 1):
        km = KMeans(n_clusters=k, n_init=5, random_state=0).fit(vecs)
        sizes = np.bincount(km.labels_)
        if sizes.min() < min_size:
            continue
        s = silhouette_score(vecs, km.labels_, sample_size=min(2000, len(vecs)), random_state=0)
        if s > best_s:
            best, best_s = km.labels_, s
    if best is None:
        return None
    return [list(np.where(best == c)[0]) for c in range(best.max() + 1)]


def candidates() -> dict:
    with db.connect() as conn:
        split = conn.execute(
            # machine instances of one template are one "question" for overload purposes
            """select n.id, count(distinct coalesce(q.template_id, q.id)) c from nodes n join questions q on q.node_id = n.id
               where n.status='active' and n.depth >= 3 group by n.id
               having count(distinct coalesce(q.template_id, q.id)) > %s""",
            (SPLIT_MIN_DIRECT,),
        ).fetchall()
        group = conn.execute(
            """select parent_id id, count(*) c from nodes where status='active' and parent_id is not null
               group by parent_id having count(*) > %s""",
            (GROUP_MAX_CHILDREN,),
        ).fetchall()
        grow = conn.execute(
            """select q.node_id id, count(*) c from questions q join question_meta m on m.question_id=q.id
               join nodes n on n.id=q.node_id
               where m.placement_conf < 0.4 and n.depth >= 3 group by q.node_id having count(*) >= %s""",
            (GROW_MIN_POOL,),
        ).fetchall()
    return {"split": split, "group": group, "grow": grow}


def propose() -> str:
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    c = candidates()
    written = 0
    with db.connect() as conn:
        for kind in ("split", "grow"):
            for row in c[kind]:
                extra = " and m.placement_conf < 0.4" if kind == "grow" else ""
                qs = conn.execute(
                    "select q.id, q.text, q.embedding::text emb from questions q left join question_meta m on m.question_id=q.id "
                    "where q.node_id=%s" + extra, (row["id"],)
                ).fetchall()
                vecs = np.stack([_vec(q["emb"]) for q in qs])
                groups = cluster(vecs)
                if not groups:
                    continue
                prop = {
                    "type": kind, "node": row["id"], "n_questions": len(qs),
                    "clusters": [{"size": len(g), "samples": [qs[i]["text"] for i in g[:12]],
                                  "child": {"key": "", "label": "", "description": "", "not_for": "", "examples": []}}
                                 for g in groups],
                }
                (PROPOSALS / f"{kind}__{row['id']}.json").write_bytes(orjson.dumps(prop, option=orjson.OPT_INDENT_2))
                written += 1
        for row in c["group"]:
            kids = conn.execute(
                "select id, label, description, embedding::text emb from nodes where parent_id=%s and status='active'", (row["id"],)
            ).fetchall()
            vecs = np.stack([_vec(k["emb"]) for k in kids])
            groups = cluster(vecs, kmax=8, min_size=3)
            if not groups:
                continue
            prop = {"type": "group", "node": row["id"],
                    "clusters": [{"members": [kids[i]["id"] for i in g], "samples": [kids[i]["label"] for i in g],
                                  "child": {"key": "", "label": "", "description": "", "not_for": "", "examples": []}}
                                 for g in groups]}
            (PROPOSALS / f"group__{row['id']}.json").write_bytes(orjson.dumps(prop, option=orjson.OPT_INDENT_2))
            written += 1
    return (f"candidates: split={len(c['split'])} group={len(c['group'])} grow={len(c['grow'])}; "
            f"proposals written: {written} (fill in child labels in {PROPOSALS}, then `askjev restructure --apply <file>`)")


def _card(ch: dict) -> dict:
    card = {"label": ch["label"], "what": ch["description"]}
    if ch.get("not_for"):
        card["not_for"] = ch["not_for"]
    if ch.get("examples"):
        card["examples"] = ch["examples"][:3]
    return card


async def _route(qs: list[dict], crit: dict) -> dict[str, tuple[str, float, float]]:
    c = JevClient()
    try:
        reqs = {q["id"]: Request(question_state(q), {"r": gateway_question(
            "choice", {"question": "Which topic area does the question in `question` belong to?"}, crit)}) for q in qs}
        res = await c.run(list(reqs.values()))
    finally:
        await c.close()
    out = {}
    for qid, r in reqs.items():
        a = answers(res[r.hash]).get("r")
        if not a:
            continue
        ranked = sorted(a.dist.items(), key=lambda kv: kv[1], reverse=True)
        sep = ranked[0][1] / max(ranked[1][1], 1e-6) if len(ranked) > 1 else 100.0
        out[qid] = (ranked[0][0], ranked[0][1], min(sep, 100.0))
    return out


def apply(path: str, min_child: int = MIN_CHILD) -> str:
    prop = orjson.loads(Path(path).read_bytes())
    if prop["type"] == "group":
        return "group apply: not needed yet (no node exceeds the child cap); skipped"
    node = prop["node"]
    children = [c["child"] for c in prop["clusters"] if c["child"].get("label")]
    if len(children) < 2:
        return "proposal has < 2 labeled children; fill them in first"
    for ch in children:
        ch["key"] = ch.get("key") or "_".join(ch["label"].lower().split())[:30]
    with db.connect() as conn:
        parent = conn.execute("select * from nodes where id=%s", (node,)).fetchone()
        direct = conn.execute("select id, text, options, state from questions where node_id=%s", (node,)).fetchall()
        sib = conn.execute(
            "select q.id, q.text, q.options, q.state, q.node_id from questions q join nodes n on n.id=q.node_id "
            "where n.parent_id=%s order by random() limit 60", (node,)
        ).fetchall()
        existing_kids = conn.execute("select id, choice_card from nodes where parent_id=%s and status='active'", (node,)).fetchall()
    crit = {k["id"].rsplit(".", 1)[-1]: k["choice_card"] for k in existing_kids}
    for ch in children:
        crit[ch["key"]] = _card(ch)
    crit["here"] = {"what": f"The question is about {parent['label']} in general, not one listed sub-area."}
    routed = asyncio.run(_route(direct + sib, crit))
    new_keys = {ch["key"] for ch in children}
    counts = {k: 0 for k in new_keys}
    seps = []
    for q in direct:
        r = routed.get(q["id"])
        if r and r[0] in new_keys:
            counts[r[0]] += 1
            seps.append(r[2])
    moved = sum(1 for q in sib if routed.get(q["id"], ("",))[0] in new_keys)
    move_rate = moved / max(len(sib), 1)
    med_sep = statistics.median(seps) if seps else 0.0
    ok = all(v >= min_child for v in counts.values()) and med_sep >= 1.5 and move_rate < 0.10
    metrics = {"counts": counts, "median_separation": med_sep, "sibling_move_rate": move_rate}
    with db.connect() as conn:
        conn.execute("insert into tree_events (type, node_ids, proposal, metrics, accepted) values (%s,%s,%s,%s,%s)",
                     (prop["type"], [node], db.Jsonb(prop), db.Jsonb(metrics), ok))
        if ok:
            vecs = embed([f"{c['label']}: {c['description']}" for c in children])
            for i, (ch, v) in enumerate(zip(children, vecs)):
                cid = f"{node}.{ch['key']}"
                conn.execute(
                    """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, not_for, examples,
                         source, locked, ord, choice_card, embedding)
                       values (%s,%s,(select path from nodes where id=%s) || %s::ltree,%s,%s,%s,%s,%s,%s,'grown',false,%s,%s,%s)""",
                    (cid, node, node, ch["key"], parent["depth"] + 1, parent["hemisphere"], ch["label"], ch["description"],
                     ch.get("not_for"), ch.get("examples") or [], 100 + i, db.Jsonb(_card(ch)), to_pg(v)),
                )
            for q in direct:
                r = routed.get(q["id"])
                if r and r[0] in new_keys:
                    cid = f"{node}.{r[0]}"
                    conn.execute("update questions set node_id=%s, path=(select path from nodes where id=%s) where id=%s",
                                 (cid, cid, q["id"]))
                    conn.execute(
                        "insert into placements (question_id, node_id, node_version, method, confidence, separation) values (%s,%s,1,'split',%s,%s)",
                        (q["id"], cid, r[1], r[2]),
                    )
        conn.commit()
    return f"{'ACCEPTED' if ok else 'REJECTED'} {prop['type']} of {node}: {metrics}"


def restructure(dry_run: bool = False, apply_path: str | None = None) -> str:
    if apply_path:
        return apply(apply_path)
    if dry_run:
        c = candidates()
        return f"split={[(r['id'], r['c']) for r in c['split']]} group={[(r['id'], r['c']) for r in c['group']]} grow={[(r['id'], r['c']) for r in c['grow']]}"
    return propose()
