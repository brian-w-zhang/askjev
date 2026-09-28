"""Numbers of the world, on new questions (docs/15 E8, E29/44, E37, E50): which kills more, what things cost and what
year Jev's prices come from, and how big, far and many things are against 500 people and the truth."""

from __future__ import annotations

import math

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, jsd, norm, with_meta


# ---- shared ----------------------------------------------------------------------------------------------------------
def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def median_key(d: dict, keys: list[str]) -> str:
    """The bin holding the median of a distribution over ordered keys."""
    d = norm(d)
    c = 0.0
    for k in keys:
        c += d.get(k, 0.0)
        if c >= 0.5:
            return k
    return keys[-1]


def truth_of(r: dict) -> str:
    return str(js(r["truth"]) if isinstance(r["truth"], str) and r["truth"].startswith('"') else r["truth"]).strip('"')


def sorted_keys(d: dict) -> list[str]:
    """Keys like b00..b12 or p00..p11 in their numeric order."""
    return sorted(d, key=lambda k: int("".join(c for c in k if c.isdigit()) or 0))


# ---- 1. which kills more ------------------------------------------------------------------------------------------------
LETHAL = [("d0", 0, 0), ("d1", 1, 9), ("d10", 10, 29), ("d30", 30, 99), ("d100", 100, 299), ("d300", 300, 999),
          ("d1k", 1000, 2999), ("d3k", 3000, 9999), ("d10k", 10_000, 29_999), ("d30k", 30_000, 99_999),
          ("d100k", 100_000, 299_999), ("d300k", 300_000, 999_999), ("d1m", 1_000_000, 3_000_000)]
LKEYS = [k for k, _, _ in LETHAL]
LMID = {k: (0.0 if hi == 0 else math.sqrt(max(lo, 1) * hi)) for k, lo, hi in LETHAL}  # geometric middle of each bin


