"""Jev beam placement over the topic tree (docs/02-tree.md §7).

One Choice per beam node per level. All beam nodes of one question share a state (the question),
so each level is a single request per question. Many questions run concurrently.
Every node offers extra options `here` (belongs at this node itself) and `none` (doesn't belong here).
Path score = geometric mean of step probabilities. Separation = best / runner-up path score.
"""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field

from . import db
from .jev import JevClient, Request, answers, gateway_question

BEAM = 3
MIN_STEP = 0.3


@dataclass
class Path:
    node: str
    logp: float = 0.0
    steps: int = 0
    probs: list = field(default_factory=list)
    done: bool = False
    dead: bool = False

    @property
    def score(self) -> float:
        return math.exp(self.logp / self.steps) if self.steps else 1.0


class TreeIndex:
    def __init__(self):
        with db.connect() as conn:
            rows = conn.execute(
                "select id, parent_id, label, description, choice_card from nodes where status='active' order by ord"
            ).fetchall()
        self.nodes = {r["id"]: r for r in rows}
        self.kids: dict[str, list[str]] = {}
        for r in rows:
            if r["parent_id"]:
                self.kids.setdefault(r["parent_id"], []).append(r["id"])

    def criteria(self, nid: str) -> dict:
        crit = {}
        for k in self.kids.get(nid, []):
            crit[k.rsplit(".", 1)[-1]] = self.nodes[k]["choice_card"]
        if nid != "root":
            lab = self.nodes[nid]["label"]
            crit["here"] = {"what": f"The question is about {lab} in general, or does not fit any one listed sub-area more specifically."}
            crit["none"] = {"what": f"The question does not belong under {lab} at all."}
        return crit

    def question(self, nid: str) -> dict:
        lab = self.nodes[nid]["label"] if nid != "root" else "all questions"
        return gateway_question(
            "choice",
            {
                "question": f"Within {lab}, which topic area does the question in `question` belong to?",
                "focus": "Judge what the question is about (its subject and what kind of judgment it asks for), not its wording. "
                         "If it needs a specific input such as a message or document, judge the domain of that input.",
            },
            self.criteria(nid),
        )


def question_state(q: dict) -> dict:
    s = {"question": q["text"]}
    if q.get("options"):
        opts = q["options"]
        if isinstance(opts, dict):
            # show descriptions when present (keys like "a"/"b" carry no content)
            s["answer_options"] = [str(v)[:160] if v else k for k, v in list(opts.items())[:12]]
        else:
            s["answer_options"] = opts
    if q.get("state"):
        s["input_excerpt"] = str(q["state"])[:400]
    return s


async def place_one(client: JevClient, idx: TreeIndex, q: dict, start: str = "root") -> dict:
    beam = [Path(start)]
    finished: list[Path] = []
    state = question_state(q)
    for _level in range(10):
        live = [p for p in beam if not p.done]
        if not live:
            break
        expand = [p for p in live if idx.kids.get(p.node)]
        for p in live:
            if not idx.kids.get(p.node):
                p.done = True
                finished.append(p)
        if not expand:
            break
        qs = {f"n{i}": idx.question(p.node) for i, p in enumerate(expand)}
        req = Request(state, qs)
        res = (await client.run([req]))[req.hash]
        if "error" in res:
            return {"error": res["error"]}
        ans = answers(res)
        cand: list[Path] = []
        for i, p in enumerate(expand):
            a = ans.get(f"n{i}")
            if a is None:
                continue
            best_child = max((v for k, v in a.dist.items() if k not in ("here", "none")), default=0.0)
            for key, prob in a.dist.items():
                if prob <= 0.01:
                    continue
                if key == "none":
                    continue
                if key == "here":
                    cand.append(Path(p.node, p.logp + math.log(prob), p.steps + 1, p.probs + [(p.node, "here", prob)], done=True))
                    continue
                child = f"{p.node}.{key}" if p.node != "root" else key
                cand.append(Path(child, p.logp + math.log(prob), p.steps + 1, p.probs + [(child, key, prob)]))
            if best_child < MIN_STEP and a.dist.get("here", 0) < MIN_STEP:
                # low-confidence fork: stop at this node rather than guessing deeper
                cand.append(Path(p.node, p.logp + math.log(max(best_child, a.dist.get("here", 0), 0.05)), p.steps + 1,
                                 p.probs + [(p.node, "stop", best_child)], done=True))
        cand.sort(key=lambda c: c.score, reverse=True)
        beam = cand[:BEAM]
        finished += [c for c in beam if c.done]
    finished += [p for p in beam if not p.done]
    if not finished:
        return {"node": start, "confidence": 0.0, "separation": 1.0, "path_probs": []}
    # merge duplicates (same node reached via here/leaf) keep best
    best: dict[str, Path] = {}
    for f in finished:
        if f.node not in best or f.score > best[f.node].score:
            best[f.node] = f
    ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)
    top = ranked[0]
    second = ranked[1].score if len(ranked) > 1 else top.score / 100
    return {
        "node": top.node,
        "confidence": round(top.score, 4),
        "separation": round(min(top.score / max(second, 1e-6), 100.0), 3),  # capped at 100x
        "runner_up": ranked[1].node if len(ranked) > 1 else None,
        "path_probs": top.probs,
    }


