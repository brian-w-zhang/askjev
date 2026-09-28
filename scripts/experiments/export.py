"""Bundle every experiment for the atlas (docs/16 pass 4): data/analysis/experiments.json (private).

One entry per experiment: its spec (the six steps), result, chart data, evaluation, the example questions as rows
(the same shape as the portrait's), how many shown questions each of its sources has, and the tree nodes those
questions sit under (for map links). publish.py uploads the file next to portrait.json.
Run from the repo root: `uv run python scripts/experiments/export.py`.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "portrait"))
from export_page import row  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cases  # noqa: E402
import memes  # noqa: E402

A = Path("data/analysis")
OUT = A / "experiments"
FAMILY = {  # display names and order
    "perception": "Reading words and numbers", "names": "Names", "taste": "Taste", "personality": "Personality tests",
    "resemble": "Who Jev resembles", "moral": "Moral judgment", "judgment": "Judgment and bias", "risk": "Risk and forecasting",
    "social": "Reading people", "humor": "Humor", "words": "How words feel", "judge": "Judging text",
    "knowledge": "What it knows", "polls": "Reading the crowd", "work": "Work tasks", "consistency": "Consistency",
    "self": "Defaults",
}


def row_order(e: dict, shown: pl.DataFrame) -> list[list]:
    """Every question the experiment used, most telling first: the script's examples, then the rows where Jev misses
    (wrong on a right answer, or a different top answer from real people), biggest gap first, then the rest.
    Each entry is [question id, flag], flag "wrong" | "differs" | ""."""
    f = OUT / "_rows" / f"{e['spec']['id']}.json"
    ids = json.loads(f.read_text()) if f.exists() else []
    if not ids:
        return []
    t = shown.filter(pl.col("id").is_in(ids)).select("id", "jev_dist", "people_dist", "humans", "truth")
    rows = []
    for r in t.iter_rows(named=True):
        j = json.loads(r["jev_dist"]) if r["jev_dist"] else {}
        top = max(j, key=j.get) if j else None
        flag, gap = "", 0.0
        truth = json.loads(r["truth"]) if r["truth"] else None
        hs = json.loads(r["humans"]) if r["humans"] else []
        h = max(hs, key=lambda x: x.get("n") or 0)["dist"] if hs else None
        if truth is not None and top is not None:
            key = "true" if truth is True else "false" if truth is False else str(truth)
            gap = 1 - float(j.get(key, 0))
            flag = "wrong" if top != key else ""
        elif h and top is not None:
            tot = sum(h.values()) or 1
            gap = 0.5 * sum(abs(j.get(k, 0) - h.get(k, 0) / tot) for k in set(j) | set(h))
            flag = "differs" if top != max(h, key=h.get) else ""
        rows.append((r["id"], flag, gap))
    ex = {i: n for n, i in enumerate(e["result"].get("examples") or [])}
    rows.sort(key=lambda x: (x[0] not in ex, ex.get(x[0], 0), x[1] == "", -x[2], x[0]))
    return [[i, fl] for i, fl, _ in rows]


def main():
    exps = []
    for f in sorted(OUT.glob("*.json")):
        if f.name.startswith("_"):
            continue
        exps.append(json.loads(f.read_text()))
    q = pl.read_parquet(A / "questions.parquet")
    shown = q.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())
    ids = {i for e in exps for i in (e["result"].get("examples") or [])[:8]}
    rows = {}
    for r in shown.filter(pl.col("id").is_in(list(ids))).iter_rows(named=True):
        x = row(r)
        opts = json.loads(r["options"]) if r["options"] else {}
        if isinstance(opts, dict) and any(opts.values()):  # show "50%" rather than the key "p050"
            x["labels"] = {k: v for k, v in opts.items() if v}
        rows[r["id"]] = x
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
        # the case study (docs/17): the site shows every section; the public doc shows the method part
        c = cases.load(s["id"])
        if c:
            out[-1]["result"] = (c.get("result") or r["result"]).strip()
            out[-1]["case"] = {"sections": c["sections"], "chart_note": c.get("chart_note") or "",
                               "caveats": c.get("caveats") or [], "facts": c.get("facts") or []}
            mm = memes.resolve(c["meme"]) if c.get("meme") else None
            if mm:
                out[-1]["meme"] = mm
        take = OUT / "_take" / f"{s['id']}.json"
        if take.exists():
            out[-1]["take"] = json.loads(take.read_text())
    # every question behind each result, for the paged rows (served privately next to experiments.json)
    RD = A / "experiment_rows"
    RD.mkdir(exist_ok=True)
    for e in exps:
        order = row_order(e, shown)
        (RD / f"{e['spec']['id']}.json").write_text(json.dumps(order, separators=(",", ":")))
        x = next(o for o in out if o["id"] == e["spec"]["id"])
        x["n_rows"] = len(order)
        # where these questions live: the experiment's own questions by topic, with the topic's parent for a mini tree
        ids = [i for i, _ in order]
        if ids:
            bynode = shown.filter(pl.col("id").is_in(ids)).group_by("node_id").len().sort("len", descending=True)
            x["topics"] = [{"node": nd, "n": c, "label": labels.get(nd) or nd.rsplit(".", 1)[-1].replace("_", " ").capitalize(),
                            "parent": nd.rsplit(".", 1)[0], "parent_label": labels.get(nd.rsplit(".", 1)[0])
                            or nd.rsplit(".", 2)[-2].replace("_", " ").capitalize()}
                           for nd, c in bynode.head(16).iter_rows()]
            x["n_topics"] = bynode.height
        x["n_flagged"] = {k: sum(1 for _, fl in order if fl == k) for k in ("wrong", "differs")}
    out.sort(key=lambda x: -((x["evaluation"] or {}).get("strength") or -99))
    # portrait candidates: Jev's order among kept experiments, at most two per family, so the reel isn't one topic
    per: Counter = Counter()
    cands = []
    for x in out:
        if (x["evaluation"] or {}).get("outcome") == "keep" and per[x["family"]] < 2:
            per[x["family"]] += 1
            cands.append(x["id"])
    for x in out:
        x["portrait_rank"] = cands.index(x["id"]) + 1 if x["id"] in cands[:30] else None
    (OUT / "_portrait_candidates.json").write_text(json.dumps(
        [{"rank": i + 1, "id": c, **{k: next(x for x in out if x["id"] == c)[k] for k in ("family", "title", "result")}}
         for i, c in enumerate(cands[:30])], indent=1))
    data = {"experiments": out, "families": FAMILY}
    (A / "experiments.json").write_text(json.dumps(data, separators=(",", ":"), default=str))
    print(f"{len(out)} experiments, {len(rows)} example rows -> {A / 'experiments.json'} "
          f"({(A / 'experiments.json').stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