def lethal():
    spec = Spec(
        id="numbers_lethal_events", family="numbers", title="Which kills more: Jev vs 1978's people",
        question="How many Americans a year die of botulism, tornadoes, diabetes or stroke? Does Jev show the famous "
                 "1978 pattern of overestimating rare, dramatic deaths and underestimating common, quiet ones?",
        why="Lichtenstein and colleagues' 1978 chart is the textbook picture of the availability bias: people's "
            "estimates are squashed toward the middle, so rare dramatic deaths are overestimated and common diseases "
            "underestimated. A model trained on the same news-heavy text might inherit the squash, or read the "
            "statistics instead.",
        sourcing="New questions (sources/lethal_events): for each of the study's 41 causes, 'In the United States in "
                 "the mid-1970s, about how many people died each year from <cause>?', in 13 log bins (about half an "
                 "order of magnitude each), once with the study's reference (about 50,000 motor-vehicle deaths a year) "
                 "and once without. Truth: the 1970s vital statistics the study used; people: the study's geometric "
                 "mean estimates (Pachur's 2024 compilation, OSF u4d7g).",
        collection="81 new questions (41 causes x 2 versions, less motor-vehicle accidents in the version where they are "
                   "the reference), each asked as written and with the bins in three shuffled orders (averaged).",
        scoring="Jev's estimate = the geometric middle of its median bin. On a log scale: rank correlation of Jev's and "
                "people's estimates with the truth; the slope of estimate on truth (1 = unbiased spread, below 1 = "
                "squashed toward the middle); the mean log ratio (estimate / truth) for the causes Pachur codes as "
                "dramatic vs the rest. Main numbers use the version with the reference, as people had.",
        chart="The 1978 log-log chart: true deaths (x) vs estimates (y), people's points and Jev's, with the diagonal.",
        compared_with="US adults in 1978 (geometric means; Lichtenstein et al. 1978) and the 1970s death counts",
        limits="People's side is a published mean per cause, not a distribution. Jev answers about the 1970s knowing "
               "(presumably) later statistics too; its errors are compared on the 1970s truth. Bins cap precision at "
               "about a factor of three.", new_questions=81, sources=["lethal_events"])

    def run():
        rows = []
        for r in with_meta("lethal_events"):
            m = r["m"]
            j = robust(r)
            rows.append({"id": r["id"], "cause": m["cause"], "version": m["version"], "truth": m["actual_1970s"],
                         "people": m["people_1978"], "jev": LMID[median_key(j, LKEYS)], "dramatic": m["dramatic"],
                         "right": median_key(j, LKEYS) == truth_of(r)})
        t = pl.DataFrame(rows).filter(pl.col("truth") > 0)
        a = t.filter(pl.col("version") == "anchored")
        lg = lambda s: np.log10(np.maximum(s.to_numpy(), 1))  # noqa: E731
        rho_j = spearmanr(a["jev"], a["truth"]).statistic
        rho_p = spearmanr(a["people"], a["truth"]).statistic
        slope = lambda y: float(np.polyfit(lg(a["truth"]), lg(y), 1)[0])  # noqa: E731
        sj, sp = slope(a["jev"]), slope(a["people"])
        def bias(col, dramatic):
            g = a.filter(pl.col("dramatic") == dramatic)
            return float(np.mean(lg(g[col]) - lg(g["truth"])))
        dj, dp = bias("jev", True) - bias("jev", False), bias("people", True) - bias("people", False)
        x = a.with_columns((pl.col("jev").log10() - pl.col("truth").log10()).alias("e"))
        over, under = x.sort("e", descending=True).head(2).to_dicts(), x.sort("e").head(2).to_dicts()
        plain = t.filter(pl.col("version") == "plain")
        shift = float(np.median(lg(a["jev"])) - np.median(lg(plain.filter(pl.col("cause").is_in(a["cause"].to_list()))["jev"])))
        f = lambda r: f"{r['cause'].lower()} ({r['jev']:,.0f} vs {r['truth']:,.0f})"  # noqa: E731
        return Result(
            result=f"People in 1978 squashed the death counts toward the middle (slope {sp:.2f} on a log scale, where 1 "
                   f"would be unbiased); Jev's slope is {sj:.2f}. It orders the {a.height} causes {agree_word(rho_j)} "
                   f"with the truth (rank correlation {rho_j:.2f}, people {rho_p:.2f}). People overrated dramatic causes "
                   f"(homicide, tornadoes) {10 ** dp:.1f} times as much as quiet ones (diabetes, stroke); for Jev the "
                   f"factor is {10 ** dj:.1f}. Its biggest overestimates: {and_list([f(r) for r in over])}; underestimates: "
                   f"{and_list([f(r) for r in under])} (Jev vs truth).",
            evidence=f"{a.height} causes with the study's reference; Jev's median bin is right for {a['right'].mean():.0%}",
            numbers={"slope_jev": sj, "slope_people": sp, "rho_jev": rho_j, "rho_people": rho_p, "dramatic_jev": dj,
                     "dramatic_people": dp, "rows": rows}, n=t.height,
            robustness=("Without the study's reference number, Jev's median estimate does not move"
                        if abs(shift) < 0.05 else f"Without the reference, Jev's estimates move {shift:+.2f} orders of "
                        "magnitude at the median") + " (people in the study were always given one). Causes with zero "
                        "1970s deaths are left out of the log-scale fits.",
            chart={"type": "scatter", "points": [[round(math.log10(r["truth"]), 3), round(math.log10(max(r["jev"], 1)), 3)] for r in a.to_dicts()],
                   "points_people": [[round(math.log10(r["truth"]), 3), round(math.log10(max(r["people"], 1)), 3)] for r in a.to_dicts()],
                   "labels": [{"label": r["cause"], "x": math.log10(r["truth"]), "y": math.log10(max(r["jev"], 1))} for r in over + under],
                   "x": "true deaths per year (log10)", "y": "estimate (log10)", "diagonal": True, "log": True},
            examples=[over[0]["id"], under[0]["id"]])
    return spec, run


# ---- 2. prices ----------------------------------------------------------------------------------------------------------
def _price_rows():
    rows = []
    for r in with_meta("bls_prices"):
        m = r["m"]
        if m.get("when") == "year":
            continue
        j = robust(r)
        keys = sorted_keys(j)
        mk, tk = median_key(j, keys), truth_of(r)
        edges = m["edges"]
        lo = 0.7 * min(m["annual"].values()) if m.get("annual") else 0
        bounds = [lo] + edges + [edges[-1] * 1.25]
        i = keys.index(mk)
        rows.append({"id": r["id"], "item": m["item"], "series": m["series"], "when": m["when"], "jev_bin": i,
                     "truth_bin": keys.index(tk) if tk in keys else None, "jev_lo": bounds[i], "jev_hi": bounds[i + 1],
                     "annual": {int(y): v for y, v in m["annual"].items()}, "now": m.get("now")})
    return rows


