"""Recompute question embeddings as text + options + input excerpt (askjev.embed.question_text)."""
from askjev import db
from askjev.embed import embed, question_text, to_pg

with db.connect() as conn:
    rows = conn.execute("select id, text, options, state from questions").fetchall()
    for i in range(0, len(rows), 1000):
        chunk = rows[i:i + 1000]
        vecs = embed([question_text(r["text"], r["options"], r["state"]) for r in chunk])
        for r, v in zip(chunk, vecs):
            conn.execute("update questions set embedding=%s::vector where id=%s", (to_pg(v), r["id"]))
        conn.commit()
    print("re-embedded", len(rows))