async def place_many(qs: list[dict], starts: dict[str, str] | None = None, concurrency: int = 64) -> dict[str, dict]:
    idx = TreeIndex()
    client = JevClient()
    sem = asyncio.Semaphore(concurrency)
    out: dict[str, dict] = {}

    async def one(q):
        async with sem:
            out[q["id"]] = await place_one(client, idx, q, (starts or {}).get(q["id"], "root"))

    try:
        await asyncio.gather(*(one(q) for q in qs))
    finally:
        await client.close()
    return out


def resolve_start(hint: str | None, nodes: dict) -> str:
    if not hint:
        return "root"
    parts = hint.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in nodes:
            return cand
    return "root"


def place_pending(limit: int | None = None, fast: bool | None = None) -> str:
    with db.connect() as conn:
        rows = conn.execute(
            "select id, text, options, state, meta, embedding::text as embedding from questions where node_id is null order by id"
            + (f" limit {int(limit)}" if limit else "")
        ).fetchall()
        nodes = {r["id"] for r in conn.execute("select id from nodes where status='active'")}
    if not rows:
        return "nothing to place"
    starts = {r["id"]: resolve_start((r["meta"] or {}).get("node_hint"), {n: 1 for n in nodes}) for r in rows}
    # beam is more accurate (90.1% vs 84.9% exact on the held-out set); fast only for very large batches
    use_fast = fast if fast is not None else len(rows) > 20000
    res = asyncio.run(place_fast_many(rows, starts) if use_fast else place_many(rows, starts))
    n_ok = 0
    with db.connect() as conn:
        for qid, r in res.items():
            if "error" in r:
                continue
            node = r["node"] if r["node"] in nodes else "root"
            conn.execute(
                "update questions set node_id=%s, path=(select path from nodes where id=%s) where id=%s",
                (node, node, qid),
            )
            conn.execute(
                """insert into placements (question_id, node_id, node_version, method, confidence, separation, path_probs, runner_up)
                   values (%s,%s,(select version from nodes where id=%s),%s,%s,%s,%s,
                           (select path from nodes where id=%s))""",
                (qid, node, node, r.get("method", "jev"), r["confidence"], r["separation"], db.Jsonb(r["path_probs"]), r.get("runner_up")),
            )
            n_ok += 1
        conn.commit()
    return f"placed {n_ok}/{len(rows)}"


# --- fast bulk placement (node-embedding candidates + one Jev Choice) -------------------------------------

FAST_K = 8
FAST_ACCEPT = 0.5


def _node_candidates(conn, vec: str, within: str | None, k: int = FAST_K) -> list[str]:
    if within and within != "root":
        rows = conn.execute(
            "select id from nodes where status='active' and depth >= 2 and path <@ (select path from nodes where id=%s) "
            "order by embedding <=> %s::vector limit %s", (within, vec, k)).fetchall()
    else:
        rows = conn.execute(
            "select id from nodes where status='active' and depth >= 2 order by embedding <=> %s::vector limit %s",
            (vec, k)).fetchall()
    return [r["id"] for r in rows]


async def place_fast_many(qs: list[dict], starts: dict[str, str] | None = None, concurrency: int = 64) -> dict[str, dict]:
    """qs need 'embedding' (pgvector text). One Choice over the K nearest nodes (+ none); beam fallback when unsure."""
    idx = TreeIndex()
    client = JevClient()
    sem = asyncio.Semaphore(concurrency)
    out: dict[str, dict] = {}
    starts = dict(starts or {})

    async def hemisphere(q):
        # step 1: Jev picks the hemisphere (cheap, and where embeddings alone confuse Self/Machine)
        req = Request(question_state(q), {"h": idx.question("root")})
        res = (await client.run([req]))[req.hash]
        a = answers(res).get("h") if "error" not in res else None
        return max(a.dist, key=a.dist.get) if a else "root"

    async def one(q):
        async with sem:
            if starts.get(q["id"], "root") == "root":
                starts[q["id"]] = await hemisphere(q)
            with db.connect() as conn:
                cn = [c for c in _node_candidates(conn, q["embedding"], starts[q["id"]]) if c in idx.nodes]
            if cn:
                crit = {f"n{i}": {"topic_path": " > ".join(idx.nodes[".".join(nid.split(".")[: j + 1])]["label"]
                                                            for j in range(len(nid.split(".")))),
                                  **(idx.nodes[nid]["choice_card"] or {})} for i, nid in enumerate(cn)}
                crit["none"] = {"what": "None of these topic areas fits the question well."}
                gq = gateway_question("choice", {"question": "Which topic area does the question in `question` belong to?"}, crit)
                req = Request(question_state(q), {"fast": gq})
                res = (await client.run([req]))[req.hash]
                a = answers(res).get("fast") if "error" not in res else None
                if a:
                    key = max(a.dist, key=a.dist.get)
                    if key != "none" and a.dist[key] >= FAST_ACCEPT:
                        ranked = sorted(a.dist.values(), reverse=True)
                        node = cn[int(key[1:])]
                        out[q["id"]] = {"node": node, "confidence": a.dist[key],
                                        "separation": round(min(ranked[0] / max(ranked[1], 1e-6), 100.0), 3) if len(ranked) > 1 else 100.0,
                                        "path_probs": [[node, "fast", a.dist[key]]], "method": "jev_fast"}
                        return
            r = await place_one(client, idx, q, starts.get(q["id"], "root"))
            r["method"] = "jev"
            out[q["id"]] = r

    try:
        await asyncio.gather(*(one(q) for q in qs))
    finally:
        await client.close()
    return out