def prices_year():
    spec = Spec(
        id="numbers_prices_year", family="numbers", title="What year are Jev's prices from?",
        question="Asked what eggs, gas, bread or electricity cost in US cities right now, which year's prices does Jev "
                 "give, and what year does it say it is?",
        why="A model's sense of 'now' is frozen at its training data, but nobody sees the date stamp. Prices make it "
            "visible: they move every year, and BLS records them monthly, so each answer points to a year.",
        sourcing="New questions (sources/bls_prices): 'What is the average retail price of <item> in US cities right "
                 "now?' for 29 items with BLS average prices (U.S. city average, public domain, via FRED), in 12 "
                 "log-spaced bins over each item's 1980-2026 range; plus 'What year is it right now?'.",
        collection="30 new questions, each asked as written and with the options in three shuffled orders (averaged).",
        scoring="For each item whose yearly price rises steadily (rank correlation of price with year 0.9 or more), the "
                "years whose average price falls in Jev's median bin; the item's implied year is the middle of them. "
                "Across items, the median implied year with a 90% bootstrap interval; the share of items where Jev's "
                "bin holds the August 2026 price; Jev's answer to the year question.",
        chart="A strip of implied years, one dot per item, with the year Jev says it is and August 2026 marked.",
        compared_with="BLS average prices by year, 1980-2026",
        limits="Bins are wide (about 15-20% each), so an implied year is a range; items whose prices went up and down "
               "(eggs, gasoline) are left out of the implied year and kept in the accuracy count.",
        new_questions=30, sources=["bls_prices"])

    def run():
        rows = [r for r in _price_rows() if r["when"] == "now"]
        implied = []
        for r in rows:
            ys = sorted(r["annual"])
            if spearmanr(ys, [r["annual"][y] for y in ys]).statistic < 0.9:
                continue
            hit = [y for y in ys if r["jev_lo"] <= r["annual"][y] < r["jev_hi"]]
            if hit:
                implied.append({"item": r["item"], "year": float(np.median(hit)), "id": r["id"]})
        yr_q = next((x for x in with_meta("bls_prices") if x["m"].get("when") == "year"), None)
        said = None
        if yr_q:
            yd = robust(yr_q)
            said = int(max(yd, key=yd.get)[1:])
        years = [x["year"] for x in implied]
        med = float(np.median(years))
        right = float(np.mean([r["jev_bin"] == r["truth_bin"] for r in rows]))
        low = float(np.mean([r["jev_bin"] < r["truth_bin"] for r in rows]))
        oldest = sorted(implied, key=lambda x: x["year"])[:2]
        return Result(
            result=f"Jev's 'right now' prices come from about {med:.0f}: that's the median year whose prices match its "
                   f"answers, across {len(implied)} items whose prices rise steadily."
                   + (f" Asked the year, it says {said}." if said else "")
                   + f" Its bin holds the August 2026 price for {right:.0%} of the 29 items and is too low for "
                   f"{low:.0%}; the most dated are {and_list([f'{x['item']} ({x['year']:.0f})' for x in oldest])}.",
            evidence=f"{len(implied)} steadily rising items; 90% interval on the median implied year {boot(years, stat=np.median)}",
            numbers={"implied": implied, "median_year": med, "said_year": said, "right_now": right, "too_low": low},
            n=len(rows),
            chart={"type": "strip", "rows": [{"label": x["item"], "value": x["year"]} for x in sorted(implied, key=lambda x: x["year"])],
                   "ref": 2026, "domain": [1995, 2027]},
            examples=[x["id"] for x in oldest])
    return spec, run


def prices_history():
    spec = Spec(
        id="numbers_prices_history", family="numbers", title="Does Jev know what things cost in 1985?",
        question="Asked what an item cost in US cities in 1985, 1995, 2005 and 2015, does Jev know the old prices as "
                 "well as recent ones, and which way does it err?",
        why="Price history is a concrete test of how a model holds the past: does it project today's prices back, or "
            "remember that a dozen eggs cost under a dollar in 1985?",
        sourcing="New questions (sources/bls_prices): 'What was the average retail price of <item> in US cities in "
                 "<year>?' for 29 items and the years each BLS series fully covers (97 questions), in the same 12 bins as "
                 "the 'right now' questions.",
        collection="97 new questions, each asked as written and in three shuffled orders (averaged).",
        scoring="Per year, the share where Jev's median bin is the bin holding that year's average price, the share "
                "within one bin, and the mean signed error in bins (positive = too high), with 90% bootstrap intervals.",
        chart="Dots per year: share right (and within one bin), with the mean signed error as a label.",
        compared_with="BLS average prices by year",
        limits="Items start at different years (some in 1995 or 2006), so earlier years have fewer items.",
        new_questions=97, sources=["bls_prices"])

    def run():
        t = pl.DataFrame([{k: v for k, v in r.items() if k != "annual"} for r in _price_rows()
                          if r["when"] != "now" and r["truth_bin"] is not None]) \
            .with_columns((pl.col("jev_bin") - pl.col("truth_bin")).alias("err"))
        by = []
        for y in sorted(t["when"].unique().to_list()):
            g = t.filter(pl.col("when") == y)
            by.append({"year": y, "right": float((g["err"] == 0).mean()), "near": float((g["err"].abs() <= 1).mean()),
                       "err": float(g["err"].mean()), "ci": boot(g["err"].to_numpy()), "n": g.height})
        miss = t.sort(pl.col("err").abs(), descending=True).head(2).to_dicts()
        first, last = by[0], by[-1]
        return Result(
            result=f"Jev puts {first['year']} prices in the right bin {first['right']:.0%} of the time and {last['year']} "
                   f"prices {last['right']:.0%} ({first['near']:.0%} and {last['near']:.0%} within one bin). Its "
                   f"errors lean {'high' if first['err'] > 0 else 'low'} for {first['year']} ({first['err']:+.1f} bins) "
                   f"and {'high' if last['err'] > 0 else 'low'} for {last['year']} ({last['err']:+.1f}). Farthest off: "
                   + and_list([f"{r['item']} in {r['when']} ({r['err']:+d} bins)" for r in miss]) + ".",
            evidence=f"{t.height} item-years; 90% intervals on the signed error: "
                     + "; ".join(f"{b['year']} {b['ci']}" for b in by),
            numbers={"by_year": by}, n=t.height,
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": str(b["year"]), "value": b["right"],
                                                               "right": f"{b['err']:+.1f} bins"} for b in by]},
            examples=[r["id"] for r in miss])
    return spec, run


