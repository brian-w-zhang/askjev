"""Bulk near-duplicate detection (docs/02-tree.md §8, layer 1).

Candidate pairs: same node, local-embedding cosine >= 0.90, excluding machine instances of one template and
same-dataset pairs (adapters dedupe within a source; instrument items are intentionally similar).
Decision: one Jev Noul per pair ("same question?"), >= 0.7. The duplicate (preferring to keep dataset items over
synthetic/template ones) is linked to its canonical question, flagged `duplicate`, hidden, and bumps ask_count.
Nothing is deleted.
"""

from __future__ import annotations

import asyncio

from . import db
from .jev import JevClient, Request, answers, gateway_question
from .place import question_state

SIM = 0.90


def same_question(candidate) -> dict:
    """The shared "same question?" Noul (contrastive criteria), used by bulk dedupe, the ask flow, and the eval."""
    # A contrastive true/false version was tried and measured worse on labeled Quora pairs (F1 0.54 vs 0.66).
    return gateway_question(
        "noul",
        {"question": "Is `candidate` asking essentially the same question as `question` (same meaning and same answer options)?",
         "candidate": candidate},
    )
DUP_P = 0.7
ORIGIN_RANK = {"dataset": 0, "typesafe-docs": 0, "wikidata-fact": 1, "template": 2, "synthetic": 3, "asked": 4}


def candidate_pairs() -> list[dict]:
    with db.connect() as conn:
        return conn.execute(
            """select a.id a_id, b.id b_id, a.text a_text, b.text b_text, a.options a_opt, b.options b_opt,
                      a.origin a_origin, b.origin b_origin, 1 - (a.embedding <=> b.embedding) sim
               from questions a join lateral (
                   select id, text, options, origin, source, embedding from questions b
                   where b.node_id = a.node_id and b.id > a.id and b.template_id is not distinct from null
                     and not ('duplicate' = any(b.flags))
                     -- items from one dataset are already deduped by its adapter; instrument items are
                     -- intentionally similar (facets, reverse-keyed), so only cross-source pairs are checked
                     and not (b.source = a.source and a.origin in ('dataset', 'wikidata-fact', 'template'))
                   order by b.embedding <=> a.embedding limit 3) b on true
               where a.template_id is null and not ('duplicate' = any(a.flags))
                 and 1 - (a.embedding <=> b.embedding) >= %s""",
            (SIM,),
        ).fetchall()


async def _judge(pairs):
    c = JevClient()
    reqs = []
    for p in pairs:
        reqs.append(Request(question_state({"text": p["a_text"], "options": p["a_opt"]}),
                            {"d": same_question(question_state({"text": p["b_text"], "options": p["b_opt"]}))}))
    res = await c.run(reqs)
    await c.close()
    return [answers(res[r.hash]).get("d") for r in reqs]


def dedupe() -> str:
    pairs = candidate_pairs()
    if not pairs:
        return "no candidate pairs"
    verdicts = asyncio.run(_judge(pairs))
    n = 0
    with db.connect() as conn:
        for p, a in zip(pairs, verdicts):
            if not a or a.p_yes < DUP_P:
                continue
            ra, rb = ORIGIN_RANK.get(p["a_origin"], 5), ORIGIN_RANK.get(p["b_origin"], 5)
            keep, dup = (p["a_id"], p["b_id"]) if ra <= rb else (p["b_id"], p["a_id"])
            conn.execute(
                "insert into question_links (from_id, to_id, type, condition) values (%s,%s,'duplicate',%s) on conflict do nothing",
                (dup, keep, db.Jsonb({"p_same": a.p_yes, "sim": float(p["sim"])})),
            )
            conn.execute("update questions set flags = array_append(flags, 'duplicate'), display_ok=false where id=%s and not ('duplicate' = any(flags))", (dup,))
            conn.execute("update questions set ask_count = ask_count + 1 where id=%s", (keep,))
            n += 1
        conn.commit()
    return f"checked {len(pairs)} candidate pairs; linked {n} duplicates"
