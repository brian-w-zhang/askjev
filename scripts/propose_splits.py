"""Split proposals for nodes over the node cap (docs/10-expansion.md §4) that the template split can't fix
(their load isn't one big template). Clusters the node's direct questions with local embeddings and writes
authored/restructure/split__<node>.json for labeling; then `askjev restructure --apply <file>` (Jev re-routes and
the accept rules decide). Group proposals are never written here (no group operations while the UI is in flux).

  uv run python scripts/propose_splits.py [--cap 1500] [--kmax 8]
"""

import argparse

import numpy as np
import orjson

from askjev import db
from askjev.embed import question_text
from askjev.restructure import PROPOSALS, _vec, cluster
from askjev.template_split import MIN_TEMPLATE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=1500)
    ap.add_argument("--kmax", type=int, default=8)
    a = ap.parse_args()
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    with db.connect() as conn:
        nodes = conn.execute(
            "select node_id, count(*) c from questions where display_ok group by 1 having count(*) > %s order by 2 desc", (a.cap,)
        ).fetchall()
        for r in nodes:
            # questions not covered by a big template (those move by template split instead)
            qs = conn.execute(
                """select q.id, q.text, q.options, q.state, q.embedding::text emb from questions q
                   where q.node_id=%s and (q.template_id is null or q.template_id not in (
                     select template_id from questions where node_id=%s and template_id is not null
                     group by 1 having count(*) >= %s))""",
                (r["node_id"], r["node_id"], MIN_TEMPLATE),
            ).fetchall()
            if len(qs) <= a.cap:
                print(f"skip {r['node_id']}: {r['c']} direct, {len(qs)} outside big templates")
                continue
            groups = cluster(np.stack([_vec(q["emb"]) for q in qs]), kmax=a.kmax, min_size=100)
            if not groups:
                print(f"no clean clusters for {r['node_id']} ({len(qs)})")
                continue
            prop = {"type": "split", "node": r["node_id"], "n_questions": len(qs),
                    "clusters": [{"size": len(g), "samples": [question_text(qs[i]["text"], qs[i]["options"], qs[i]["state"])[:300]
                                                              for i in g[:15]],
                                  "child": {"key": "", "label": "", "description": "", "not_for": "", "examples": []}}
                                 for g in groups]}
            (PROPOSALS / f"split__{r['node_id']}.json").write_bytes(orjson.dumps(prop, option=orjson.OPT_INDENT_2))
            print(f"proposal {r['node_id']}: {len(qs)} questions → {[len(g) for g in groups]}")


if __name__ == "__main__":
    main()