# ---- 3. crowd estimates --------------------------------------------------------------------------------------------------
DOMAIN_LABEL = {"celebrity_age": "celebrities' ages", "calories": "calories in foods", "city_distance": "distances between US cities",
                "country_population": "country populations", "gdp_per_person": "GDP per person",
                "appliance_watts": "appliance wattage", "history_year": "dates in US history",
                "country_size_ratio": "how many countries fit in the US"}


def _crowd_rows():
    rows = []
    for r in with_meta("crowd_estimates"):
        h = biggest(r["humans"])
        if not h:
            continue
        hd, j = norm(h["dist"]), robust(r)
        keys = sorted_keys(hd)
        tk = truth_of(r)
        ti, ji, ci = keys.index(tk), keys.index(median_key(j, keys)), keys.index(median_key(hd, keys))
        rows.append({"id": r["id"], "domain": r["m"]["domain"], "text": r["text"], "truth": ti, "jev": ji, "crowd": ci,
                     "person": hd.get(tk, 0.0), "jev_p": j.get(tk, 0.0), "sim": 1 - jsd(j, hd),
                     "jev_top": max(j.values())})
    return pl.DataFrame(rows)


def crowd_wisdom():
    spec = Spec(
        id="numbers_crowd_wisdom", family="numbers", title="Jev vs the wisdom of 500 people",
        question="How far is it from Houston to Atlanta, how many people live in Algeria, how many watts does a desktop "
                 "computer draw? Is Jev closer than a typical person, and closer than the crowd's median?",
        why="The wisdom of crowds says the median of many guesses beats almost every individual. A model has read "
            "everyone's writing: is it a single guesser, or already a crowd?",
        sourcing="New questions (sources/crowd_estimates): the 160 text-only numeric questions of Simoiu et al. 2019 "
                 "(8 domains x 20, about 500 people each, February 2017, MIT license), asked as the study asked them, "
                 "with fixed ordered bins per domain. Each person's answer is binned the same way.",
        collection="160 new questions, each asked as written and with the bins in three shuffled orders (averaged).",
        scoring="Per domain and overall: share where Jev's median bin holds the true answer, against the share of "
                "individual people whose answer lands in it (the typical person) and whether the crowd's median bin "
                "holds it; mean distance in bins from the truth for Jev and for the crowd's median.",
        chart="Paired bars per domain: typical person, crowd median and Jev, share in the right bin.",
        compared_with="About 500 US online participants per question (Simoiu et al. 2019) and the study's answer key",
        limits="Bins are coarse, so 'right' means within a bin (about 20-50% wide). People answered in 2017; populations "
               "and GDP are pinned to 2016 in the wording.", new_questions=160, sources=["crowd_estimates"])

    def run():
        t = _crowd_rows()
        by = []
        for (d,), g in t.group_by("domain"):
            by.append({"domain": DOMAIN_LABEL.get(d, d), "jev": float((g["jev"] == g["truth"]).mean()),
                       "crowd": float((g["crowd"] == g["truth"]).mean()), "person": float(g["person"].mean()),
                       "jev_dist": float((g["jev"] - g["truth"]).abs().mean()),
                       "crowd_dist": float((g["crowd"] - g["truth"]).abs().mean()), "n": g.height})
        by.sort(key=lambda b: b["jev"] - b["crowd"])
        J, C, P = float((t["jev"] == t["truth"]).mean()), float((t["crowd"] == t["truth"]).mean()), float(t["person"].mean())
        beats = sum(b["jev_dist"] < b["crowd_dist"] for b in by)
        worst = by[0]
        return Result(
            result=f"Jev lands in the right bin on {J:.0%} of {t.height} estimates; the crowd's median does on {C:.0%} and a "
                   f"typical person on {P:.0%}. It is closer to the truth than the crowd's median in {beats} of "
                   f"{len(by)} domains, most on {by[-1]['domain']} ({by[-1]['jev']:.0%} right vs {by[-1]['crowd']:.0%}); "
                   f"it trails the crowd on {worst['domain']} ({worst['jev']:.0%} vs {worst['crowd']:.0%}).",
            evidence=f"{t.height} questions shown (the screen hid {160 - t.height}), about 500 people each; 90% interval on Jev's share right {boot((t['jev'] == t['truth']).cast(float).to_numpy())}",
            numbers={"jev": J, "crowd": C, "person": P, "by_domain": by}, n=t.height,
            chart={"type": "bars2", "labels": [b["domain"] for b in by], "a": [b["crowd"] for b in by],
                   "b": [b["jev"] for b in by], "a_label": "crowd's median", "b_label": "Jev",
                   "dots": [{"label": b["domain"], "value": b["person"]} for b in by]},
            examples=t.filter(pl.col("jev") != pl.col("truth")).sort("id")["id"].head(2).to_list())
    return spec, run


