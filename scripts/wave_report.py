"""Wave gate numbers (docs/10-expansion.md §3-§4): per-source stats for questions created since a time, plus
the corpus-wide template cap and node cap checks. Read-only on Postgres; prints markdown.

  uv run python scripts/wave_report.py --since 2026-09-24T21:00 [--until 2026-09-25T09:00]
"""

import argparse

from askjev import db

TEMPLATE_CAP, MACHINE_TEMPLATE_CAP, NODE_CAP = 5000, 3000, 1500


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", default="infinity")
    a = ap.parse_args()
    with db.connect() as c:
        rows = c.execute(
            """select q.source, q.hemisphere, count(*) n,
                 count(*) filter (where exists (select 1 from probes p join answers x on x.probe_id=p.id where p.question_id=q.id)) answered,
                 count(*) filter (where q.truth is not null or exists (select 1 from human_dists h where h.question_id=q.id)) anchored,
                 avg(m.correct::int) acc, avg((m.p_top > 0.95)::int) decisive, avg(m.p_top) ptop,
                 count(*) filter (where not q.display_ok) hidden, count(distinct q.text) texts
               from questions q left join question_meta m on m.question_id=q.id
               where q.created_at >= %s and q.created_at < %s group by 1,2 order by 3 desc""",
            (a.since, a.until),
        ).fetchall()
        tot = sum(r["n"] for r in rows)
        anch = sum(r["anchored"] for r in rows)
        syn = c.execute("select count(*) c from questions where created_at >= %s and created_at < %s and origin='synthetic'", (a.since, a.until)).fetchone()["c"]
        hem = c.execute("select hemisphere, count(*) c from questions where created_at >= %s and created_at < %s group by 1", (a.since, a.until)).fetchall()
        print(f"## Added since {a.since}: {tot:,} questions\n")
        print(f"- anchored (truth or human data): {anch:,} ({anch / max(tot, 1):.0%}); synthetic: {syn:,} ({syn / max(tot, 1):.0%})")
        print("- by hemisphere: " + ", ".join(f"{r['hemisphere']} {r['c']:,}" for r in hem) + "\n")
        print("| source | hemi | n | answered | anchored | texts | correct | decisive | mean p_top | hidden | saturated |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            f = lambda v: "" if v is None else f"{v:.2f}"
            sat = r["acc"] is not None and r["acc"] >= 0.95 and (r["decisive"] or 0) >= 0.60
            print(f"| {r['source']} | {r['hemisphere']} | {r['n']:,} | {r['answered']:,} | {r['anchored']:,} | {r['texts']:,} | "
                  f"{f(r['acc'])} | {f(r['decisive'])} | {f(r['ptop'])} | {r['hidden']:,} | {'yes' if sat else ''} |")
        over = c.execute(
            """select coalesce(template_id, text) text, hemisphere, count(*) c from questions group by 1,2
               having count(*) > case when hemisphere='machine' then %s else %s end order by 3 desc""",
            (MACHINE_TEMPLATE_CAP, TEMPLATE_CAP),
        ).fetchall()
        print("\n### Templates (template_id, else text) over the cap (frozen: no new rows)")
        for r in over:
            print(f"- {r['c']:,} × [{r['hemisphere']}] {r['text'][:90]}")
        full = c.execute(
            """select node_id, count(*) c from questions where display_ok group by 1 having count(*) > %s order by 2 desc""",
            (NODE_CAP,),
        ).fetchall()
        print(f"\n### Nodes over {NODE_CAP:,} direct displayable questions (split candidates)")
        for r in full:
            print(f"- {r['node_id']}: {r['c']:,}")


if __name__ == "__main__":
    main()
