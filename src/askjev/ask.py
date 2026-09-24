"""Single-question flows used by the UI: `walk` (Jev's path for a query) and `ask` (dedupe → place → screen+answer).

Fast placement (docs/02-tree.md §7): the nodes of the 10 nearest placed questions become candidates and ONE
Jev Choice picks among them (+ `none`); the full beam walk is the fallback.
"""

from __future__ import annotations

import asyncio

from . import db
from .answer import answer_pending, screen_pending
from .embed import embed, question_text, to_pg
from .jev import JevClient, Request, answers, gateway_question
from .measure import measure_all, rollup
from .model import KINDS, SHAPES, Question
from .place import TreeIndex, place_one, question_state

DUP_THRESHOLD = 0.7
FAST_ACCEPT = 0.5


async def _one(req: Request) -> dict:
    c = JevClient()
    try:
        return (await c.run([req]))[req.hash]
    finally:
        await c.close()


def walk(text: str) -> dict:
    async def go():
        c = JevClient()
        try:
            return await place_one(c, TreeIndex(), {"text": text})
        finally:
            await c.close()

    return asyncio.run(go())


def nearest(vec, k: int = 10, placed_only: bool = True) -> list[dict]:
    with db.connect() as conn:
        return conn.execute(
            "select id, text, node_id, 1 - (embedding <=> %s::vector) as sim from questions "
            + ("where node_id is not null " if placed_only else "")
            + "order by embedding <=> %s::vector limit %s",
            (to_pg(vec), to_pg(vec), k),
        ).fetchall()


def find_duplicate(q: dict, neigh: list[dict]) -> str | None:
    cands = [n for n in neigh if n["sim"] >= 0.8][:8]
    if not cands:
        return None
    qs = {
        f"d{i}": gateway_question(
            "noul",
            {"question": "Is `candidate` asking essentially the same question as `question` (same meaning and same answer options)?",
             "candidate": n["text"]},
        )
        for i, n in enumerate(cands)
    }
    resp = asyncio.run(_one(Request(question_state(q), qs)))
    best, best_p = None, 0.0
    for i, n in enumerate(cands):
        a = answers(resp).get(f"d{i}")
        if a and a.p_yes > best_p:
            best, best_p = n["id"], a.p_yes
    return best if best_p >= DUP_THRESHOLD else None


def fast_place(q: dict, neigh: list[dict]) -> dict | None:
    idx = TreeIndex()
    cand_nodes = []
    for n in neigh:
        if n["sim"] < 0.45:
            continue
        if n["node_id"] and n["node_id"] not in cand_nodes and n["node_id"] in idx.nodes:
            cand_nodes.append(n["node_id"])
    cand_nodes = cand_nodes[:8]
    if len(cand_nodes) < 1:
        return None
    crit = {f"n{i}": {"topic_path": nid.replace(".", " > "), **(idx.nodes[nid]["choice_card"] or {})} for i, nid in enumerate(cand_nodes)}
    crit["none"] = {"what": "None of these topic areas fits the question well."}
    gq = gateway_question("choice", {"question": "Which topic area does the question in `question` belong to?"}, crit)
    resp = asyncio.run(_one(Request(question_state(q), {"fast": gq})))
    a = answers(resp).get("fast")
    if not a:
        return None
    key = max(a.dist, key=a.dist.get)
    if key == "none" or a.dist[key] < FAST_ACCEPT:
        return None
    ranked = sorted(a.dist.values(), reverse=True)
    sep = min(ranked[0] / max(ranked[1], 1e-6), 100.0) if len(ranked) > 1 else 100.0
    return {"node": cand_nodes[int(key[1:])], "confidence": a.dist[key], "separation": round(sep, 3),
            "path_probs": [[cand_nodes[int(key[1:])], "fast", a.dist[key]]], "method": "jev_fast"}


def infer_tag(q: dict, hemisphere: str) -> str:
    if hemisphere == "machine":
        opts = {s: None for s in sorted(SHAPES)}
        instr = "What kind of decision does the question in `question` ask a program to make about its input?"
    else:
        opts = {
            "personality": "What someone is like (traits, habits of mind)",
            "values": "What is right or wrong, fair or unfair",
            "taste": "What someone likes or prefers",
            "evaluative": "Whether something is good, overrated, hard, important",
            "social": "What most people think or do",
            "factual": "What is true; has a checkable correct answer",
            "forecast": "Whether something will happen in the future",
            "perception": "How something looks, sounds, feels, tastes",
        }
        instr = "What sort of judgment does the question in `question` ask for?"
    resp = asyncio.run(_one(Request(question_state(q), {"tag": gateway_question("choice", instr, opts)})))
    a = answers(resp).get("tag")
    return max(a.dist, key=a.dist.get) if a else ("classify" if hemisphere == "machine" else "evaluative")


