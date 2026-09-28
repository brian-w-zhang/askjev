"""Tree nodes for the experiments' new questions (docs/16 pass 3): each set sits under its subject, one leaf per set.
Idempotent. Run from the repo root: `uv run python scripts/experiments/new_nodes.py`."""

from __future__ import annotations

from askjev import db
from askjev.embed import embed, to_pg

NODES = [
    ("world.society.languages.word.probability_words", "Probability and Amount Words",
     "Questions about what words like likely, probably, a few or several mean as numbers."),
    ("world.society.languages.word.adjective_intensity", "Adjective Intensity",
     "Questions about which of two related adjectives is stronger, like good versus great."),
    ("world.society.languages.word.word_humor", "Funny Words",
     "Questions about how funny single English words are on their own."),
    ("world.society.languages.sentence_inference", "What Sentences Imply",
     "Questions about whether one sentence follows from, contradicts, or leaves open another."),
    ("world.money.careers.work_context", "What Jobs Are Like",
     "Questions about the daily conditions of specific occupations: angry customers, weather, deadlines, sitting."),
]

if __name__ == "__main__":
    with db.connect() as conn:
        have = {r["id"]: r for r in conn.execute("select id, depth from nodes")}
        new = [n for n in NODES if n[0] not in have]
        vecs = embed([f"{label}: {desc}" for _, label, desc in new]) if new else []
        for (nid, label, desc), v in zip(new, vecs):
            parent = nid.rsplit(".", 1)[0]
            not_for = "General questions about the parent topic stay at the parent."
            conn.execute(
                """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, not_for, examples, source,
                     locked, ord, choice_card, embedding)
                   values (%s,%s,(select path from nodes where id=%s) || %s::ltree,%s,%s,%s,%s,%s,'{}','experiments',false,900,%s,%s)
                   on conflict (id) do nothing""",
                (nid, parent, parent, nid.rsplit(".", 1)[-1], have[parent]["depth"] + 1, nid.split(".")[0], label, desc,
                 not_for, db.Jsonb({"label": label, "what": desc, "not_for": not_for}), to_pg(v)))
        conn.commit()
    print(f"added {len(new)} nodes: {[n[0] for n in new]}")
