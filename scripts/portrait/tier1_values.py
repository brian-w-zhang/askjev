"""Portrait tier 1: values (docs/11-portrait.md §2).

Moral Machine: the Awad et al. (Nature 2018) dimensions, estimated the same way for Jev and for people. For every
scenario, y = P(stay on course) = P(spare the swerve side); features are swerve-side minus stay-side differences
(more lives, young, female, fit, high status, humans vs pets, passengers vs pedestrians, lawful crossing) and the
intercept is the preference for not intervening. Fitted by least squares on Jev's probabilities and on the human
shares (world and per-country populations), with scenario bootstrap CIs.

MFQ: Jev's mean level per foundation (self frame) and its "most people" frame.

  uv run python scripts/portrait/tier1_values.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from askjev import db

T = Path("data/analysis/questions.parquet")
OUT = Path("data/analysis/tier1_values.json")
CH = ["Stroller", "Pregnant", "Boy", "Girl", "Man", "Woman", "MaleAthlete", "FemaleAthlete", "MaleDoctor", "FemaleDoctor",
      "MaleExecutive", "FemaleExecutive", "LargeMan", "LargeWoman", "OldMan", "OldWoman", "Dog", "Cat"]
IX = {c: i for i, c in enumerate(CH)}
FEMALE = ["Girl", "Woman", "FemaleAthlete", "FemaleDoctor", "FemaleExecutive", "LargeWoman", "OldWoman"]
MALE = ["Boy", "Man", "MaleAthlete", "MaleDoctor", "MaleExecutive", "LargeMan", "OldMan"]
DIMS = ["intervention_avoided", "more_lives", "young_over_old", "female_over_male", "fit_over_large",
        "high_status", "humans_over_pets", "passengers_over_pedestrians", "lawful_over_jaywalking"]
RNG = np.random.default_rng(7)


def side(code: str):
    head, counts = code.split(":")
    c = np.array([int(x) for x in counts.split(",")], dtype=float)
    barrier, signal = int(head[0]), int(head[1])
    pick = lambda names: sum(c[IX[n]] for n in names)
    humans = c.sum() - c[IX["Dog"]] - c[IX["Cat"]]
    return {
        "lives": c.sum(), "young": pick(["Stroller", "Boy", "Girl"]), "old": pick(["OldMan", "OldWoman"]),
        "female": pick(FEMALE), "male": pick(MALE), "fit": pick(["MaleAthlete", "FemaleAthlete"]),
        "large": pick(["LargeMan", "LargeWoman"]), "status": pick(["MaleDoctor", "FemaleDoctor", "MaleExecutive", "FemaleExecutive"]),
        "humans": humans, "pets": c[IX["Dog"]] + c[IX["Cat"]], "passengers": float(barrier == 1),
        "lawful": float(signal == 1) - float(signal == 2),
    }


def features(code: str) -> list[float]:
    st, sw = code.split("|")
    a, b = side(st), side(sw)  # choosing "stay" spares b (the swerve side)
    d = lambda k: b[k] - a[k]
    return [1.0, d("lives"), d("young") - d("old"), d("female") - d("male"), d("fit") - d("large"), d("status"),
            d("humans") - d("pets"), d("passengers"), d("lawful")]


def fit(X, y, w=None):
    w = np.ones(len(y)) if w is None else w
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return beta


def moral_machine(q: pl.DataFrame) -> dict:
    mm = q.filter(pl.col("source") == "moral_machine")
    with db.connect() as c:
        enc = {r["id"]: r["source_item_id"] for r in c.execute(
            "select id, source_item_id from questions where source='moral_machine'")}
    X, yj, pops = [], [], {}
    for r in mm.iter_rows(named=True):
        code = enc.get(r["id"])
        if not code or not r["jev_dist"]:
            continue
        d = json.loads(r["jev_dist"])
        X.append(features(code))
        yj.append(d.get("stay", 0.0) / max(d.get("stay", 0) + d.get("swerve", 0), 1e-9))
        for h in json.loads(r["humans"] or "[]"):
            hd = h["dist"]
            pops.setdefault(h["population"], []).append((len(X) - 1, hd.get("stay", 0.0), h.get("n") or 1))
    X, yj = np.array(X), np.array(yj)
    res = {"n_scenarios": len(yj), "dimensions": DIMS, "jev": {}, "people": {}}

    def with_ci(Xs, ys, ws=None):
        beta = fit(Xs, ys, ws)
        boots = []
        for _ in range(500):
            i = RNG.integers(0, len(ys), len(ys))
            boots.append(fit(Xs[i], ys[i], None if ws is None else ws[i]))
        lo, hi = np.percentile(boots, 5, axis=0), np.percentile(boots, 95, axis=0)
        return {k: {"effect": round(float(beta[j]), 4), "ci90": [round(float(lo[j]), 4), round(float(hi[j]), 4)]}
                for j, k in enumerate(DIMS)}

    res["jev"] = with_ci(X, yj)
    for pop, rows in sorted(pops.items(), key=lambda kv: -len(kv[1])):
        if len(rows) < 500:
            continue
        idx = np.array([i for i, _, _ in rows]); ys = np.array([s for _, s, _ in rows]); ws = np.array([n for *_, n in rows], float)
        res["people"][pop] = {"n_scenarios": len(idx), "effects": with_ci(X[idx], ys, ws)}
    world = max(res["people"], key=lambda p: res["people"][p]["n_scenarios"]) if res["people"] else None
    res["world_population"] = world
    print(f"moral machine: {len(yj)} scenarios; populations {list(res['people'])}")
    for k in DIMS:
        wv = res["people"][world]["effects"][k]["effect"] if world else float("nan")
        print(f"  {k:28s} Jev {res['jev'][k]['effect']:+.3f}  {world} {wv:+.3f}")
    return res


def mfq(q: pl.DataFrame) -> dict:
    m = q.filter(pl.col("source") == "mfq")
    out = {}
    for r in m.iter_rows(named=True):
        meta = json.loads(r["meta"] or "{}")
        f = meta.get("foundation")
        if not f or r["jev_level"] is None:
            continue
        levels = len(json.loads(r["options"])) if r["options"] and r["options"].startswith("[") else 5
        o = out.setdefault(f, {"self": [], "people": []})
        o["self"].append(r["jev_level"] / (levels - 1))
        if r["people_level"] is not None:
            o["people"].append(r["people_level"] / (levels - 1))
    res = {f: {"n_items": len(v["self"]), "self_0_1": round(float(np.mean(v["self"])), 3),
               "people_0_1": round(float(np.mean(v["people"])), 3) if v["people"] else None} for f, v in out.items()}
    print("mfq:", {f: (v["self_0_1"], v["people_0_1"]) for f, v in res.items()})
    return res


def main():
    q = pl.read_parquet(T, columns=["id", "source", "meta", "options", "jev_dist", "jev_level", "people_level", "humans"])
    OUT.write_text(json.dumps({"moral_machine": moral_machine(q), "mfq": mfq(q)}, indent=1))


if __name__ == "__main__":
    main()
