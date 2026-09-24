"""Mix report: canonical-question counts vs targets (docs/03-questions.md §2, docs/02-tree.md §3)."""

from __future__ import annotations

from . import db

KIND_TARGETS = {  # % of all canonical questions
    "personality": 9, "values": 10, "taste": 15, "evaluative": 9, "social": 8,
    "factual": 15, "forecast": 1, "perception": 3,
}
HEMI_TARGETS = {"world": 35, "self": 35, "machine": 30}


def _pct(n, total):
    return 100.0 * n / total if total else 0.0


def mix_report(markdown: bool = False) -> str:
    with db.connect() as conn:
        total = conn.execute("select count(*) c from questions").fetchone()["c"]
        hemi = {r["hemisphere"]: r["c"] for r in conn.execute("select hemisphere, count(*) c from questions group by 1")}
        kinds = {r["k"]: r["c"] for r in conn.execute(
            "select coalesce(kind, 'machine:'||shape) k, count(*) c from questions group by 1")}
        l1 = conn.execute(
            """select n.id, n.label, n.share, count(q.id) c from nodes n
               left join questions q on q.path <@ n.path where n.depth = 2 and n.status='active'
               group by n.id, n.label, n.share order by n.id"""
        ).fetchall()
        src = conn.execute(
            """select source, count(*) c, count(*) filter (where truth is not null and truth != 'null'::jsonb) t,
                      count(*) filter (where exists (select 1 from human_dists h where h.question_id=q.id)) h
               from questions q group by 1 order by 2 desc"""
        ).fetchall()
        placed = conn.execute("select count(*) c from questions where node_id is not null").fetchone()["c"]
        answered = conn.execute("select count(*) c from question_meta where top is not null").fetchone()["c"]
        hidden = conn.execute("select count(*) c from questions where not display_ok").fetchone()["c"]
    L = []
    L.append(f"TOTAL canonical questions: {total}  placed: {placed}  answered: {answered}  hidden (flagged): {hidden}")
    L.append("\nHEMISPHERE        actual   target")
    for h, t in HEMI_TARGETS.items():
        L.append(f"  {h:14s} {_pct(hemi.get(h, 0), total):6.1f}%  {t:5.1f}%   ({hemi.get(h, 0)})")
    L.append("\nKIND (world/self)  actual   target")
    for k, t in KIND_TARGETS.items():
        L.append(f"  {k:14s} {_pct(kinds.get(k, 0), total):6.1f}%  {t:5.1f}%   ({kinds.get(k, 0)})")
    mach = {k: v for k, v in kinds.items() if k and k.startswith("machine:")}
    L.append("  machine shapes: " + ", ".join(f"{k[8:]}={v}" for k, v in sorted(mach.items())))
    L.append("\nL1 ROOT               actual   target")
    for r in l1:
        L.append(f"  {r['id']:22s} {_pct(r['c'], total):6.1f}%  {r['share'] or 0:5.1f}%   ({r['c']})")
    L.append("\nSOURCE                 n    truth  human")
    for r in src:
        L.append(f"  {r['source']:20s} {r['c']:6d} {r['t']:6d} {r['h']:6d}")
    out = "\n".join(L)
    if markdown:
        return "```\n" + out + "\n```"
    return out
