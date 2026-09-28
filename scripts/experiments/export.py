"""Bundle every experiment for the atlas (docs/16 pass 4): data/analysis/experiments.json (private).

One entry per experiment: its spec (the six steps), result, chart data, evaluation, the example questions as rows
(the same shape as the portrait's), how many shown questions each of its sources has, and the tree nodes those
questions sit under (for map links). publish.py uploads the file next to portrait.json.
Run from the repo root: `uv run python scripts/experiments/export.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "portrait"))
from export_page import row  # noqa: E402

A = Path("data/analysis")
OUT = A / "experiments"
FAMILY = {  # display names and order
    "perception": "Reading words and numbers", "names": "Names", "taste": "Taste", "personality": "Personality tests",
    "resemble": "Who Jev resembles", "moral": "Moral judgment", "judgment": "Judgment and bias", "risk": "Risk and forecasting",
    "social": "Reading people", "humor": "Humor", "words": "How words feel", "judge": "Judging text",
    "knowledge": "What it knows", "polls": "Reading the crowd", "work": "Work tasks", "consistency": "Consistency",
    "self": "Defaults",
}


def main():
    exps = []
    for f in sorted(OUT.glob("*.json")):
        if f.name.startswith("_"):
            continue
        exps.append(json.loads(f.read_text()))
    q = pl.read_parquet(A / "questions.parquet")
    shown = q.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())
    ids = {i for e in exps for i in (e["result"].get("examples") or [])[:8]}
    rows = {r["id"]: row(r) for r in shown.filter(pl.col("id").is_in(list(ids))).iter_rows(named=True)}
    srcs = {s for e in exps for s in e["spec"].get("sources") or []}
    counts = dict(shown.filter(pl.col("source").is_in(list(srcs))).group_by("source").len().iter_rows())
    nodes = {}
    for (s,), g in shown.filter(pl.col("source").is_in(list(srcs))).group_by("source"):
        top = g.group_by("node_id").len().sort("len", descending=True).head(4)
        nodes[s] = [{"node": n, "n": c} for n, c in top.iter_rows()]
    labels = {}
    try:
        labels = {n["node_id"]: n.get("label") for n in json.loads((A / "portrait.json").read_text()).get("nodes", [])}
    except FileNotFoundError:
        pass
    out = []
    for e in exps:
        s, r, ev = e["spec"], e["result"], e.get("evaluation") or {}
        out.append({
            "id": s["id"], "family": s["family"], "family_label": FAMILY.get(s["family"], s["family"]), "title": s["title"],
            "question": s["question"], "why": s["why"], "sourcing": s["sourcing"], "collection": s["collection"],
            "scoring": s["scoring"], "chart_desc": s["chart"], "compared_with": s["compared_with"], "limits": s["limits"],
            "new_questions": s.get("new_questions", 0),
            "sources": [{"name": x, "shown": counts.get(x, 0), "nodes": [{**n, "label": labels.get(n["node"])} for n in nodes.get(x, [])]}
                        for x in s.get("sources") or []],
            "result": r["result"], "evidence": r["evidence"], "robustness": r.get("robustness", ""), "n": r.get("n", 0),
            "chart": r["chart"],
            "rows": [rows[i] for i in (r.get("examples") or [])[:8] if i in rows],
            "evaluation": {k: ev.get(k) for k in ("outcome", "strength", "top", "interest", "verdict", "checks", "version")} if ev else None,
        })
    out.sort(key=lambda x: -((x["evaluation"] or {}).get("strength") or -99))
    data = {"experiments": out, "families": FAMILY}
    (A / "experiments.json").write_text(json.dumps(data, separators=(",", ":"), default=str))
    print(f"{len(out)} experiments, {len(rows)} example rows -> {A / 'experiments.json'} "
          f"({(A / 'experiments.json').stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