def ask(payload: dict) -> dict:
    text = (payload.get("text") or "").strip()
    prim = payload.get("primitive")
    opts = payload.get("options")
    state = payload.get("state")
    probe = Question(text, prim, "world", "asked", "ask-box", opts, state=state, kind="evaluative")
    q = {"id": probe.id, "text": text, "options": opts, "state": state}
    errs = [e for e in probe.validate() if "kind" not in e]
    if errs:
        return {"error": "; ".join(errs)}
    with db.connect() as conn:
        exists = conn.execute("select id from questions where id=%s", (probe.id,)).fetchone()
        if exists:
            conn.execute("update questions set ask_count = ask_count + 1 where id=%s", (probe.id,))
            conn.commit()
            return result(probe.id, duplicate_of=probe.id)
    vec = embed([question_text(text, opts, state)])[0]
    neigh = nearest(vec, 10)
    dup = find_duplicate(q, neigh)
    if dup:
        with db.connect() as conn:
            conn.execute("update questions set ask_count = ask_count + 1 where id=%s", (dup,))
            conn.commit()
        return result(dup, duplicate_of=dup)
    placement = fast_place(q, neigh)
    if placement is None:
        placement = walk_q(q)
        placement["method"] = "jev"
    node = placement.get("node") or "root"
    hemisphere = node.split(".")[0] if node != "root" else "world"
    tag = infer_tag(q, hemisphere)
    with db.connect() as conn:
        conn.execute(
            """insert into questions (id, node_id, path, hemisphere, kind, shape, primitive, text, options, state, origin,
                 source, embedding, ask_count, meta)
               values (%s,%s,(select path from nodes where id=%s),%s,%s,%s,%s,%s,%s,%s,'asked','ask-box',%s,1,'{}')""",
            (probe.id, node, node, hemisphere, None if hemisphere == "machine" else tag,
             tag if hemisphere == "machine" else None, prim, text, db.Jsonb(opts) if opts is not None else None, db.Jsonb(state) if state is not None else None, to_pg(vec)),
        )
        conn.execute(
            """insert into placements (question_id, node_id, node_version, method, confidence, separation, path_probs)
               values (%s,%s,(select version from nodes where id=%s),%s,%s,%s,%s)""",
            (probe.id, node, node, placement.get("method", "jev"), placement.get("confidence"),
             placement.get("separation"), db.Jsonb(placement.get("path_probs"))),
        )
        conn.commit()
    screen_pending(ids=[probe.id])
    answer_pending(ids=[probe.id])
    measure_all(ids=[probe.id])
    return result(probe.id, placement=placement)


def walk_q(q: dict) -> dict:
    async def go():
        c = JevClient()
        try:
            return await place_one(c, TreeIndex(), q)
        finally:
            await c.close()

    return asyncio.run(go())


def result(qid: str, duplicate_of: str | None = None, placement: dict | None = None) -> dict:
    with db.connect() as conn:
        q = conn.execute("select id, node_id, flags, display_ok, text, primitive, options from questions where id=%s", (qid,)).fetchone()
        m = conn.execute("select * from question_meta where question_id=%s", (qid,)).fetchone()
        ans = conn.execute(
            """select p.frame, p.variant_kind, a.distribution from probes p join answers a on a.probe_id=p.id
               where p.question_id=%s and p.universe_id='base'""",
            (qid,),
        ).fetchall()
    out_ans = {}
    for a in ans:
        if a["variant_kind"] == "base":
            out_ans[a["frame"]] = a["distribution"]
    meta = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in (m or {}).items()}
    return {
        "question_id": qid, "duplicate_of": duplicate_of, "node_id": q["node_id"] if q else None,
        "placement": placement, "flags": q["flags"] if q else [], "display_ok": q["display_ok"] if q else None,
        "meta": meta, "answers": out_ans,
    }
