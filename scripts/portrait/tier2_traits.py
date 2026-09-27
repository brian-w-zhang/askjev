"""Portrait tier 2 (docs/11-portrait.md §2): authored trait questions (meta.measures).

The direction audit (data/analysis/audit/tier2_audit.jsonl, 50 random items per facet, judged by hand) found that the
listed order runs low->high for Score items but not for multi-option Choice items (shuffled keys) or type axes
(per-item poles). Tier 2 therefore scores Score items only, in facets whose Score items passed at >= 90% in the audit.
There are no human norms for authored items, so each facet reports Jev's level (0 = lowest level, 1 = highest) next to
its own "most people" frame on the same items (self minus typical person), with an item bootstrap CI.

  uv run python scripts/portrait/tier2_traits.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

T = Path("data/analysis/questions.parquet")
AUDIT = Path("data/analysis/audit")
OUT = Path("data/analysis/tier2_traits.json")
BAR = 0.90
RNG = np.random.default_rng(7)


def passing_facets() -> dict[str, float]:
    sample = {r["id"]: r for r in json.loads((AUDIT / "tier2_sample.json").read_text())}
    agg = defaultdict(lambda: [0, 0])
    for line in (AUDIT / "tier2_audit.jsonl").read_text().splitlines():
        a = json.loads(line)
        if sample[a["id"]]["primitive"] != "score" or ".type." in a["facet"]:
            continue
        agg[a["facet"]][0] += a["verdict"] == "ok"
        agg[a["facet"]][1] += 1
    return {f: ok / n for f, (ok, n) in agg.items() if n >= 10 and ok / n >= BAR}


def main():
    ok = passing_facets()
    q = pl.read_parquet(T, columns=["id", "text", "primitive", "meta", "options", "jev_level", "people_level", "display_ok", "harmful"])
    q = q.filter(pl.col("display_ok") & ~pl.col("harmful") & (pl.col("primitive") == "score") & pl.col("jev_level").is_not_null())
    facets = defaultdict(list)
    for r in q.iter_rows(named=True):
        m = json.loads(r["meta"] or "{}")
        f = m.get("measures")
        if f not in ok:
            continue
        L = len(json.loads(r["options"])) if r["options"] else 5
        facets[f].append((r["id"], r["text"], r["jev_level"] / (L - 1),
                          None if r["people_level"] is None else r["people_level"] / (L - 1)))
    out = {"bar": BAR, "facets": {}}
    for f, items in sorted(facets.items()):
        s = np.array([x[2] for x in items]); p = np.array([x[3] for x in items if x[3] is not None])
        d = np.array([x[2] - x[3] for x in items if x[3] is not None])
        bs = [RNG.choice(s, len(s)).mean() for _ in range(1000)]
        bd = [RNG.choice(d, len(d)).mean() for _ in range(1000)] if len(d) else [0]
        out["facets"][f] = {"audit_ok_rate": round(ok[f], 3), "n_items": len(items),
                            "self": round(float(s.mean()), 3), "self_ci90": [round(float(np.percentile(bs, 5)), 3), round(float(np.percentile(bs, 95)), 3)],
                            "people": round(float(p.mean()), 3) if len(p) else None,
                            "self_minus_people": round(float(d.mean()), 3) if len(d) else None,
                            "gap_ci90": [round(float(np.percentile(bd, 5)), 3), round(float(np.percentile(bd, 95)), 3)]}
        o = out["facets"][f]
        print(f"{f.replace('self.personality.',''):48s} n={len(items):5d} self {o['self']:.2f} people {o['people']} gap {o['self_minus_people']:+.3f} {o['gap_ci90']}")
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
