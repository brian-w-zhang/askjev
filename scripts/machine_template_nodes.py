"""Machine hemisphere: each high-volume template (≥ 100 instances) becomes a topic node under its use-case L2,
and its instances move into it (docs/02-tree.md §2: Machine nodes hold templates, items are template × input)."""
from askjev import db
from askjev.embed import embed, to_pg

LABELS = {
    "unfair_tos.unfair": "Unfair clause?", "unfair_tos.clause_type": "Unfair clause type",
    "msmarco.answers_query": "Passage answers query?", "msmarco.relevance_level": "Passage relevance level",
    "amazon.satisfaction": "Reviewer satisfaction", "amazon.topic": "Review topic",
    "sms.spam": "Is it spam?", "sms.call_to_action": "Call to action?",
    "fpb.investor_sentiment": "Investor sentiment", "emotion.primary": "Primary emotion",
    "banking77.intent": "Banking intent", "banking77.urgency": "Customer urgency",
    "banking77.money_left": "Money already left?", "code.language": "Programming language",
    "guardrail.jailbreak": "Jailbreak attempt?", "er.same_product": "Same product?",
    "er.same_paper": "Same paper?", "people.occupation_group": "Occupation group",
    "scifact.claim_support": "Claim support", "people.same_person": "Same person?",
}
with db.connect() as conn:
    rows = conn.execute("""select template_id, node_id, count(*) n, min(text) text from questions
                           where hemisphere='machine' and template_id is not null group by 1,2 having count(*) >= 100""").fetchall()
    vecs = embed([f"{LABELS.get(r['template_id'], r['template_id'])}: {r['text']}" for r in rows])
    made = moved = 0
    for i, (r, v) in enumerate(zip(rows, vecs)):
        key = "t_" + r["template_id"].replace(".", "_")
        nid = f"{r['node_id']}.{key}"
        label = LABELS.get(r["template_id"], r["template_id"])
        desc = f"Template run over many real inputs: \"{r['text']}\""
        card = {"label": label, "what": desc}
        cur = conn.execute(
            """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, examples, source, locked, ord,
                 choice_card, embedding)
               values (%s,%s,(select path from nodes where id=%s) || %s::ltree,(select depth+1 from nodes where id=%s),
                       'machine',%s,%s,%s,'template',false,%s,%s,%s) on conflict (id) do nothing""",
            (nid, r["node_id"], r["node_id"], key, r["node_id"], label, desc, [r["text"]], 500 + i, db.Jsonb(card), to_pg(v)))
        made += cur.rowcount
        c2 = conn.execute("""update questions set node_id=%s, path=(select path from nodes where id=%s)
                             where template_id=%s and node_id=%s returning id""", (nid, nid, r["template_id"], r["node_id"]))
        ids = [x["id"] for x in c2.fetchall()]
        moved += len(ids)
        if ids:
            conn.execute("""insert into placements (question_id, node_id, node_version, method, confidence)
                            select unnest(%s::text[]), %s, 1, 'template', 1.0""", (ids, nid))
    conn.commit()
print(f"template nodes created: {made}; instances moved: {moved}")
