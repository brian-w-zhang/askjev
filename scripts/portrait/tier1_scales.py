"""Portrait, tier 1: the Open Psychometrics scales (openpsych source) scored against the people who took them.

Each scale's rating items carry the real answer distribution of the site's respondents. For every scale with at
least five shown items, this compares Jev's own answer, Jev's answer for "most people", and the average real answer,
item by item on a 0-1 scale, with reverse-keyed items flipped so higher always means more of the trait. The gap
(Jev minus people) gets a 90% interval from resampling items. This is "you vs the average answer of people who took
the test online", not a percentile: the site publishes item distributions, not individual scores.

Writes claims with section "scales" into data/analysis/findings.json (replacing earlier ones). No Jev calls.

  uv run python scripts/portrait/tier1_scales.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from askjev import db

A = Path("data/analysis")
RNG = np.random.default_rng(11)
MIN_ITEMS = 5


def mean_level(dist: dict, k: int) -> float | None:
    """Expected level (0..k-1) of a Score distribution keyed "0".."k-1"."""
    tot = sum(dist.values())
    if not tot:
        return None
    return sum(int(key) * v for key, v in dist.items() if key.isdigit()) / tot


def main():
    with db.connect() as c:
        rows = c.execute("""
            select q.id, q.text, q.options, q.meta->>'instrument' ins, q.meta->>'scale' sc, q.meta->>'keyed' keyed,
                   (select a.distribution from probes p join answers a on a.probe_id = p.id
                     where p.question_id = q.id and p.universe_id = 'base' and p.variant_kind = 'base' and p.frame in ('self','none') limit 1) jev,
                   (select a.distribution from probes p join answers a on a.probe_id = p.id
                     where p.question_id = q.id and p.universe_id = 'base' and p.variant_kind = 'base' and p.frame = 'human' limit 1) guess,
                   (select jsonb_build_object('dist', h.distribution, 'n', h.n) from human_dists h where h.question_id = q.id
                     order by h.n desc nulls last limit 1) hum
            from questions q
            where q.source = 'openpsych' and q.primitive = 'score' and q.display_ok and q.meta->>'scale' is not null
              and q.meta->>'keyed' in ('+', '-')""").fetchall()
    scales: dict[tuple, list] = {}
    for r in rows:
        if not r["jev"] or not r["hum"]:
            continue
        k = len(r["options"])
        vals = [mean_level(r["jev"], k), mean_level(r["guess"], k) if r["guess"] else None, mean_level(r["hum"]["dist"], k)]
        if vals[0] is None or vals[2] is None:
            continue
        flip = r["keyed"] == "-"
        norm = [None if v is None else ((k - 1 - v) if flip else v) / (k - 1) for v in vals]
        scales.setdefault((r["ins"], r["sc"]), []).append({"id": r["id"], "self": norm[0], "guess": norm[1], "people": norm[2],
                                                          "n": r["hum"]["n"] or 0, "text": r["text"]})
    claims = []
    for (ins, sc), items in sorted(scales.items()):
        if len(items) < MIN_ITEMS:
            continue
        s = np.array([i["self"] for i in items]); h = np.array([i["people"] for i in items])
        g = np.array([i["guess"] for i in items if i["guess"] is not None])
        gap = s - h
        boots = [gap[RNG.integers(0, len(gap), len(gap))].mean() for _ in range(1000)]
        ci = [round(float(np.percentile(boots, 5)), 3), round(float(np.percentile(boots, 95)), 3)]
        # the items where Jev and the test-takers differ most, for the drawer
        ex = [i["id"] for i in sorted(items, key=lambda i: -abs(i["self"] - i["people"]))[:3]]
        slug = f"{ins}_{sc}".lower().replace(" ", "_").replace(":", "").replace("/", "_").replace("+", "")
        claims.append({
            "id": f"scale_{slug}", "section": "scales", "tier": "1", "n": len(items), "effect": round(float(gap.mean()), 3),
            "ci90": ci, "examples": ex, "script": "scripts/portrait/tier1_scales.py",
            "instrument": ins, "scale": sc, "self": round(float(s.mean()), 3), "people": round(float(h.mean()), 3),
            "guess": round(float(g.mean()), 3) if len(g) else None, "median_respondents": int(np.median([i["n"] for i in items])),
            "sentence": f"{ins} {sc}: Jev {s.mean():.2f} vs the average test-taker {h.mean():.2f} (0-1, higher = more "
                        f"{sc.lower()}), over {len(items)} items.",
        })
    L = json.loads((A / "findings.json").read_text())
    L["claims"] = [c for c in L["claims"] if c.get("section") != "scales"] + claims
    L["n_claims"] = len(L["claims"])
    (A / "findings.json").write_text(json.dumps(L, indent=1, default=str))
    for c in sorted(claims, key=lambda c: -abs(c["effect"])):
        sig = "" if c["ci90"][0] <= 0 <= c["ci90"][1] else " *"
        print(f"{c['effect']:+.2f} [{c['ci90'][0]:+.2f},{c['ci90'][1]:+.2f}]{sig}  {c['instrument']} | {c['scale']}  self {c['self']:.2f} ppl {c['people']:.2f} guess {c['guess']} n={c['n']} resp~{c['median_respondents']}")


if __name__ == "__main__":
    main()