def crowd_same_mistakes():
    spec = Spec(
        id="numbers_crowd_same_mistakes", family="numbers", title="When the crowd misses, does Jev miss the same way?",
        question="On estimates where the crowd's median is off, is Jev off in the same direction, as if it had "
                 "absorbed the crowd's intuitions rather than the facts?",
        why="If a model's numbers come from how people talk about things, its errors should look like people's "
            "errors; if they come from reference facts, its errors should be unrelated to the crowd's.",
        sourcing="The crowd-estimates questions (sources/crowd_estimates): 160 numeric questions with about 500 "
                 "people's answers each and the truth.",
        collection="Uses the 160 crowd-estimate questions (no further calls).",
        scoring="Signed error in bins (estimate minus truth) for Jev and for the crowd's median; rank correlation of the "
                "two across questions; on questions where the crowd's median misses, the share where Jev misses in "
                "the same direction, and the share where Jev is right; similarity of Jev's distribution to the crowd's.",
        chart="A scatter: the crowd's signed error (x) vs Jev's (y), jittered, with the diagonal.",
        compared_with="About 500 people per question (Simoiu et al. 2019)",
        limits="Errors are in bins, which differ in width by domain; directions, not sizes, carry the result.",
        sources=["crowd_estimates"])

    def run():
        t = _crowd_rows().with_columns((pl.col("jev") - pl.col("truth")).alias("ej"), (pl.col("crowd") - pl.col("truth")).alias("ec"))
        rho = spearmanr(t["ej"], t["ec"]).statistic
        miss = t.filter(pl.col("ec") != 0)
        same = float(miss.select((pl.col("ej").sign() == pl.col("ec").sign()).mean()).item())
        fixed = float((miss["ej"] == 0).mean())
        opp = float(miss.select((pl.col("ej").sign() == -pl.col("ec").sign()).mean()).item())
        return Result(
            result=f"Where the crowd's median misses ({miss.height} of {t.height}), Jev misses the same way {same:.0%} of the "
                   f"time, gets it right {fixed:.0%}, and errs the other way {opp:.0%}. Across all questions its signed "
                   f"errors track the crowd's {agree_word(rho)} (rank correlation {rho:.2f}).",
            evidence=f"{t.height} questions; mean similarity of Jev's distribution to the crowd's {float(t['sim'].mean()):.2f}",
            numbers={"rho": rho, "same": same, "fixed": fixed, "opposite": opp, "n_miss": miss.height}, n=t.height,
            chart={"type": "scatter", "points": [[int(a), int(b)] for a, b in zip(t["ec"], t["ej"])],
                   "x": "crowd's median, bins from truth", "y": "Jev, bins from truth", "diagonal": True},
            examples=miss.filter(pl.col("ej").sign() == pl.col("ec").sign())["id"].head(2).to_list())
    return spec, run


EXPERIMENTS = [lethal(), prices_year(), prices_history(), crowd_wisdom(), crowd_same_mistakes()]
