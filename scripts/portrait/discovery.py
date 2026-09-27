"""Portrait step 3 (docs/11-portrait.md): an indicator card for every node and every source, ranked by how far each
metric sits from the corpus baseline (z-scores with a minimum n), to surface candidate findings across all
categories. Pure Polars over data/analysis/questions.parquet; shown rows only (display_ok and not harmful).

Card metrics (where defined):
  n, accuracy (truth rows), mean confidence (p_top on truth rows), ECE (10 bins), confident-miss share
  (p_top >= 0.9 and wrong), decisive share (p_top >= 0.95), stability (same top under shuffles / reversed levels),
  frame gap (TVD self vs "most people" frame), crowd agreement (Jev top == human top), crowd TVD.

  uv run python scripts/portrait/discovery.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

T = Path("data/analysis/questions.parquet")
OUT = Path("data/analysis")
MIN_N = 150


def human_top_and_tvd(jev_json: str | None, humans_json: str | None):
    if not jev_json or not humans_json:
        return None, None
    hs = json.loads(humans_json)
    if not hs:
        return None, None
    h = max(hs, key=lambda x: x.get("n") or 0)["dist"]
    j = json.loads(jev_json)
    keys = set(h) | set(j)
    ht, jt = sum(h.values()) or 1, sum(j.values()) or 1
    tvd = 0.5 * sum(abs(h.get(k, 0) / ht - j.get(k, 0) / jt) for k in keys)
    return max(h, key=h.get), tvd


def load() -> pl.DataFrame:
    q = pl.read_parquet(T, columns=["id", "node_id", "l1", "l2", "hemisphere", "kind", "primitive", "source", "text",
                                    "top", "p_top", "correct", "stability", "frame_gap", "jev_dist", "humans",
                                    "display_ok", "harmful"])
    q = q.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())
    ht = [human_top_and_tvd(j, h) for j, h in zip(q["jev_dist"], q["humans"])]
    return q.with_columns(pl.Series("human_top", [a for a, _ in ht], dtype=pl.Utf8),
                          pl.Series("crowd_tvd", [b for _, b in ht], dtype=pl.Float64)).with_columns(
        (pl.col("top") == pl.col("human_top")).alias("crowd_agree"),
        (pl.col("p_top") >= 0.95).alias("decisive"),
        ((pl.col("p_top") >= 0.9) & (pl.col("correct") == False)).alias("confident_miss"),  # noqa: E712
    ).drop("jev_dist", "humans")


def ece(p: np.ndarray, c: np.ndarray) -> float | None:
    if len(p) < 30:
        return None
    bins = np.clip((p * 10).astype(int), 0, 9)
    return float(sum(abs(p[bins == b].mean() - c[bins == b].mean()) * (bins == b).sum() for b in range(10) if (bins == b).any()) / len(p))


def cards(q: pl.DataFrame, by: str) -> pl.DataFrame:
    g = q.group_by(by).agg(
        n=pl.len(),
        n_truth=pl.col("correct").is_not_null().sum(),
        accuracy=pl.col("correct").cast(pl.Float64).mean(),
        confidence=pl.col("p_top").filter(pl.col("correct").is_not_null()).mean(),
        confident_miss=pl.col("confident_miss").cast(pl.Float64).filter(pl.col("correct").is_not_null()).mean(),
        decisive=pl.col("decisive").cast(pl.Float64).mean(),
        stability=pl.col("stability").mean(),
        frame_gap=pl.col("frame_gap").mean(),
        n_crowd=pl.col("crowd_agree").is_not_null().sum(),
        crowd_agree=pl.col("crowd_agree").cast(pl.Float64).mean(),
        crowd_tvd=pl.col("crowd_tvd").mean(),
    )
    eces = {}
    for key, sub in q.filter(pl.col("correct").is_not_null()).group_by(by):
        eces[key[0]] = ece(sub["p_top"].to_numpy(), sub["correct"].cast(pl.Float64).to_numpy())
    return g.with_columns(pl.col(by).map_elements(lambda k: eces.get(k), return_dtype=pl.Float64).alias("ece"))


def zscores(c: pl.DataFrame, q: pl.DataFrame) -> pl.DataFrame:
    """Binomial z against the corpus rate for share metrics; mean/sd z for continuous ones; NaN below MIN_N."""
    base = {m: q[col].cast(pl.Float64).drop_nulls() for m, col in
            [("accuracy", "correct"), ("decisive", "decisive"), ("crowd_agree", "crowd_agree"),
             ("stability", "stability"), ("frame_gap", "frame_gap"), ("crowd_tvd", "crowd_tvd")]}
    exprs = []
    for m, nn in [("accuracy", "n_truth"), ("decisive", "n"), ("crowd_agree", "n_crowd"), ("stability", "n"),
                  ("frame_gap", "n"), ("crowd_tvd", "n_crowd")]:
        mu, sd = float(base[m].mean()), float(base[m].std())
        exprs.append(pl.when(pl.col(nn) >= MIN_N).then((pl.col(m) - mu) / (sd / pl.col(nn).cast(pl.Float64).sqrt()))
                     .otherwise(None).alias(f"z_{m}"))
    c = c.with_columns(exprs)
    zc = [e.meta.output_name() for e in exprs]
    return c.with_columns(pl.max_horizontal([pl.col(z).abs() for z in zc]).alias("z_max"))


def main():
    q = load()
    print(f"shown answered rows: {q.height:,}")
    base = {"accuracy": q["correct"].cast(pl.Float64).mean(), "decisive": q["decisive"].cast(pl.Float64).mean(),
            "crowd_agree": q["crowd_agree"].cast(pl.Float64).mean(), "stability": q["stability"].mean(),
            "frame_gap": q["frame_gap"].mean()}
    print("corpus baseline:", {k: round(v, 3) for k, v in base.items()})
    for by, name in [("node_id", "node_cards"), ("source", "source_cards"), ("l2", "l2_cards"), ("l1", "l1_cards")]:
        c = zscores(cards(q, by), q).sort("z_max", descending=True, nulls_last=True)
        c.write_parquet(OUT / f"{name}.parquet")
        print(f"{name}: {c.height} cards; with |z|>=5 on some metric: {c.filter(pl.col('z_max') >= 5).height}")
    (OUT / "baseline.json").write_text(json.dumps({k: round(float(v), 4) for k, v in base.items()}, indent=1))


if __name__ == "__main__":
    main()
