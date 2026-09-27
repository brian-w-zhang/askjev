"""Portrait tier 1: Big Five percentiles from the 50-item IPIP Big-Five Factor Markers (docs/11-portrait.md §2).

Jev's score per trait = mean over the trait's 10 items of its expected level (1-5), reverse-keyed per the IPIP key.
The human reference is the same scoring applied to every complete respondent in the Open Psychometrics IPIP-FFM file
(2016-2018, one submission per IP address, as the codebook recommends). Percentile = share of respondents below Jev's
score (ties split). Uncertainty: bootstrap over items within each trait. Robustness: the same score from Jev's
reversed-level probes, and from its "most people" answers (which should land near the human median).

  uv run python scripts/portrait/tier1_bigfive.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

T = Path("data/analysis/questions.parquet")
FFM = Path("data/raw/ipip/IPIP-FFM-data-8Nov2018/data-final.csv")
OUT = Path("data/analysis/tier1_bigfive.json")
SCALE = "Big-Five Factor Markers (50-item)"
NAMES = {"EXT": "extraversion", "EST": "neuroticism", "AGR": "agreeableness", "CSN": "conscientiousness", "OPN": "openness"}
RNG = np.random.default_rng(7)


def level_1_5(dist_json: str | None, reverse: bool = False) -> float | None:
    """Expected level on 1-5 from a score distribution {"0": p, ..., "4": p}."""
    if not dist_json:
        return None
    d = json.loads(dist_json)
    ev = sum(int(k) * v for k, v in d.items()) / max(sum(d.values()), 1e-9)
    return ev + 1


def main():
    q = pl.read_parquet(T).filter(pl.col("source") == "ipip")
    items = []
    for r in q.iter_rows(named=True):
        m = json.loads(r["meta"] or "{}")
        if m.get("scale") != SCALE:
            continue
        # openpsychometrics_item is outside META_KEYS in build_table; recover the code from the item text via the codebook
        items.append(r)
    codebook = {}
    for line in Path(FFM.parent / "codebook.txt").read_text().splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0][:3] in NAMES and parts[0][3:].isdigit():
            codebook[parts[1].strip().rstrip(".").lower()] = parts[0]
    rows = []
    for r in items:
        stmt = r["text"].split('"')[1].strip().rstrip(".").lower()
        code = codebook.get(stmt)
        if not code:
            continue
        m = json.loads(r["meta"])
        rev = m.get("keyed") == "-"
        variants = json.loads(r["variants"] or "[]")
        rev_probe = next((v for v in variants if v["kind"] == "reversed_levels"), None)
        rows.append({
            "code": code, "trait": NAMES[code[:3]], "keyed": m.get("keyed"), "text": r["text"], "id": r["id"],
            "jev": level_1_5(r["jev_dist"]), "jev_rev": level_1_5(json.dumps(rev_probe["dist"])) if rev_probe else None,
            "people": level_1_5(r["people_dist"]),
        })
    print(f"matched {len(rows)} of 50 marker items to the codebook")
    # the human file's items are keyed within their own trait: EST items measure emotional stability in the file's
    # naming but the DB trait for them is neuroticism with keys relative to neuroticism; score humans with the DB keys
    key = {r["code"]: (-1 if r["keyed"] == "-" else 1) for r in rows}
    cols = [r["code"] for r in rows]
    h = pl.read_csv(FFM, separator="\t", columns=cols + ["IPC"], infer_schema_length=0)
    h = h.with_columns([pl.col(c).cast(pl.Float64, strict=False) for c in cols + ["IPC"]])
    h = h.filter((pl.col("IPC") == 1) & pl.all_horizontal([(pl.col(c) >= 1) & (pl.col(c) <= 5) for c in cols]))
    print(f"human respondents (complete, one per IP): {h.height:,}")
    H = h.select(cols).to_numpy()
    out = {"instrument": SCALE, "human_reference": f"Open Psychometrics IPIP-FFM 2016-2018, n={h.height}", "traits": {}}
    for trait in NAMES.values():
        idx = [i for i, r in enumerate(rows) if r["trait"] == trait]
        sgn = np.array([key[cols[i]] for i in idx])
        hs = (np.where(sgn > 0, H[:, idx], 6 - H[:, idx])).mean(axis=1)

        def score(vals):
            v = np.array([(x if s > 0 else 6 - x) for x, s in zip(vals, sgn) if x is not None])
            return float(v.mean()) if len(v) else None

        def pct(s):
            return float(((hs < s).sum() + 0.5 * (hs == s).sum()) / len(hs) * 100)

        jev_items = [rows[i]["jev"] for i in idx]
        s_jev = score(jev_items)
        boots = []
        for _ in range(2000):
            pick = RNG.integers(0, len(idx), len(idx))
            v = np.array([(jev_items[j] if sgn[j] > 0 else 6 - jev_items[j]) for j in pick])
            hsb = (np.where(sgn[pick] > 0, H[:, [idx[j] for j in pick]], 6 - H[:, [idx[j] for j in pick]])).mean(axis=1)
            boots.append(((hsb < v.mean()).sum() + 0.5 * (hsb == v.mean()).sum()) / len(hsb) * 100)
        s_rev = score([rows[i]["jev_rev"] for i in idx])
        s_people = score([rows[i]["people"] for i in idx])
        out["traits"][trait] = {
            "n_items": len(idx), "jev_score": round(s_jev, 3), "percentile": round(pct(s_jev), 1),
            "ci90": [round(float(np.percentile(boots, 5)), 1), round(float(np.percentile(boots, 95)), 1)],
            "human_mean": round(float(hs.mean()), 3), "human_sd": round(float(hs.std()), 3),
            "robust_reversed_levels_pct": round(pct(s_rev), 1) if s_rev else None,
            "people_frame_pct": round(pct(s_people), 1) if s_people else None,
            "items": [{"id": rows[i]["id"], "code": rows[i]["code"], "text": rows[i]["text"], "keyed": rows[i]["keyed"],
                       "jev": round(rows[i]["jev"], 2), "human_mean": round(float(H[:, i].mean()), 2)} for i in idx],
        }
        t = out["traits"][trait]
        print(f"{trait:18s} Jev {t['jev_score']:.2f} vs humans {t['human_mean']:.2f}±{t['human_sd']:.2f} -> "
              f"{t['percentile']:.0f}th pct (90% CI {t['ci90'][0]:.0f}-{t['ci90'][1]:.0f}); reversed {t['robust_reversed_levels_pct']}; "
              f"people-frame {t['people_frame_pct']}")
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
