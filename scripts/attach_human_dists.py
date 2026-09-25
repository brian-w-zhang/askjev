"""Attach human answer distributions to EXISTING questions from a JSONL file (no new questions).

Each line: {"question_id", "population", "distribution", "n", "source"?, "wave"?, ...} (extra fields are ignored).
Rows whose question_id is not in `questions` are skipped; an existing (question_id, population) row is kept
(on conflict do nothing), so reruns are safe.

    uv run python scripts/attach_human_dists.py data/normalized/ipip_neo_norms_dists.jsonl [--dry-run]
"""

import argparse
import json

from askjev import db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--dry-run", action="store_true", help="count what would be inserted, write nothing")
    a = ap.parse_args()
    rows = [json.loads(ln) for ln in open(a.file, encoding="utf-8") if ln.strip()]
    for r in rows:
        dist = r["distribution"]
        assert r["question_id"] and r["population"] and dist, r
        assert abs(sum(dist.values()) - 1) < 1e-3, (r["question_id"], r["population"], "shares must sum to 1")
    ids = sorted({r["question_id"] for r in rows})
    with db.connect() as conn:
        have = {x["id"] for x in conn.execute("select id from questions where id = any(%s)", (ids,)).fetchall()}
        taken = {(x["question_id"], x["population"]) for x in conn.execute(
            "select question_id, population from human_dists where question_id = any(%s)", (ids,)).fetchall()}
        todo = [r for r in rows if r["question_id"] in have and (r["question_id"], r["population"]) not in taken]
        if not a.dry_run:
            for r in todo:
                conn.execute(
                    """insert into human_dists (question_id, population, n, distribution, source, wave)
                       values (%s,%s,%s,%s,%s,%s) on conflict do nothing""",
                    (r["question_id"], r["population"], r.get("n"), db.Jsonb(r["distribution"]), r.get("source"),
                     r.get("wave")),
                )
            conn.commit()
    print(f"{len(rows)} rows, {len(ids)} questions: {len(have)} exist, {len(todo)} rows "
          f"{'would be ' if a.dry_run else ''}inserted, {len(rows) - len(todo)} skipped (missing question or already set)")


if __name__ == "__main__":
    main()
