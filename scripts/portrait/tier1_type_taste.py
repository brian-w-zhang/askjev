"""Portrait tier 1: type (OEJTS) and taste rankings (docs/11-portrait.md §2).

OEJTS: for each dichotomy, Jev's mean probability of each pole across the axis's items (self frame), a bootstrap CI
over items, and the "most people" frame for contrast. No human norms for OEJTS are in the corpus, so this is a
type-like profile, not a percentile.

Taste: per pairwise source, a Bradley-Terry fit (Zermelo/MM iterations) with Jev's pair probabilities as soft wins,
and the same fit on the human pair shares where they exist; Spearman agreement between Jev's and people's rankings;
and, for films and books, agreement between Jev's pairwise ranking and its single-item ratings of the same titles.

  uv run python scripts/portrait/tier1_type_taste.py
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

T = Path("data/analysis/questions.parquet")
OUT = Path("data/analysis/tier1_type_taste.json")
PAIRS = ["movielens_pairs", "goodreads_pairs", "boardgame_pairs", "anime_pairs", "music_pairs", "beer_pairs",
         "food_538", "so_survey_pairs", "goat_pairs"]
RNG = np.random.default_rng(7)


def oejts(q: pl.DataFrame) -> dict:
    axes = defaultdict(lambda: {"self": [], "people": [], "letters": set()})
    for r in q.filter(pl.col("source") == "oejts").iter_rows(named=True):
        m = json.loads(r["meta"] or "{}")
        poles, dich = m.get("poles"), m.get("dichotomy")
        if not poles or not dich or not r["jev_dist"]:
            continue
        first = sorted(set(poles.values()))[0]  # alphabetical first letter of the pair as the reference pole
        for frame, col in (("self", "jev_dist"), ("people", "people_dist")):
            if r[col]:
                d = json.loads(r[col])
                tot = sum(d.values()) or 1
                axes[dich][frame].append(sum(p for k, p in d.items() if poles.get(k) == first) / tot)
        axes[dich]["letters"] |= set(poles.values())
    out = {}
    for dich, v in axes.items():
        letters = sorted(v["letters"]); s = np.array(v["self"])
        boots = [RNG.choice(s, len(s)).mean() for _ in range(2000)]
        p = float(s.mean())
        out[dich] = {"n_items": len(s), "letters": letters, f"p_{letters[0]}": round(p, 3),
                     "ci90": [round(float(np.percentile(boots, 5)), 3), round(float(np.percentile(boots, 95)), 3)],
                     "lean": letters[0] if p > 0.5 else letters[1], "strength": round(abs(p - 0.5) * 2, 3),
                     f"people_p_{letters[0]}": round(float(np.mean(v["people"])), 3) if v["people"] else None}
    print("oejts:", {k: (v["lean"], v["strength"], v["ci90"]) for k, v in out.items()})
    return out


def bradley_terry(pairs: list[tuple[str, str, float, float]], iters: int = 200) -> dict[str, float]:
    """pairs: (a, b, wins_a, wins_b) soft counts. Returns log-strength per item (mean 0)."""
    items = sorted({x for a, b, *_ in pairs for x in (a, b)})
    ix = {k: i for i, k in enumerate(items)}
    w = np.zeros(len(items)); n = defaultdict(float)
    for a, b, wa, wb in pairs:
        w[ix[a]] += wa; w[ix[b]] += wb
        n[(ix[a], ix[b])] += wa + wb
    p = np.ones(len(items))
    for _ in range(iters):
        denom = np.zeros(len(items))
        for (i, j), nij in n.items():
            s = nij / (p[i] + p[j]); denom[i] += s; denom[j] += s
        p = (w + 0.5) / (denom + 1.0 / p.clip(1e-9))  # light prior toward equal strength
        p /= np.exp(np.log(p).mean())
    return {k: float(np.log(p[ix[k]])) for k in items}


def spearman(x, y):
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def taste(q: pl.DataFrame) -> dict:
    out = {}
    ratings = {}
    for r in q.filter(pl.col("source") == "taste_ratings").iter_rows(named=True):
        m = re.match(r"How much would you enjoy (?:watching|reading) (.+)\?$", r["text"])
        if m and r["jev_level"] is not None:
            ratings[m.group(1)] = r["jev_level"]
    for src in PAIRS:
        rows = q.filter((pl.col("source") == src) & pl.col("jev_dist").is_not_null() & pl.col("display_ok"))
        jp, hp, label = [], [], {}
        for r in rows.iter_rows(named=True):
            opts = json.loads(r["options"] or "{}")
            if not isinstance(opts, dict) or len(opts) != 2:
                continue
            (ka, la), (kb, lb) = list(opts.items())
            label[ka], label[kb] = la or ka, lb or kb
            d = json.loads(r["jev_dist"]); tot = (d.get(ka, 0) + d.get(kb, 0)) or 1
            jp.append((ka, kb, d.get(ka, 0) / tot, d.get(kb, 0) / tot))
            for h in json.loads(r["humans"] or "[]")[:1]:
                hd = h["dist"]; ht = (hd.get(ka, 0) + hd.get(kb, 0)) or 1
                hp.append((ka, kb, hd.get(ka, 0) / ht, hd.get(kb, 0) / ht))
        if len(jp) < 200:
            continue
        sj = bradley_terry(jp)
        res = {"n_pairs": len(jp), "n_items": len(sj),
               "top": [{"key": k, "label": label.get(k, k), "strength": round(v, 3)} for k, v in sorted(sj.items(), key=lambda kv: -kv[1])[:15]],
               "bottom": [{"key": k, "label": label.get(k, k), "strength": round(v, 3)} for k, v in sorted(sj.items(), key=lambda kv: kv[1])[:10]]}
        if hp:
            sh = bradley_terry(hp)
            common = [k for k in sj if k in sh]
            res["people_n_pairs"] = len(hp)
            res["spearman_jev_vs_people"] = round(spearman([sj[k] for k in common], [sh[k] for k in common]), 3)
            res["people_top"] = [label.get(k, k) for k, _ in sorted(sh.items(), key=lambda kv: -kv[1])[:10]]
        if src in ("movielens_pairs", "goodreads_pairs"):
            common = [k for k in sj if label.get(k) in ratings]
            if len(common) > 30:
                res["spearman_pairs_vs_own_ratings"] = round(spearman([sj[k] for k in common], [ratings[label[k]] for k in common]), 3)
                res["n_rated_overlap"] = len(common)
        out[src] = res
        print(f"{src:18s} pairs {len(jp):5d} items {len(sj):5d} top: {[t['label'][:28] for t in res['top'][:4]]} "
              f"rho(people)={res.get('spearman_jev_vs_people')} rho(own ratings)={res.get('spearman_pairs_vs_own_ratings')}")
    return out


def main():
    q = pl.read_parquet(T, columns=["id", "source", "text", "meta", "options", "jev_dist", "people_dist", "jev_level",
                                    "humans", "display_ok"])
    OUT.write_text(json.dumps({"oejts": oejts(q), "taste": taste(q)}, indent=1))


if __name__ == "__main__":
    main()
