"""Portrait step 4 (docs/11-portrait.md): the claims ledger, data/analysis/findings.json.

Every candidate finding is computed here from data/analysis/questions.parquet, the tier outputs and the discovery
cards. Each entry has the claim sentence, section, evidence tier, n, effect, a cluster-bootstrap CI (resampling
sources, so one big dataset cannot manufacture confidence), the relevant noise floor, robustness notes, three example
question ids chosen by a fixed seed (never hand-picked) and the Jev version that answered. Nothing reaches the page
unless it is in this file.

  uv run python scripts/portrait/findings.py
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import polars as pl

A = Path("data/analysis")
NOISE = {"noul": 0.03, "score": 0.03, "choice": 0.08}  # measured noise floors (findings-preview.md)
RNG = np.random.default_rng(7)
LEDGER: list[dict] = []


def seeded(ids: list[str], key: str, k: int = 3) -> list[str]:
    return sorted(ids, key=lambda i: hashlib.md5(f"{key}|{i}".encode()).hexdigest())[:k]


def cluster_ci(df: pl.DataFrame, value: str, group: str = "source", b: int = 400) -> tuple[float, list[float]]:
    """Mean of `value` with a bootstrap CI that resamples whole groups (sources/templates)."""
    g = df.group_by(group).agg(s=pl.col(value).cast(pl.Float64).sum(), n=pl.col(value).count())
    s, n = g["s"].to_numpy(), g["n"].to_numpy()
    est = float(s.sum() / max(n.sum(), 1))
    if len(s) < 2:
        return est, [est, est]
    boots = []
    for _ in range(b):
        i = RNG.integers(0, len(s), len(s))
        boots.append(s[i].sum() / max(n[i].sum(), 1))
    return est, [float(np.percentile(boots, 5)), float(np.percentile(boots, 95))]


def add(cid: str, section: str, sentence: str, tier: str, n: int, effect, ci=None, examples=None, **extra):
    LEDGER.append({"id": cid, "section": section, "sentence": sentence, "tier": tier, "n": int(n),
                   "effect": effect, "ci90": ci, "examples": examples or [], "script": "scripts/portrait/findings.py",
                   **extra})


def ordinal(x: float) -> str:
    n = round(x)
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


AXIS = {"IE": "introversion over extraversion", "SN": "sensing over intuition", "FT": "thinking over feeling",
        "JP": "judging over perceiving"}
MM_PHRASE = {"intervention_avoided": "by staying the course", "more_lives": "more lives", "young_over_old": "the young over the old",
             "female_over_male": "women over men", "fit_over_large": "the fit over the large", "high_status": "high status over low",
             "humans_over_pets": "humans over pets", "passengers_over_pedestrians": "passengers over pedestrians",
             "lawful_over_jaywalking": "the lawful over jaywalkers"}
FAV_NAME = {"movielens_pairs": "films", "goodreads_pairs": "books", "boardgame_pairs": "board games", "anime_pairs": "anime",
            "music_pairs": "musicians", "beer_pairs": "beers", "food_538": "candy", "so_survey_pairs": "dev tools",
            "goat_pairs": "GOATs"}
PRIM_NAME = {"choice": "Pick-one", "score": "Rating", "noul": "Yes/no"}


def node_phrase(metric: str, v: float, base: dict) -> str:
    """A discovery card's standout number in words, next to the corpus-wide typical value."""
    b = base.get(metric)
    typ = lambda f: f" (typical {f(b)})" if b is not None else ""
    return {
        "accuracy": lambda: f"right {v:.0%} of the time{typ(lambda x: f'{x:.0%}')}",
        "decisive": lambda: f"95%+ sure on {v:.0%} of questions{typ(lambda x: f'{x:.0%}')}",
        "crowd_agree": lambda: f"gives the crowd's most common answer {v:.0%} of the time{typ(lambda x: f'{x:.0%}')}",
        "stability": lambda: f"keeps its answer when the options are shuffled {v:.0%} of the time{typ(lambda x: f'{x:.0%}')}",
        "frame_gap": lambda: f"Jev's own answer and its 'most people' answer differ by {v:.2f}{typ(lambda x: f'{x:.2f}')}",
        "crowd_tvd": lambda: f"Jev's answers differ from the crowd's by {v:.2f} (0 is identical, 1 is opposite)",
    }.get(metric, lambda: f"{metric.replace('_', ' ')} {v:.2f}")()


