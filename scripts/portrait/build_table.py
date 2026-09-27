"""Portrait step 1 (docs/11-portrait.md): one row per question with everything the analysis needs, from Postgres to
data/analysis/questions.parquet. Pure SQL + Polars, no Jev calls. JSON-valued columns stay as JSON text and are parsed
by the step that needs them.

  uv run python scripts/portrait/build_table.py
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl

from askjev import db

OUT = Path("data/analysis")
CSV = OUT / "questions.csv"

# meta keys the scoring tiers use (instrument keys, authored trait targets, entity ids, provenance)
META_KEYS = ("measures", "trait", "facet", "keyed", "level_map", "scale", "dichotomy", "poles", "foundation",
             "scenario_type", "domain", "movie_id", "book_id", "bgg_ids", "mal_ids", "beer_ids", "movie_ids", "book_ids",
             "bgg_id", "mal_id", "beer_id", "genre", "authored_file", "round_trip", "unflagged", "mean", "mean_0_5",
             "mean_1_5", "sd", "crowd_pick", "winpercent", "flags")

SQL = f"""
copy (
  select q.id, q.node_id, q.hemisphere, q.kind, q.shape, q.primitive, q.source, q.origin, q.template_id,
         q.text, q.options::text as options, left(q.state::text, 2000) as state, q.truth::text as truth, array_to_string(q.flags, ',') as flags,
         q.display_ok,
         (select jsonb_object_agg(k, q.meta->k) from unnest(array[{",".join(f"'{k}'" for k in META_KEYS)}]) k
            where q.meta ? k)::text as meta,
         m.model_served, m.top, m.p_top, m.margin, m.entropy, m.top_h, m.p_top_h, m.stability, m.frame_gap,
         m.human_gap, m.correct, m.brier,
         b.distribution::text as jev_dist, b.score_scalar as jev_level,
         h.distribution::text as people_dist, h.score_scalar as people_level,
         v.variants::text as variants,
         hd.humans::text as humans
  from questions q
  left join question_meta m on m.question_id = q.id
  left join lateral (select a.distribution, a.score_scalar from probes p join answers a on a.probe_id = p.id
                     where p.question_id = q.id and p.universe_id = 'base' and p.variant_kind = 'base'
                       and p.frame in ('self', 'none') limit 1) b on true
  left join lateral (select a.distribution, a.score_scalar from probes p join answers a on a.probe_id = p.id
                     where p.question_id = q.id and p.universe_id = 'base' and p.variant_kind = 'base'
                       and p.frame = 'human' limit 1) h on true
  left join lateral (select jsonb_agg(jsonb_build_object('kind', p.variant_kind, 'params', p.variant_params,
                                                         'dist', a.distribution, 'level', a.score_scalar)) variants
                     from probes p join answers a on a.probe_id = p.id
                     where p.question_id = q.id and p.universe_id = 'base'
                       and p.variant_kind in ('shuffle', 'reversed_levels')) v on true
  left join lateral (select jsonb_agg(jsonb_build_object('population', population, 'n', n, 'dist', distribution,
                                                         'source', source)) humans
                     from human_dists where question_id = q.id) hd on true
) to stdout with (format csv, header true)
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with db.connect() as c, open(CSV, "wb") as fh:
        with c.cursor().copy(SQL) as cp:
            for chunk in cp:
                fh.write(chunk)
    print(f"exported csv in {time.time() - t0:.0f}s ({CSV.stat().st_size / 1e9:.2f} GB)")
    df = pl.read_csv(CSV, infer_schema_length=0)  # all text first; cast known numerics
    num = ["p_top", "margin", "entropy", "p_top_h", "stability", "frame_gap", "human_gap", "brier", "jev_level",
           "people_level"]
    df = df.with_columns(
        [pl.col(c).cast(pl.Float64) for c in num]
        + [pl.col("display_ok") == "t", pl.when(pl.col("correct") == "t").then(True)
           .when(pl.col("correct") == "f").then(False).otherwise(None).alias("correct")]
    ).with_columns(
        pl.col("node_id").str.split(".").list.get(1, null_on_oob=True).alias("l1"),
        pl.col("node_id").str.split(".").list.slice(0, 3).list.join(".").alias("l2"),
        pl.col("flags").fill_null("").str.contains("harmful").alias("harmful"),
    )
    df.write_parquet(OUT / "questions.parquet", compression="zstd")
    CSV.unlink()
    print(f"wrote {OUT / 'questions.parquet'}: {df.height:,} rows x {df.width} cols in {time.time() - t0:.0f}s")
    print(df.group_by("hemisphere").agg(pl.len(), pl.col("jev_dist").is_not_null().sum().alias("answered"),
                                        pl.col("humans").is_not_null().sum().alias("with_humans"),
                                        pl.col("correct").is_not_null().sum().alias("with_truth")))


if __name__ == "__main__":
    main()
