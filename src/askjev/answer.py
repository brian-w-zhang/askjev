"""Screen request + answer bundle (docs/03-questions.md §8).

Screen (every candidate): content-filter Nouls, weak-spot Noul, and Jev's self-assessment of the
question (objective / disagreement / ambiguous / reveals_self). The judged question is a data
field inside `instructions`, so screens for many questions share one neutral state and batch together.

Answer bundle (sampled questions): self frame + human frame (World/Self) + 3 option shuffles (Choice)
or a reversed-level probe (Score). Stateless questions share a neutral state and batch together;
Machine questions batch per identical input.
"""

from __future__ import annotations

import asyncio
import random
from collections import defaultdict

from . import db
from .jev import JevClient, Request, answers, gateway_question, pack, sha

NEUTRAL_STATE = {"context": "Independent standalone questions. Answer each one on its own."}

DISAGREEMENT_LEVELS = [
    "Essentially everyone would give the same answer",
    "Most people would agree, with a few exceptions",
    "People would be noticeably split, but one answer would clearly be more common",
    "People would split roughly evenly between the answers",
]


def subject(q: dict) -> str:
    s = q["text"]
    o = q.get("options")
    if isinstance(o, dict):
        s += " Options: " + "; ".join(f"{k}" + (f" ({v})" if v else "") for k, v in list(o.items())[:20])
    elif isinstance(o, list):
        s += " Scale: " + " | ".join(o)
    return s


def screen_questions(q: dict) -> dict[str, dict]:
    subj = subject(q)
    human_side = q["hemisphere"] != "machine"

    def noul(question):
        return gateway_question("noul", {"question": question, "subject": subj})

    out = {
        "f_political": noul("Is the question in `subject` about a contested political or partisan issue "
                            "(elections, parties, politicians, abortion, guns, immigration, or similar)?"),
        "f_sensitive": noul("Does the question in `subject` involve sexual content, self-harm, or graphic violence?"),
        "f_weak": noul("Does answering the question in `subject` require arithmetic, counting, exact numbers, or comparing dates?"),
        "m_objective": noul("Does the question in `subject` have a single correct answer that could be checked against facts?"),
        "m_ambiguous": noul("Is the question in `subject` ambiguous or underspecified, so that different readers could understand it differently?"),
    }
    if human_side:
        out["m_reveals_self"] = noul("Would someone's answer to the question in `subject` reveal something about their personality or values?")
        out["m_disagreement"] = gateway_question(
            "score", {"question": "How much would thoughtful people disagree about the answer to the question in `subject`?", "subject": subj},
            DISAGREEMENT_LEVELS,
        )
    return out


def human_instructions(q: dict):
    ht = (q.get("meta") or {}).get("human_text")
    if ht:
        return ht
    return {
        "question": q["text"],
        "perspective": "Do not give your own view. Choose the answer that most people would give (the most common human answer).",
    }


def answer_probes(q: dict) -> list[dict]:
    """Returns probe dicts: {id, frame, variant_kind, params, gw, perm}."""
    probes = []
    o = q.get("options")
    prim = q["primitive"]
    crit = o if prim in ("choice", "score") else (o or None)

    def add(frame, variant, params, instructions, criteria, perm=None):
        gw = gateway_question(prim, instructions, criteria)
        pid = sha({"q": q["id"], "u": "base", "f": frame, "v": variant, "p": params})[:20]
        probes.append({"id": pid, "frame": frame, "variant_kind": variant, "params": params, "gw": gw, "perm": perm})

    add("self" if q["hemisphere"] != "machine" else "none", "base", {}, q["text"], crit)
    if q["hemisphere"] != "machine":
        add("human", "base", {}, human_instructions(q), crit)
    if prim == "choice" and isinstance(o, dict) and len(o) >= 2:
        keys = list(o.keys())
        rng = random.Random(q["id"])
        seen = {tuple(keys)}
        for i in range(3):
            perm = keys[:]
            for _ in range(10):
                rng.shuffle(perm)
                if tuple(perm) not in seen or len(keys) == 2:
                    break
            seen.add(tuple(perm))
            if len(keys) == 2:
                perm = keys[::-1] if i % 2 == 0 else keys[:]
            add("self" if q["hemisphere"] != "machine" else "none", "shuffle", {"i": i, "order": perm},
                q["text"], {k: o[k] for k in perm}, perm)
    elif prim == "score" and isinstance(o, list):
        add("self" if q["hemisphere"] != "machine" else "none", "reversed_levels", {}, q["text"], o[::-1], list(range(len(o)))[::-1])
    return probes


def state_of(q: dict):
    return q["state"] if q.get("state") else NEUTRAL_STATE


def _load(sql: str, params=()) -> list[dict]:
    with db.connect() as conn:
        return conn.execute(sql, params).fetchall()


async def _run(reqs: list[Request]) -> dict[str, dict]:
    c = JevClient()
    try:
        return await c.run(reqs)
    finally:
        await c.close()


def _group_requests(items: list[tuple[str, object, dict]]) -> list[Request]:
    """items: (key, state, gateway_question) → pack by identical state."""
    by_state: dict[str, tuple[object, dict]] = {}
    for key, state, gw in items:
        sk = sha(state)
        if sk not in by_state:
            by_state[sk] = (state, {})
        by_state[sk][1][key] = gw
    reqs = []
    for state, qs in by_state.values():
        reqs += pack(state, qs)
    return reqs