def load() -> pl.DataFrame:
    q = pl.read_parquet(A / "questions.parquet")
    return q.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())


def human_top(humans: str | None):
    if not humans:
        return None
    hs = json.loads(humans)
    if not hs:
        return None
    h = max(hs, key=lambda x: x.get("n") or 0)["dist"]
    return max(h, key=h.get) if h else None


def main():
    q = load()
    version = q["model_served"].drop_nulls().mode().to_list()[0] if q["model_served"].drop_nulls().len() else None
    q = q.with_columns(pl.Series("human_top", [human_top(h) for h in q["humans"]], dtype=pl.Utf8))
    q = q.with_columns((pl.col("top") == pl.col("human_top")).alias("crowd_agree"),
                       (pl.col("p_top") >= 0.95).alias("decisive"))
    ids = lambda df: df["id"].to_list()

    # ---- personality (tier 1 and 2) ----
    bf = json.loads((A / "tier1_bigfive.json").read_text())
    for t, v in bf["traits"].items():
        add(f"bigfive_{t}", "personality",
            f"Big Five, {t}: on the public 50-item test, Jev's answers land at the {ordinal(v['percentile'])} percentile of "
            f"the {int(bf['human_reference'].split('n=')[1]):,} people who took it; answering for 'most people', at the "
            f"{ordinal(v['people_frame_pct'])}.", "1", v["n_items"], v["percentile"], v["ci90"],
            seeded([i["id"] for i in v["items"]], f"bf{t}"),
            robustness={"reversed_levels_pct": v["robust_reversed_levels_pct"], "people_frame_pct": v["people_frame_pct"]},
            human_n=int(bf["human_reference"].split("n=")[1].split()[0].strip(",;)")))
    t2 = json.loads((A / "tier2_traits.json").read_text())["facets"]
    neg = [f for f, v in t2.items() if v["self_minus_people"] is not None and v["gap_ci90"][1] < -0.03]
    add("muted_self", "personality",
        f"On {len(neg)} of {len(t2)} trait facets, Jev rates itself lower than it rates 'most people' on the same "
        f"questions: less extraverted, less anxious, less driven, less dark.", "2",
        sum(v["n_items"] for v in t2.values()), round(float(np.mean([v["self_minus_people"] for v in t2.values()])), 3),
        None, [], facets={f.replace("self.personality.", ""): v for f, v in t2.items()}, n_lower=len(neg), n_facets=len(t2))
    tt = json.loads((A / "tier1_type_taste.json").read_text())
    oe = tt["oejts"]
    order = [("IE", "EI"), ("SN", "NS"), ("FT", "TF"), ("JP", "PJ")]
    letters = "".join(oe[k]["lean"] for k, _ in order if k in oe)
    add("type", "personality", f"Type test (OEJTS): Jev leans {letters}, most clearly on "
        f"{AXIS[max(oe, key=lambda k: oe[k]['strength'])]}.", "1", sum(v["n_items"] for v in oe.values()), letters, None,
        [], axes=oe, caveat="type-like profile; OEJTS human norms are not in the corpus")

    # ---- values (tier 1) ----
    vals = json.loads((A / "tier1_values.json").read_text())
    mm = vals["moral_machine"]; w = mm["world_population"]
    mm_ids = ids(q.filter(pl.col("source") == "moral_machine"))
    for dim in mm["dimensions"]:
        j, h = mm["jev"][dim], mm["people"][w]["effects"][dim]
        add(f"mm_{dim}", "values", f"Moral Machine, sparing {MM_PHRASE.get(dim, dim.replace('_', ' '))}: Jev's pull "
            f"{j['effect']:+.2f}, players worldwide {h['effect']:+.2f}.", "1", mm["n_scenarios"], j["effect"], j["ci90"],
            seeded(mm_ids, f"mm{dim}"), people=h, countries={p: v["effects"][dim]["effect"] for p, v in mm["people"].items()})
    mf = vals["mfq"]
    add("mfq", "values", "On the Moral Foundations Questionnaire Jev rates every foundation as less relevant to itself than "
        "to 'most people', lowest on purity and equality.", "1", sum(v["n_items"] for v in mf.values()), None, None,
        seeded(ids(q.filter(pl.col("source") == "mfq")), "mfq"), foundations=mf)

    # ---- taste (tier 1) ----
    def distinct(items: list[dict]) -> list[dict]:
        """Drop near-duplicate entities (Bob Marley / Bob Marley & The Wailers, iPhone 15 / iPhone 17, four kinds of
        Reese's): the higher-ranked one is kept."""
        seen, out = set(), []
        for t in items:
            words = re.findall(r"[a-z]+", t["label"].lower())
            # a possessive brand (Reese's ..., Hershey's ...) is one entity; otherwise the first two real words
            k = words[0] if len(words) > 1 and words[1] == "s" else " ".join([w for w in words if len(w) > 2][:2])
            if k not in seen:
                seen.add(k)
                out.append(t)
        return out

    for src, v in tt["taste"].items():
        v = {**v, "top": distinct(v["top"]), "bottom": distinct(v["bottom"])}
        sub = q.filter(pl.col("source") == src)
        add(f"favorites_{src}", "taste_favorites", f"Favorite {FAV_NAME.get(src, src.replace('_pairs', ''))} from "
            f"{v['n_pairs']:,} head-to-heads: " + ", ".join(t["label"] for t in v["top"][:5]) + ".",
            "1", v["n_pairs"], v.get("spearman_jev_vs_people"), None, seeded(ids(sub), f"fav{src}"),
            top=v["top"], bottom=v["bottom"], rho_people=v.get("spearman_jev_vs_people"),
            rho_own_ratings=v.get("spearman_pairs_vs_own_ratings"))
    tr = q.filter(pl.col("source").is_in(["taste_ratings", "g5_w13_ratings"]) & pl.col("jev_level").is_not_null()
                  & pl.col("people_level").is_not_null()).with_columns((pl.col("jev_level") - pl.col("people_level")).alias("gap"))
    for dom, sub in tr.group_by(pl.col("node_id").str.split(".").list.last()):
        if sub.height < 300:
            continue
        s = sub.sort("gap")
        add(f"beyond_{dom[0]}", "taste_beyond", f"{dom[0].replace('_ratings', '').replace('_', ' ').capitalize()}: what Jev "
            f"rates higher (and lower) for itself than for 'most people'.", "1", sub.height, round(float(sub["gap"].mean()), 3), None,
            ids(s.tail(3)) + ids(s.head(3)), more=[{"id": r["id"], "text": r["text"], "gap": round(r["gap"], 2)} for r in s.tail(8).reverse().iter_rows(named=True)],
            less=[{"id": r["id"], "text": r["text"], "gap": round(r["gap"], 2)} for r in s.head(8).iter_rows(named=True)])

    # ---- how Jev answers: the middle lean on ratings ----
    rt = q.filter(pl.col("source").is_in(["taste_ratings", "g5_w13_ratings"]))
    mid = rt.with_columns(pl.col("top").cast(pl.Utf8).alias("t"), pl.col("options").str.count_matches('", "').alias("k"))
    share_mid = mid.filter(pl.col("k") == 4).select((pl.col("t") == "2").mean()).item()
    choice_top = float(q.filter(pl.col("primitive") == "choice")["p_top"].mean())
    add("middle_lean", "defaults", f"Rating one thing at a time, Jev's single most likely answer is the middle level "
        f"{share_mid:.0%} of the time; on pick-one questions its top answer averages {choice_top:.0%}.",
        "1", mid.height, round(float(share_mid), 3), None, seeded(ids(rt), "mid"), choice_p_top=round(choice_top, 3))

    # ---- knowledge and calibration ----
    tq = q.filter(pl.col("correct").is_not_null())
    for l1, sub in tq.group_by("l1"):
        if sub.height < 1000:
            continue
        acc, ci = cluster_ci(sub.with_columns(pl.col("correct").cast(pl.Float64)), "correct")
        conf = float(sub["p_top"].mean())
        misses = sub.filter((pl.col("p_top") >= 0.9) & ~pl.col("correct"))
        add(f"knowledge_{l1[0]}", "knowledge", f"{l1[0].replace('_', ' ').title()}: right {acc:.0%} of the time at an average "
            f"confidence of {conf:.0%}.", "1", sub.height, round(acc, 3), [round(x, 3) for x in ci],
            seeded(ids(misses), f"miss{l1[0]}") if misses.height else seeded(ids(sub), f"k{l1[0]}"),
            confidence=round(conf, 3), overconfidence=round(conf - acc, 3), confident_misses=misses.height)
    bins = np.linspace(0, 1, 11)
    p, c = tq["p_top"].to_numpy(), tq["correct"].cast(pl.Float64).to_numpy()
    rel = [{"bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}", "n": int(((p >= bins[i]) & (p < bins[i + 1] + (i == 9))).sum()),
            "acc": float(c[(p >= bins[i]) & (p < bins[i + 1] + (i == 9))].mean()) if ((p >= bins[i]) & (p < bins[i + 1] + (i == 9))).any() else None}
           for i in range(10)]
    add("calibration", "calibration", "Where there is a right answer, how often Jev is right at each level of confidence.", "1",
        len(p), None, None, seeded(ids(tq), "cal"), reliability=rel)

    # ---- work effectiveness: Machine tasks against the noise band ----
    mq = tq.filter(pl.col("hemisphere") == "machine")
    for src, sub in mq.group_by("source"):
        if sub.height < 500:
            continue
        acc = float(sub["correct"].cast(pl.Float64).mean()); dec = float(sub["decisive"].cast(pl.Float64).mean())
        cls = "saturated" if acc >= 0.95 and dec >= 0.6 else ("near chance" if acc <= 0.6 else "informative")
        add(f"task_{src[0]}", "work", f"Task {src[0]}: right {acc:.0%} of the time, 95%+ sure on {dec:.0%} of items.", "1", sub.height,
            round(acc, 3), None, seeded(ids(sub.filter(~pl.col("correct"))), f"t{src[0]}"), decisive=round(dec, 3), band=cls)

    # ---- humor near chance ----
    for src in ("imgflip_captions", "rjokes_pairs"):
        sub = tq.filter(pl.col("source") == src)
        if sub.height:
            add(f"humor_{src}", "jaggedness", f"Predicting which {'caption' if 'imgflip' in src else 'joke'} a crowd upvoted more, "
                f"Jev is right {sub['correct'].cast(pl.Float64).mean():.0%} of the time (chance is 50%).", "1", sub.height,
                round(float(sub["correct"].cast(pl.Float64).mean()), 3), None, seeded(ids(sub), src))

    # ---- jaggedness: order and wording sensitivity; the stable core ----
    st = q.filter(pl.col("stability").is_not_null())
    for prim, sub in st.group_by("primitive"):
        add(f"stability_{prim[0]}", "jaggedness", f"{PRIM_NAME.get(prim[0], prim[0])} questions: Jev keeps its answer when "
            f"the options are shuffled {sub['stability'].mean():.0%} of the time.", "1", sub.height, round(float(sub["stability"].mean()), 3),
            None, seeded(ids(sub.filter(pl.col("stability") < 0.5)), f"st{prim[0]}"))
    l2c = pl.read_parquet(A / "l2_cards.parquet").filter((pl.col("n") >= 1000) & pl.col("stability").is_not_null())
    for r in l2c.sort("stability").head(6).iter_rows(named=True):
        add(f"fragile_{r['l2']}", "jaggedness", f"{r['l2']}: the answer survives shuffling the options only {r['stability']:.0%} of the time.",
            "discovery", r["n"], round(r["stability"], 3), None, seeded(ids(st.filter((pl.col("l2") == r["l2"]) & (pl.col("stability") < 0.5))), r["l2"]))
    for r in l2c.sort("stability", descending=True).head(6).iter_rows(named=True):
        add(f"stable_{r['l2']}", "stable_core", f"{r['l2']}: the same answer after shuffling the options {r['stability']:.0%} of the time.",
            "discovery", r["n"], round(r["stability"], 3), None, seeded(ids(q.filter(pl.col("l2") == r["l2"])), r["l2"]))

    # ---- agreement with people (crowd) ----
    cq = q.filter(pl.col("crowd_agree").is_not_null())
    for l1, sub in cq.group_by("l1"):
        if sub.height < 1000:
            continue
        a, ci = cluster_ci(sub.with_columns(pl.col("crowd_agree").cast(pl.Float64)), "crowd_agree")
        add(f"crowd_{l1[0]}", "agreement", f"{l1[0].replace('_', ' ').title()}: Jev's answer matches the most common human "
            f"answer {a:.0%} of the time.", "1", sub.height, round(a, 3), [round(x, 3) for x in ci], seeded(ids(sub), f"cr{l1[0]}"))

    # ---- tier 3 themes ----
    th = json.loads((A / "themes" / "final.json").read_text())
    for name, v in th.items():
        if v["status"] != "kept":
            continue
        sub = q.filter(pl.col("id").is_in(v["members"]))
        lv = sub.filter(pl.col("frame_gap").is_not_null())
        add(f"theme_{name}", "themes", f"Theme, {name.replace('_', ' ')}: about {v['n']:,} questions, {v['precision']:.0%} on topic in an audit.",
            "3", v["n"], round(float(lv["frame_gap"].mean()), 3) if lv.height else None, None, seeded(ids(sub), name),
            precision=v["precision"], decisive=round(float(sub["decisive"].cast(pl.Float64).mean()), 3) if sub.height else None)

    # ---- risk: described gambles against real human choice rates (choices13k, Wulff) ----
    rows = []
    for r in q.filter(pl.col("source").is_in(["choices13k", "wulff_description"])).iter_rows(named=True):
        opts = list(json.loads(r["options"]).keys())
        hs = json.loads(r["humans"] or "[]")
        if len(opts) != 2 or not hs:
            continue
        d, h = json.loads(r["jev_dist"]), max(hs, key=lambda x: x.get("n") or 0)["dist"]
        jt, ht = (d.get(opts[0], 0) + d.get(opts[1], 0)) or 1, (h.get(opts[0], 0) + h.get(opts[1], 0)) or 1
        sure = "for sure" in (r["text"] + json.dumps(json.loads(r["options"]))).lower()
        rows.append((r["id"], d.get(opts[0], 0) / jt, h.get(opts[0], 0) / ht, sure))
    if rows:
        jv, hv = np.array([x[1] for x in rows]), np.array([x[2] for x in rows])
        agree = float(((jv >= 0.5) == (hv >= 0.5)).mean())
        add("risk_gambles", "values", f"Choosing between {len(rows):,} described gambles, Jev picks the same option as most people "
            f"{agree:.0%} of the time (correlation with the human choice share {np.corrcoef(jv, hv)[0, 1]:.2f}).", "1",
            len(rows), round(agree, 3), None, seeded([x[0] for x in rows], "risk"),
            mean_abs_diff=round(float(np.abs(jv - hv).mean()), 3), r=round(float(np.corrcoef(jv, hv)[0, 1]), 3))

    # ---- tier 3 theme stances: Jev's own answer vs its 'most people' answer, on the theme's yes/no questions ----
    for name, v in th.items():
        if v["status"] != "kept":
            continue
        sub = q.filter(pl.col("id").is_in(v["members"]) & (pl.col("primitive") == "noul") & pl.col("people_dist").is_not_null())
        if sub.height < 50:
            continue
        py = lambda s: (json.loads(s).get("true", 0.0) if s else None)
        sj = np.array([py(x) for x in sub["jev_dist"]]); sp = np.array([py(x) for x in sub["people_dist"]])
        add(f"stance_{name}", "themes", f"{name.replace('_', ' ')}: on {sub.height} yes/no questions Jev says yes "
            f"{sj.mean():.0%} on average; for 'most people' it says {sp.mean():.0%}.", "3", sub.height,
            round(float(sj.mean() - sp.mean()), 3), None, seeded(ids(sub), f"stance{name}"),
            self_yes=round(float(sj.mean()), 3), people_yes=round(float(sp.mean()), 3), precision=v["precision"])

    # ---- discovery candidates: the most unusual node cards not already covered ----
    base = json.loads((A / "baseline.json").read_text())
    nc = pl.read_parquet(A / "node_cards.parquet").filter(pl.col("n") >= 300).sort("z_max", descending=True).head(60)
    for r in nc.iter_rows(named=True):
        zs = {k: r[k] for k in r if k.startswith("z_") and k != "z_max" and r[k] is not None}
        m = max(zs, key=lambda k: abs(zs[k])); metric = m[2:]
        add(f"node_{r['node_id']}", "discovery", f"{r['node_id']}: {node_phrase(metric, r[metric], base)}.", "discovery", r["n"], round(float(r[metric]), 3), None,
            seeded(ids(q.filter(pl.col("node_id") == r["node_id"])), r["node_id"]), metric=metric, z=round(zs[m], 1))

    for e in LEDGER:
        e["jev_version"] = version
        e["noise_floor"] = NOISE
    (A / "findings.json").write_text(json.dumps({"n_claims": len(LEDGER), "claims": LEDGER}, indent=1, default=str))
    from collections import Counter
    print(f"ledger: {len(LEDGER)} claims; by section {dict(Counter(e['section'] for e in LEDGER))}; by tier {dict(Counter(e['tier'] for e in LEDGER))}")


if __name__ == "__main__":
    main()
