"""Experiment coverage of the tree: for every branch, how many of its shown questions an experiment actually uses.

Two kinds of experiment use questions. Topic experiments are about something (films, attachment, lost wallets) and
use the questions on it. Cross-cutting ones are about Jev's habits over everything (calibration, option order, repeat
noise, torn vs sure) and take in whole hemispheres, so counting them would make every branch look covered. Coverage
counts topic experiments; "only cross-cutting" is shown separately. The share with a right answer or real human
answers says whether a branch *could* support a comparison, which is what decides whether an experiment is possible.

Called by export.py (the result goes into experiments.json as `coverage`); run alone to print the thinnest branches:
`uv run python scripts/experiments/coverage.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

A = Path("data/analysis")

# Experiments about Jev's behavior across the whole corpus rather than about a topic: their result isn't broken down
# by what the questions are about. (work_which_way_it_errs and work_task_not_domain sweep every work task too, but
# report each task on its own, so they count as covering it.)
CROSS = {
    "consistency_option_order", "consistency_repeat_noise", "consistency_self_vs_people", "consistency_middle_lean",
    "knowledge_calibration", "work_calibration", "self_torn_vs_sure", "self_closed_questions",
}
HEMI = ["self", "world", "machine"]


def pretty(node: str) -> str:
    return node.rsplit(".", 1)[-1].replace("_", " ").capitalize()


def build(shown: pl.DataFrame, rows: dict[str, list[str]], titles: dict[str, str], labels: dict[str, str | None]) -> dict:
    """shown: the shown questions (id, node_id, truth, humans); rows: experiment id -> its question ids."""
    use = pl.DataFrame(
        [(q, e) for e, ids in rows.items() for q in ids], schema=["id", "exp"], orient="row",
    )
    topic = use.filter(~pl.col("exp").is_in(list(CROSS)))
    per_q = topic.group_by("id").agg(pl.col("exp").unique().alias("exps"))
    cross_ids = use.filter(pl.col("exp").is_in(list(CROSS))).select("id").unique().with_columns(cross=pl.lit(True))
    parts = pl.col("node_id").str.split(".")
    q = (shown.select("id", "node_id", "truth", "humans")
         .join(per_q, on="id", how="left").join(cross_ids, on="id", how="left")
         .with_columns(
             hemi=parts.list.get(0),
             l1=pl.when(parts.list.len() >= 2).then(parts.list.slice(0, 2).list.join(".")).otherwise(None),
             l2=pl.when(parts.list.len() >= 3).then(parts.list.slice(0, 3).list.join(".")).otherwise(None),
             topic=pl.col("exps").is_not_null(),
             cross=pl.col("cross").fill_null(False),
             comparable=pl.col("truth").is_not_null() | (pl.col("humans").is_not_null() & (pl.col("humans") != "[]")),
         ))

    size = {e: len(ids) for e, ids in rows.items()}

    def summarize(g: pl.DataFrame) -> dict:
        n = g.height
        # the experiments most about this topic first: the share of an experiment's questions that sit here, so a
        # 50,000-poll sweep that brushes every topic doesn't head every list
        ex = (g.filter(pl.col("topic")).select(pl.col("exps").explode(empty_as_null=True)).group_by("exps").len()
              .with_columns(focus=pl.col("len") / pl.col("exps").replace_strict(size, default=1))
              .filter(pl.col("len") >= 5)
              .sort(["focus", "len", "exps"], descending=[True, True, False]))
        return {
            "n": n,
            "topic": int(g["topic"].sum()),
            "cross_only": int((g["cross"] & ~g["topic"]).sum()),
            "comparable": int(g["comparable"].sum()),
            "n_exps": ex.height,
            "exps": [{"id": e, "title": titles.get(e, e), "n": c, "focus": round(f, 3)} for e, c, f in ex.head(6).iter_rows()],
        }

    out = {"total": summarize(q), "cross": sorted(CROSS), "hemispheres": []}
    for h in HEMI:
        gh = q.filter(pl.col("hemi") == h)
        if gh.is_empty():
            continue
        hemi = {"id": h, "label": labels.get(h) or h.capitalize(), **summarize(gh), "branches": []}
        for (l1,), g1 in gh.filter(pl.col("l1").is_not_null()).group_by("l1"):
            b = {"id": l1, "label": labels.get(l1) or pretty(l1), **summarize(g1), "topics": []}
            for (l2,), g2 in g1.filter(pl.col("l2").is_not_null()).group_by("l2"):
                if g2.height >= 50:  # smaller topics are folded into their branch's totals only
                    b["topics"].append({"id": l2, "label": labels.get(l2) or pretty(l2), **summarize(g2)})
            b["topics"].sort(key=lambda t: -t["n"])
            hemi["branches"].append(b)
        hemi["branches"].sort(key=lambda b: -b["n"])
        out["hemispheres"].append(hemi)
    return out


def main():
    shown = pl.read_parquet(A / "questions.parquet", columns=["id", "node_id", "truth", "humans", "display_ok", "harmful", "jev_dist"])
    shown = shown.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())
    rows = {f.stem: [r[0] for r in json.loads(f.read_text())] for f in (A / "experiment_rows").glob("*.json")}
    cov = build(shown, rows, {}, {})
    t = cov["total"]
    print(f"{t['n']:,} shown; in a topic experiment {t['topic'] / t['n']:.1%}; only cross-cutting {t['cross_only'] / t['n']:.1%}")
    flat = [(tp, b["id"]) for h in cov["hemispheres"] for b in h["branches"] for tp in b["topics"]]
    flat.sort(key=lambda x: x[0]["topic"] / x[0]["n"])
    for tp, _ in flat[:40]:
        print(f"{tp['topic'] / tp['n']:6.1%}  {tp['n']:>6,}  comparable {tp['comparable'] / tp['n']:4.0%}  {tp['id']}")


if __name__ == "__main__":
    main()