def screen_pending(limit: int | None = None, ids: list[str] | None = None) -> str:
    rows = _load(
        "select q.id, q.text, q.options, q.state, q.hemisphere from questions q "
        "left join question_meta m on m.question_id=q.id where m.objective is null "
        + ("and q.id = any(%s) " if ids else "") + "order by q.id"
        + (f" limit {int(limit)}" if limit else ""),
        (ids,) if ids else (),
    )
    if not rows:
        return "nothing to screen"
    items = []
    for q in rows:
        for k, gw in screen_questions(q).items():
            items.append((f"{q['id']}__{k}", NEUTRAL_STATE, gw))
    reqs = _group_requests(items)
    res = asyncio.run(_run(reqs))
    per_q: dict[str, dict] = defaultdict(dict)
    served = None
    for r in reqs:
        resp = res.get(r.hash, {})
        if "error" in resp:
            continue
        served = served or resp.get("model")
        for key, a in answers(resp).items():
            qid, name = key.split("__", 1)
            per_q[qid][name] = a
    with db.connect() as conn:
        for qid, a in per_q.items():
            flags = []
            if a.get("f_political") and a["f_political"].p_yes >= 0.5:
                flags.append("political")
            if a.get("f_sensitive") and a["f_sensitive"].p_yes >= 0.5:
                flags.append("sensitive")
            if a.get("f_weak") and a["f_weak"].p_yes >= 0.5:
                flags.append("weak_spot")
            dis = a.get("m_disagreement")
            conn.execute(
                """insert into question_meta (question_id, objective, ambiguous, reveals_self, disagreement, updated_at)
                   values (%s,%s,%s,%s,%s,now())
                   on conflict (question_id) do update set objective=excluded.objective, ambiguous=excluded.ambiguous,
                     reveals_self=excluded.reveals_self, disagreement=excluded.disagreement, updated_at=now()""",
                (
                    qid,
                    a["m_objective"].p_yes if "m_objective" in a else None,
                    a["m_ambiguous"].p_yes if "m_ambiguous" in a else None,
                    a["m_reveals_self"].p_yes if "m_reveals_self" in a else None,
                    (dis.score / (len(DISAGREEMENT_LEVELS) - 1)) if dis and dis.score is not None else None,
                ),
            )
            if flags:
                conn.execute(
                    """update questions set flags = (select array(select distinct unnest(flags || %s::text[]))),
                       display_ok = display_ok and not (%s::text[] && array['political','sensitive'])
                       where id=%s""",
                    (flags, flags, qid),
                )
        conn.commit()
    return f"screened {len(per_q)}/{len(rows)} questions in {len(reqs)} requests"


def answer_pending(limit: int | None = None, ids: list[str] | None = None) -> str:
    rows = _load(
        "select q.id, q.text, q.options, q.state, q.hemisphere, q.primitive, q.meta from questions q "
        "where not exists (select 1 from probes p join answers a on a.probe_id=p.id where p.question_id=q.id) "
        + ("and q.id = any(%s) " if ids else "")
        + "order by q.id" + (f" limit {int(limit)}" if limit else ""),
        (ids,) if ids else (),
    )
    if not rows:
        return "nothing to answer"
    items, probe_rows = [], []
    for q in rows:
        st = state_of(q)
        for p in answer_probes(q):
            items.append((p["id"], st, p["gw"]))
            probe_rows.append((q["id"], p))
    reqs = _group_requests(items)
    res = asyncio.run(_run(reqs))
    key_to_req = {}
    for r in reqs:
        for k in r.questions:
            key_to_req[k] = r
    n = 0
    with db.connect() as conn:
        for qid, p in probe_rows:
            conn.execute(
                """insert into probes (id, question_id, universe_id, frame, variant_kind, variant_params)
                   values (%s,%s,'base',%s,%s,%s) on conflict do nothing""",
                (p["id"], qid, p["frame"], p["variant_kind"], db.Jsonb(p["params"])),
            )
            r = key_to_req[p["id"]]
            resp = res.get(r.hash, {})
            if "error" in resp or p["id"] not in (resp.get("answers") or {}):
                continue
            a = answers({"answers": {p["id"]: resp["answers"][p["id"]]}})[p["id"]]
            dist = a.dist
            if p["variant_kind"] == "reversed_levels" and p["perm"]:
                # map reversed level indices back to original indices
                k_levels = len(p["perm"])
                dist = {str(k_levels - 1 - int(k)): v for k, v in a.dist.items()}
            conn.execute(
                """insert into answers (probe_id, request_hash, model_served, distribution, confidence, score_scalar, option_order)
                   values (%s,%s,%s,%s,%s,%s,%s) on conflict do nothing""",
                (p["id"], r.hash, f"{resp.get('model')}", db.Jsonb(dist), a.confidence, a.score, db.Jsonb(p["perm"])),
            )
            n += 1
        conn.commit()
    return f"answered {n} probes for {len(rows)} questions in {len(reqs)} requests"
