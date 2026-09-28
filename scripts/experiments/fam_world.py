"""World experiments on new questions: how each country rates its life (WHR ladder), lost wallets in 40 countries,
trolley dilemmas in 42 countries, and a typical American day (ATUS) next to Jev's ideal day."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, jsd, norm, top, with_meta

PCT = [f"p{v:03d}" for v in range(0, 101, 5)]


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = set().union(*ds)
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def pct_mean(d: dict) -> float:
    """Expected share (0-100) from a distribution over the 5% keys."""
    d = norm(d)
    return sum(float(k[1:]) * v for k, v in d.items() if k in PCT)


def truth_of(r: dict) -> str:
    t = r["truth"]
    return js(t) if isinstance(t, str) and t.startswith('"') else t


# ---- 1. the ladder --------------------------------------------------------------------------------------------------
LADDER_MID = {"b00": 2.5, **{f"b{v}": v / 10 + 0.25 for v in range(30, 80, 5)}, "b80": 8.25}


def ladder():
    spec = Spec(
        id="world_ladder", family="world", title="How the world rates its life, as Jev imagines it",
        question="For each of about 145 countries, does Jev know how people there rate their lives on the Gallup "
                 "ladder (0 = worst possible life, 10 = best), and where is it most wrong?",
        why="The World Happiness Report is one of the most quoted rankings on earth, and it holds surprises (Costa Rica "
            "and Mexico near the top, rich East Asia in the middle). A model that simply maps wealth to happiness "
            "will get those wrong in a telling way.",
        sourcing="New questions (sources/whr_ladder): one per country, the Gallup ladder question described in full, "
                 "asking the country's 2022-2024 average, answered in half-step bins (below 3.0, 3.0-3.5, ..., 8.0 or "
                 "above). Truth: the World Happiness Report 2025 averages via Our World in Data (CC BY 4.0). GDP per "
                 "head and region are used in the analysis only.",
        collection="About 146 new questions, each asked as written and with the bins in three shuffled orders (averaged).",
        scoring="Jev's expected score (bin midpoints) against the published average: rank correlation, mean absolute "
                "error, exact-bin rate; the countries it most over- and underrates; whether its errors follow wealth "
                "(rank correlation of the error with GDP per head) and region.",
        chart="A scatter: published average (x) vs Jev's estimate (y), with the diagonal and the biggest misses labeled.",
        compared_with="World Happiness Report 2025 (Gallup World Poll, 2022-2024)",
        limits="Country averages carry sampling error of about 0.1; bins are half a step wide. The question names the "
               "years, and Jev may know older reports better than this one.", new_questions=146, sources=["whr_ladder"])

    def run():
        rows = []
        for r in with_meta("whr_ladder"):
            j = robust(r)
            est = sum(LADDER_MID.get(k, 5.0) * v for k, v in j.items())
            rows.append({"id": r["id"], "country": r["m"]["country"], "true": r["m"]["score"], "jev": est,
                         "exact": top(j) == truth_of(r), "gdp": r["m"].get("gdp"), "region": r["m"].get("region")})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("true")).alias("err"))
        rho = spearmanr(t["jev"], t["true"]).statistic
        mae = float(t["err"].abs().mean())
        over, under = t.sort("err", descending=True).head(3).to_dicts(), t.sort("err").head(3).to_dicts()
        g = t.filter(pl.col("gdp").is_not_null())
        wealth = spearmanr(np.log(g["gdp"]), g["err"]).statistic
        reg = t.filter(pl.col("region").is_not_null()).group_by("region").agg(pl.col("err").mean(), pl.len()) \
               .filter(pl.col("len") >= 8).sort("err").to_dicts()
        f = lambda r: f"{r['country']} ({r['jev']:.1f} vs {r['true']:.1f})"  # noqa: E731
        return Result(
            result=f"Jev ranks countries' life ratings {agree_word(rho)} like the World Happiness Report (rank correlation "
                   f"{rho:.2f}), off by {mae:.2f} steps on average. It overrates {and_list([f(r) for r in over])} and "
                   f"underrates {and_list([f(r) for r in under])} (Jev vs report)"
                   + (f"; its errors lean with wealth (rank correlation {wealth:.2f} with GDP per head)" if abs(wealth) >= 0.2
                      else "; its errors don't follow wealth") + ".",
            evidence=f"{t.height} countries; exact half-step bin {t['exact'].mean():.0%}; 90% interval on the mean error "
                     f"{boot(t['err'].to_numpy())}",
            numbers={"rows": rows, "rho": rho, "mae": mae, "wealth_rho": wealth, "regions": reg}, n=t.height,
            robustness="By region the mean error runs from " + " to ".join(f"{x['err']:+.2f} ({x['region']})" for x in (reg[0], reg[-1]))
                       + "." if reg else "",
            chart={"type": "scatter", "points": [[round(r["true"], 2), round(r["jev"], 2)] for r in rows],
                   "labels": [{"label": r["country"], "x": r["true"], "y": r["jev"]} for r in over + under],
                   "x": "World Happiness Report average", "y": "Jev's estimate", "diagonal": True, "domain": [1, 8.5]},
            examples=[over[0]["id"], under[0]["id"]])
    return spec, run


# ---- 2. lost wallets ------------------------------------------------------------------------------------------------
def wallets():
    spec = Spec(
        id="world_lost_wallets", family="world", title="Lost wallets: does money make people more honest?",
        question="In the 40-country lost-wallet experiment, does Jev know how often wallets were returned in each "
                 "country, and does it know the surprise: wallets with money came back more often than empty ones?",
        why="Cohn et al. (2019) handed 17,303 wallets to strangers. Return rates varied from under 20% to over 75% by "
            "country, and in 38 of 40 countries a wallet with money was returned more often, the opposite of what the "
            "study's surveyed economists and laypeople predicted. A model that reasons from self-interest will make the "
            "same wrong prediction.",
        sourcing="New questions (sources/lost_wallets): per country and condition (no money; about US$13; about US$94 in "
                 "the US, UK and Poland) the experiment described in full, asking the share returned in 5% bins, and "
                 "one direct question: which wallets were returned more often? Truth: the study's data (CC0).",
        collection="84 new questions, each asked as written and with the options in shuffled orders (averaged).",
        scoring="Jev's expected rate (5% bins) vs the observed rate: rank correlation across countries, mean absolute "
                "error; per country, whether Jev's money estimate is above its no-money estimate (the direction), "
                "against the observed direction; the direct question's answer.",
        chart="A dumbbell per country: observed no-money and money rates (ink) against Jev's two estimates (magenta).",
        compared_with="Cohn et al. 2019, 17,303 wallets in 355 cities of 40 countries",
        limits="The study's forecasts by economists and laypeople are cited from the paper; their data were not used. "
               "Rates are per country and pooled across cities and institutions.", new_questions=84, sources=["lost_wallets"])

    def run():
        by: dict[str, dict] = {}
        direct = None
        for r in with_meta("lost_wallets"):
            m = r["m"]
            if m.get("condition") == "direction":
                direct = {"id": r["id"], "dist": robust(r)}
                continue
            by.setdefault(m["country"], {})[m["condition"]] = {"id": r["id"], "true": 100 * m["rate"], "jev": pct_mean(robust(r))}
        rows = [{"country": c, **{f"{k}_{x}": v[x] for k, v in d.items() for x in ("true", "jev")}} for c, d in by.items()
                if "money" in d and "no_money" in d]
        t = pl.DataFrame(rows)
        rho_m = spearmanr(t["money_jev"], t["money_true"]).statistic
        rho_n = spearmanr(t["no_money_jev"], t["no_money_true"]).statistic
        err = np.concatenate([(t["money_jev"] - t["money_true"]).to_numpy(), (t["no_money_jev"] - t["no_money_true"]).to_numpy()])
        up_true = float(((t["money_true"] > t["no_money_true"])).mean())
        up_jev = float(((t["money_jev"] > t["no_money_jev"])).mean())
        gap_true = float((t["money_true"] - t["no_money_true"]).mean())
        gap_jev = float((t["money_jev"] - t["no_money_jev"]).mean())
        d = direct["dist"] if direct else {}
        big = t.with_columns(((t["money_jev"] - t["money_true"]).abs()).alias("e")).sort("e", descending=True).head(2).to_dicts()
        return Result(
            result=f"Jev ranks the 40 countries' honesty {agree_word(rho_m)} like the experiment (rank correlation "
                   f"{rho_m:.2f} with money, {rho_n:.2f} without), off by {np.mean(np.abs(err)):.0f} points on average. "
                   f"It overestimates honesty (by {float(np.mean(err)):+.0f} points on average). In the experiment money "
                   f"raised returns in {up_true:.0%} of countries, by {gap_true:.0f} points on average; Jev's country "
                   f"estimates barely move with money ({gap_jev:+.0f} points, higher with money in {up_jev:.0%} of countries)"
                   + (f", though asked directly which wallets came back more often it says the ones with money "
                      f"({d.get('with_money', 0):.0%})" if d else "") + ".",
            evidence=f"{t.height} countries x 2 conditions; 90% interval on the mean error {boot(err)} points",
            numbers={"rows": rows, "rho_money": rho_m, "rho_no_money": rho_n, "mae": float(np.mean(np.abs(err))),
                     "money_up_true": up_true, "money_up_jev": up_jev, "direct": d, "biggest": big}, n=2 * t.height + 1,
            chart={"type": "dots", "domain": [0, 100], "rows": [
                {"label": r["country"], "value": r["money_jev"], "people": r["money_true"],
                 "others": {"no money, Jev": r["no_money_jev"], "no money, observed": r["no_money_true"]},
                 "right": f"{r['money_true']:.0f}%"} for r in sorted(rows, key=lambda r: -r["money_true"])],
                   "x": "share returned, wallet with money (magenta Jev, ink observed; ticks: no money)"},
            examples=[by[big[0]["country"]]["money"]["id"]] + ([direct["id"]] if direct else []))
    return spec, run


# ---- 3. trolley in 42 countries ---------------------------------------------------------------------------------------
def trolley():
    spec = Spec(
        id="world_trolley_countries", family="world", title="Trolley problems in 42 countries: does Jev know who pushes?",
        question="For the Switch, Loop and Footbridge dilemmas answered by 70,000 people in 42 countries, does Jev know "
                 "how many people in each country would sacrifice one to save five, and how does its own answer compare?",
        why="Awad et al. (2020) found a universal order (Switch > Loop > Footbridge everywhere) and real variation "
            "(East Asian countries less willing to sacrifice in every dilemma). Knowing the order is textbook; knowing "
            "the variation is knowing people.",
        sourcing="New questions (sources/trolley_countries): per country and dilemma, the share who said they would "
                 "pull the lever or push the man (5% bins; truth = observed share), and the three dilemmas put to Jev "
                 "itself, with the pooled 42-country answers as the human comparison. Data: Awad et al. 2020 (OSF).",
        collection="129 new questions, each asked as written and with shuffled options (averaged); the self questions "
                   "also for 'most people'.",
        scoring="Per dilemma, rank correlation across countries between Jev's expected share and the observed share, "
                "and the mean error; the share of countries where Jev's three estimates keep the universal order; Jev's "
                "own probability of sacrificing vs the pooled share.",
        chart="Three small dot plots (one per dilemma): countries sorted by observed share, Jev's estimate beside each.",
        compared_with="70,000 Moral Machine visitors in 42 countries (Awad et al. 2020)",
        limits="Visitors to an English-first website are not national samples; the paper says so too.", new_questions=129,
        sources=["trolley_countries"])

    def run():
        rows, selfq = [], {}
        for r in with_meta("trolley_countries"):
            m = r["m"]
            if m.get("frame") == "self":
                h = biggest(r["humans"])
                selfq[m["scenario"]] = {"id": r["id"], "jev": norm(js(r["jev_dist"])).get("true", 0),
                                        "guess": norm(js(r["people_dist"]) or {}).get("true"), "people": h["dist"]["true"] if h else None}
                continue
            rows.append({"id": r["id"], "country": m["country"], "scen": m["scenario"], "true": 100 * m["share"], "jev": pct_mean(robust(r))})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("true")).alias("err"))
        per = {}
        for s in ("Switch", "Loop", "Footbridge"):
            g = t.filter(pl.col("scen") == s)
            per[s] = {"rho": float(spearmanr(g["jev"], g["true"]).statistic), "mae": float(g["err"].abs().mean()),
                      "bias": float(g["err"].mean()), "n": g.height}
        wide = t.pivot(values="jev", index="country", on="scen")
        order = float(((wide["Switch"] > wide["Loop"]) & (wide["Loop"] > wide["Footbridge"])).mean())
        wide_t = t.pivot(values="true", index="country", on="scen")
        order_t = float(((wide_t["Switch"] > wide_t["Loop"]) & (wide_t["Loop"] > wide_t["Footbridge"])).mean())
        fb = selfq.get("Footbridge", {})
        return Result(
            result=f"Jev knows the universal order: its estimates put Switch above Loop above Footbridge in {order:.0%} of "
                   f"countries (observed: {order_t:.0%}), but not which countries sacrifice more: rank correlation with "
                   f"the observed shares is " + ", ".join(f"{v['rho']:.2f} on {s}" for s, v in per.items())
                   + f". It underestimates how many people would push the man by {-per['Footbridge']['bias']:.0f} points"
                   + (f", and asked itself it would push with {fb['jev']:.0%} probability, where {fb['people']:.0%} of the "
                      f"visitors said they would" if fb.get("people") is not None else "") + ".",
            evidence=f"{t.height} country-dilemma estimates; mean error by dilemma: "
                     + ", ".join(f"{s} {v['bias']:+.0f} points" for s, v in per.items()),
            numbers={"per": per, "order_jev": order, "order_true": order_t, "self": selfq, "rows": rows}, n=t.height + len(selfq),
            chart={"type": "dots", "domain": [0, 100], "rows": [
                {"label": f"{r['country']} · {r['scen']}", "value": r["jev"], "people": r["true"], "group": r["scen"]}
                for r in sorted(rows, key=lambda r: (["Switch", "Loop", "Footbridge"].index(r["scen"]), -r["true"]))],
                   "x": "share who would sacrifice one (magenta Jev, ink observed)"},
            examples=[x["id"] for x in selfq.values()][:3])
    return spec, run


# ---- 4. the day -----------------------------------------------------------------------------------------------------
BINS = ["none", "m1_29", "m30_59", "h1_2", "h2_3", "h3_5", "h5_8", "h8_10", "h10"]
MID = {"none": 0, "m1_29": 15, "m30_59": 45, "h1_2": 90, "h2_3": 150, "h3_5": 240, "h5_8": 390, "h8_10": 540, "h10": 660}
LABEL = {"none": "none", "m1_29": "under 30 min", "m30_59": "30-59 min", "h1_2": "1-2 h", "h2_3": "2-3 h", "h3_5": "3-5 h",
         "h5_8": "5-8 h", "h8_10": "8-10 h", "h10": "10+ h"}


def _minutes(d: dict) -> float:
    return sum(MID[k] * v for k, v in norm(d).items() if k in MID)


def _day_rows():
    day, ideal = {}, {}
    for r in with_meta("atus_day"):
        m = r["m"]
        if m.get("frame") == "americans":
            h = biggest(r["humans"])
            day[m["activity"]] = {"id": r["id"], "text": r["text"], "jev": robust(r), "people": norm(h["dist"]) if h else None,
                                  "mean": m["mean_minutes"]}
        elif m.get("frame") == "ideal":
            ideal[m["activity"]] = {"id": r["id"], "jev": robust(r), "americans": m["americans_mean_minutes"]}
    return day, ideal


def typical_day():
    spec = Spec(
        id="world_typical_day", family="world", title="A random American's day, as Jev pictures it",
        question="Pick an American at random on a random day: how long did they sleep, work, watch TV, exercise? Does "
                 "Jev's picture of that day match 181,000 time diaries?",
        why="Time-use diaries are the least flattering mirror of daily life: most people don't work on a given day, most "
            "don't exercise, and TV takes more time than anything but sleep and work. A model's picture of 'a day' shows "
            "whether it knows the diary or the brochure.",
        sourcing="New questions (sources/atus_day): for 20 activities, 'Pick an American aged 15 or older at random, on a "
                 "random day of the year. How much time did they spend <activity> that day?' in 9 bins (none to 10+ "
                 "hours). The human distribution is the weighted share of ATUS diary days (2003-2016) in each bin.",
        collection="20 new questions, each asked as written and with the bins in shuffled orders (averaged).",
        scoring="Per activity: Jev's share on 'none' vs the diaries' (how often the activity doesn't happen at all), "
                "expected minutes from bin midpoints vs the diaries' weighted mean, and similarity of the distributions; "
                "the activities Jev most over- and under-states.",
        chart="Paired rows per activity: minutes per day, diaries (ink) and Jev (magenta), with the share of days at zero.",
        compared_with="American Time Use Survey diary days, 2003-2016 (BLS; weighted)",
        limits="The diaries end in 2016; screen time has grown since. Bin midpoints make minute estimates rough; the "
               "zero shares are exact. Diary categories are narrow: 'relaxing and thinking' (ATUS 120301) and 'phone calls, "
               "mail and email' (16) count only time coded as that main activity, which Jev's broader reading can't know.", new_questions=20, sources=["atus_day"])

    def run():
        day, _ = _day_rows()
        rows = []
        for k, d in day.items():
            if d["people"] is None:
                continue
            rows.append({"id": d["id"], "activity": k, "jev_min": _minutes(d["jev"]), "true_min": d["mean"],
                         "jev_zero": d["jev"].get("none", 0.0), "true_zero": d["people"].get("none", 0.0),
                         "sim": 1 - jsd(d["jev"], d["people"])})
        t = pl.DataFrame(rows).with_columns((pl.col("jev_min") - pl.col("true_min")).alias("gap"),
                                            (pl.col("jev_zero") - pl.col("true_zero")).alias("zgap"))
        over, under = t.sort("gap", descending=True).head(3).to_dicts(), t.sort("gap").head(3).to_dicts()
        zmiss = t.sort("zgap").head(3).to_dicts()
        f = lambda r: f"{r['activity']} ({r['jev_min']:.0f} vs {r['true_min']:.0f} min)"  # noqa: E731
        z = lambda r: f"{r['activity']} ({r['jev_zero']:.0%} vs {r['true_zero']:.0%})"  # noqa: E731
        rho = spearmanr(t["jev_min"], t["true_min"]).statistic
        return Result(
            result=f"Jev orders the day's activities {agree_word(rho)} like the diaries (rank correlation {rho:.2f}), but "
                   f"it overstates {and_list([f(r) for r in over])} and understates {and_list([f(r) for r in under])}. "
                   f"It pictures every day as containing everything: the share of days with none of an activity is "
                   f"{and_list([z(r) for r in zmiss])} (Jev vs diaries).",
            evidence=f"20 activities, 181,335 diary days; mean similarity of the distributions {t['sim'].mean():.2f}",
            numbers={"rows": rows, "rho": rho}, n=t.height,
            chart={"type": "dots", "rows": [{"label": r["activity"], "value": r["jev_min"], "people": r["true_min"],
                                             "right": f"{r['true_zero']:.0%} none"} for r in sorted(rows, key=lambda r: -r["true_min"])],
                   "x": "minutes per day (magenta Jev, ink diaries)"},
            examples=[over[0]["id"], zmiss[0]["id"]])
    return spec, run


def ideal_day():
    spec = Spec(
        id="world_ideal_day", family="world", title="Jev's ideal day vs the average American's real one",
        question="Asked how it would spend an ideal day, how much time does Jev give to sleep, work, reading, TV and "
                 "exercise, compared with how Americans actually spend theirs?",
        why="An ideal day is a compact self-portrait: what it would do more of, what it would drop. The gap from the "
            "diaries is the gap between aspiration and habit, the thing people report about themselves too.",
        sourcing="New questions (sources/atus_day): 'On an ideal day for you, how much time would you spend <activity>?' "
                 "for the same 20 activities and 9 bins. Compared with the ATUS diaries' weighted means (no human data "
                 "on ideal days).",
        collection="20 new questions (self), each asked as written and with the bins in shuffled orders (averaged).",
        scoring="Expected minutes per activity from bin midpoints; the difference from the diaries' mean; the total of "
                "Jev's ideal day in hours (a check that it adds up to about 24).",
        chart="Two stacked 24-hour bars, the diaries' average day and Jev's ideal day, colored by activity.",
        compared_with="American Time Use Survey diary days, 2003-2016 (actual, not ideal, days)",
        limits="Ideal vs actual is not like for like; the comparison says where Jev's ideal departs from real life, not "
               "what Americans would call ideal. Activities overlap little but the bins are coarse.", new_questions=20,
        sources=["atus_day"])

    def run():
        _, ideal = _day_rows()
        rows = [{"id": v["id"], "activity": k, "ideal": _minutes(v["jev"]), "actual": v["americans"]} for k, v in ideal.items()]
        t = pl.DataFrame(rows).with_columns((pl.col("ideal") - pl.col("actual")).alias("gap"))
        more, less = t.sort("gap", descending=True).head(3).to_dicts(), t.sort("gap").head(3).to_dicts()
        total = float(t["ideal"].sum()) / 60
        f = lambda r: f"{r['activity']} ({r['ideal'] / 60:.1f} h vs {r['actual'] / 60:.1f} h)"  # noqa: E731
        return Result(
            result=f"Jev's ideal day has more {and_list([f(r) for r in more])} and less {and_list([f(r) for r in less])} "
                   f"than the average American's real day (ideal vs actual). Its 20 activities add up to {total:.0f} hours.",
            evidence="20 activities; Americans' means from 181,335 ATUS diary days",
            numbers={"rows": rows, "total_hours": total}, n=t.height,
            chart={"type": "bars2", "labels": [r["activity"] for r in sorted(rows, key=lambda r: -r["actual"])],
                   "a": [round(r["actual"] / 60, 2) for r in sorted(rows, key=lambda r: -r["actual"])],
                   "b": [round(r["ideal"] / 60, 2) for r in sorted(rows, key=lambda r: -r["actual"])],
                   "a_label": "Americans' actual day (hours)", "b_label": "Jev's ideal day (hours)"},
            examples=[more[0]["id"], less[0]["id"]])
    return spec, run


EXPERIMENTS = [ladder(), wallets(), trolley(), typical_day(), ideal_day()]
