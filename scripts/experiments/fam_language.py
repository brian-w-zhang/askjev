"""Language experiments on new questions (docs/16 pass 3, round 2): what words imply (scalar implicature), which
headline gets the click (Upworthy A/B tests), how bad a health state is (US EQ-5D-5L value set), and color names from
hex codes (a documented weak spot)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, boot, js, norm, seeded, top, with_meta


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes (same keys, different order)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = set().union(*ds)
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def truth(r: dict):
    t = r["truth"]
    return js(t) if isinstance(t, str) else t


def p_yes(r: dict, col: str = "jev_dist") -> float | None:
    d = norm(js(r[col]) or {})
    return d.get("true") if d else None


# ---- 1. scalar implicature --------------------------------------------------------------------------------------------
def implicature():
    spec = Spec(
        id="language_implicature", family="language", title="Does 'good' mean 'not excellent'?",
        question="When someone says the food is 'good', do you conclude they think it's not excellent? People draw "
                 "that inference for some word pairs and not others; does Jev draw it for the same ones?",
        why="'Scalar diversity' is one of the best-documented facts in pragmatics: 'some' almost always implies 'not "
            "all', 'pretty' almost never implies 'not beautiful'. Reading what people mean beyond what they say is what "
            "a language model is for, and here there are exact human rates per word pair.",
        sourcing="New questions (sources/scalar_implicature): 'Mary says: \"The food is good.\" Would you conclude "
                 "from this that, according to Mary, the food is not excellent?' for 43 scales from van Tiel et al. "
                 "2016 (three sentences each, as in the study), 70 from Gotzner et al. 2018 and 50 from Pankratz & van "
                 "Tiel 2021, each with the study's share of people who said yes.",
        collection="234 new yes/no questions, each asked as written and for 'most people'.",
        scoring="Per scale (van Tiel's three sentences averaged), Jev's probability of yes vs people's rate: rank "
                "correlation with a 90% bootstrap interval, mean level, and spread across scales (does Jev show the "
                "diversity, or one rate for everything?). By word class (adjectives vs verbs and quantifiers). The "
                "scales with the biggest gaps. Jev's 'most people' answer is scored the same way.",
        chart="A scatter: people's rate (x) vs Jev's probability (y), one dot per scale, colored by study, diagonal, "
              "with the largest gaps labeled.",
        compared_with="Participants in van Tiel et al. 2016, Gotzner et al. 2018 and Pankratz & van Tiel 2021",
        limits="Rates were collected in different studies with different participant pools; each is one number per "
               "scale. van Tiel's three sentences share one human rate. The question asks for an inference that "
               "people may draw but not endorse, and Jev answers the literal question (a documented tendency, 01-jev §6 "
               "item 1).", new_questions=234, sources=["scalar_implicature"])

    def run():
        rows = []
        for r in with_meta("scalar_implicature"):
            j = p_yes(r)
            if j is None:
                continue
            rows.append({"id": r["id"], "study": r["m"]["study"], "scale": r["m"]["scale"], "cls": r["m"].get("word_class", "adjective"),
                         "jev": j, "guess": p_yes(r, "people_dist"), "people": r["m"]["rate"]})
        t = pl.DataFrame(rows).group_by("study", "scale", "cls").agg(
            pl.col("jev").mean(), pl.col("guess").mean(), pl.col("people").first(), pl.col("id").first())
        rho = spearmanr(t["jev"], t["people"]).statistic
        rho_g = spearmanr(t["guess"].fill_null(0.5), t["people"]).statistic
        idx = np.arange(t.height)
        ci = boot(idx, stat=lambda ii: spearmanr(t["jev"].to_numpy()[ii.astype(int)], t["people"].to_numpy()[ii.astype(int)]).statistic, b=300)
        sd_j, sd_p = float(t["jev"].std()), float(t["people"].std())
        by = t.with_columns(pl.when(pl.col("cls") == "adjective").then(pl.lit("adjectives")).otherwise(pl.lit("verbs and quantifiers")).alias("c")) \
              .group_by("c").agg(pl.col("jev").mean(), pl.col("people").mean(), pl.len()).sort("c").to_dicts()
        t = t.with_columns((pl.col("jev") - pl.col("people")).alias("gap"))
        over, under = t.sort("gap", descending=True).head(3).to_dicts(), t.sort("gap").head(3).to_dicts()
        f = lambda r: f"{r['scale'].replace('/', ' → not ')} ({r['jev']:.0%} vs {r['people']:.0%})"  # noqa: E731
        adj = next(b for b in by if b["c"] == "adjectives")
        oth = next((b for b in by if b["c"] != "adjectives"), None)
        return Result(
            result=f"Across {t.height} word pairs, Jev's yes-rate tracks people's {agree_word(rho)} (rank correlation "
                   f"{rho:.2f}); on average it says yes {t['jev'].mean():.0%} of the time, people "
                   f"{t['people'].mean():.0%}, and its answers spread {'more' if sd_j > sd_p else 'less'} across pairs "
                   f"(SD {sd_j:.2f} vs {sd_p:.2f})."
                   + (f" Like people it draws the inference more for verbs and quantifiers ({oth['jev']:.0%}; people "
                      f"{oth['people']:.0%}) than for adjectives ({adj['jev']:.0%}; people {adj['people']:.0%})."
                      if oth and oth["jev"] > adj["jev"] else
                      f" Unlike people it does not draw the inference more for verbs and quantifiers ({oth['jev']:.0%} vs "
                      f"{adj['jev']:.0%} for adjectives; people {oth['people']:.0%} vs {adj['people']:.0%}; only "
                      f"{oth['len']} such scales)." if oth else "")
                   + f" Its biggest overreach: {f(over[0])}; its biggest miss: {f(under[0])} (Jev vs people).",
            evidence=f"{t.height} scales from 3 studies; 90% interval on the rank correlation {ci[0]:.2f} to {ci[1]:.2f}; "
                     f"Jev's 'most people' answers: rank correlation {rho_g:.2f}",
            numbers={"rho": rho, "ci90": ci, "rho_guess": rho_g, "sd_jev": sd_j, "sd_people": sd_p, "by_class": by,
                     "over": over, "under": under}, n=t.height,
            chart={"type": "scatter", "points": t.select("people", "jev").to_numpy().round(3).tolist(),
                   "labels": [{"label": r["scale"], "x": r["people"], "y": r["jev"]} for r in over[:3] + under[:3]],
                   "x": "people who drew the inference", "y": "Jev's probability of yes", "diagonal": True, "domain": [0, 1]},
            examples=[over[0]["id"], under[0]["id"]])
    return spec, run


# ---- 2. Upworthy headlines --------------------------------------------------------------------------------------------
def headlines():
    spec = Spec(
        id="language_headlines", family="language", title="Which headline got more clicks?",
        question="Given two headlines Upworthy tested on the same story, can Jev tell which one readers clicked more, "
                 "and does it get better when the real difference was bigger?",
        why="Headline tests are the cleanest record of what makes people click: same story, same image, randomized "
            "readers. A model that writes headlines should know which ones work; and where the difference was noise, "
            "it should be at a coin flip.",
        sourcing="New questions (sources/upworthy_headlines): 600 pairs from the Upworthy Research Archive (Matias et "
                 "al. 2021, CC BY 4.0), two versions of the same test with the same image, each shown to 1,000+ "
                 "readers, one pair per test, 200 in each third of the click gap. Tests touching politics were dropped.",
        collection="600 new questions, each asked with the headlines in both orders (averaged).",
        scoring="Share of pairs where Jev's pick (averaged over both orders) is the headline with the higher click-through "
                "rate, by band of click gap and for gaps that clear a two-proportion z-test (|z| > 1.96), each with a "
                "90% bootstrap interval; how often Jev picks the longer headline; how often the first-listed one.",
        chart="Bars: agreement with the winner by click-gap band and for significant gaps, with a 50% line.",
        compared_with="Upworthy's readers in 2013-2015 (randomized tests, clicks per version)",
        limits="Clicks measure curiosity, not quality; readers were Upworthy's audience of the time. Many small gaps are "
               "noise, which is why the bands and the significance cut are reported.", new_questions=600,
        sources=["upworthy_headlines"])

    def run():
        rows = []
        for r in with_meta("upworthy_headlines"):
            j = robust(r)
            opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
            longer = "headline_a" if len(opts["headline_a"]) > len(opts["headline_b"]) else "headline_b"
            first = []
            for d, order in [(norm(js(r["jev_dist"])), list(opts))] + [
                    (norm(v["dist"]), (v.get("params") or {}).get("order")) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle"]:
                if order:
                    first.append(d.get(order[0], 0))
            rows.append({"id": r["id"], "right": j.get(truth(r), 0) > 0.5, "band": r["m"]["band"], "sig": r["m"]["z"] > 1.96,
                         "longer": j.get(longer, 0) > 0.5, "longer_wins": truth(r) == longer,
                         "first": float(np.mean(first)) if first else None})
        t = pl.DataFrame(rows)
        by = [{"label": b, **{k: v for k, v in zip(("right", "n"), (float(g["right"].mean()), g.height))},
               "ci": boot(g["right"].cast(float).to_numpy())} for b in ("small", "medium", "large") for g in [t.filter(pl.col("band") == b)]]
        sig = t.filter(pl.col("sig"))
        a_sig = float(sig["right"].mean())
        return Result(
            result=f"On headline pairs where the click gap clears the noise, Jev picks the winner {a_sig:.0%} of the time "
                   f"({sig.height} pairs). On the smaller two thirds of gaps, mostly noise, it is at a coin flip "
                   f"({by[0]['right']:.0%} and {by[1]['right']:.0%}); on the largest third, {by[2]['right']:.0%}.",
            evidence=f"{t.height} shown pairs (the screen hid the rest of 600); it picks the longer headline "
                     f"{t['longer'].mean():.0%} of the time, the longer one won {t['longer_wins'].mean():.0%}; 90% interval for significant gaps {boot(sig['right'].cast(float).to_numpy())}; "
                     f"Jev's average weight on the first-listed headline {t['first'].mean():.0%}",
            numbers={"by_band": by, "significant": a_sig, "n_sig": sig.height, "longer": float(t["longer"].mean()),
                     "longer_wins": float(t["longer_wins"].mean()), "first": float(t["first"].mean())}, n=t.height,
            chart={"type": "bars", "rows": [{"label": f"{b['label']} gap", "value": b["right"], "ci": b["ci"]} for b in by]
                   + [{"label": "significant gaps", "value": a_sig, "ci": boot(sig["right"].cast(float).to_numpy())}],
                   "domain": [0, 1], "note": "50% = coin flip"},
            robustness="Each pair is asked in both orders and averaged, so the first-listed position can't decide it.",
            examples=seeded(sig.filter(~pl.col("right"))["id"].to_list(), "upworthy", 2))
    return spec, run


# ---- 3. health states -------------------------------------------------------------------------------------------------
TTO_KEYS = ["worse"] + [f"y{y:02d}" for y in range(11)]
DIMS = [("MO", "walking about"), ("SC", "washing or dressing"), ("UA", "usual activities"),
        ("PD", "pain or discomfort"), ("AD", "anxiety or depression")]
US5 = {"MO": 0.322, "SC": 0.261, "UA": 0.255, "PD": 0.414, "AD": 0.321}  # value set decrement at level 5


def _tto_value(d: dict) -> float:
    """Expected utility from Jev's answer: y_k = k/10; 'worse than dying now' counted as -0.2 (the value set's
    worse-than-dead states average about that)."""
    d = norm(d)
    return sum((-0.2 if k == "worse" else int(k[1:]) / 10) * v for k, v in d.items())


def health_tto():
    spec = Spec(
        id="language_health_tto", family="language", title="Worse than being dead?",
        question="Asked the way health economists ask people (10 years in a health state, then death: how many years "
                 "of full health would be as good?), does Jev value health states like Americans do, and does it ever "
                 "say a state is worse than dying now?",
        why="These valuations decide which treatments health systems pay for. People rate pain and depression as worse "
            "than being unable to walk, and they call some states worse than death. Whether a model weighs the same "
            "things is a question about its values, with real stakes.",
        sourcing="New questions (sources/health_states): the time-trade-off question for 143 health states described "
                 "on the five EQ-5D dimensions (level wording paraphrased), spread evenly over the US value set's "
                 "answers (Pickard et al. 2019: 1,134 US adults), including 13 worse than being dead.",
        collection="143 new questions, each asked as written, for 'most people', and with the answers shuffled (averaged).",
        scoring="Jev's expected utility (its answer in years / 10; 'worse than dying now' counted as -0.2) vs the value "
                "set: rank correlation, mean gap, how often each says 'worse than dead'. A least-squares fit of Jev's "
                "utilities on the five dimensions' levels gives its weights, compared with the value set's decrement "
                "at the worst level of each dimension.",
        chart="Dots per dimension: how much the worst level costs (utility points), people vs Jev.",
        compared_with="The US EQ-5D-5L value set (Pickard et al. 2019)",
        limits="The value set is a model fitted to people's answers, not raw answers; it is the population average. "
               "The -0.2 used for Jev's 'worse than dead' affects the mean gap, not the ranks.", new_questions=143,
        sources=["health_states"])

    def run():
        rows = []
        for r in with_meta("health_states"):
            if r["m"].get("set") != "tto":
                continue
            j = robust(r)
            rows.append({"id": r["id"], "state": r["m"]["state"], "u": r["m"]["utility"], "jev": _tto_value(j),
                         "jev_worse": j.get("worse", 0), "guess": _tto_value(js(r["people_dist"]) or {"y05": 1})})
        t = pl.DataFrame(rows)
        rho = spearmanr(t["jev"], t["u"]).statistic
        X = np.array([[1.0] + [1.0 if int(s[i]) == lv else 0.0 for i in range(5) for lv in (2, 3, 4, 5)] for s in t["state"]])
        coef, *_ = np.linalg.lstsq(X, t["jev"].to_numpy(), rcond=None)
        w5 = {d: float(-coef[1 + 4 * i + 3]) for i, (d, _) in enumerate(DIMS)}
        top_j = max(w5, key=w5.get)
        names = dict(DIMS)
        worse_j = float((t["jev_worse"] > 0.5).mean())
        worse_p = float((t["u"] < 0).mean())
        gap = (t["jev"] - t["u"]).to_numpy()
        return Result(
            result=f"Jev orders health states {agree_word(rho)} like Americans (rank correlation {rho:.2f}) but values "
                   f"them {'higher' if gap.mean() > 0 else 'lower'} by {abs(gap.mean()):.2f} on average. It calls "
                   f"{worse_j:.0%} of the states worse than dying now; the value set puts {worse_p:.0%} of them there. Fitted to "
                   f"its answers, the worst level of each dimension costs: "
                   + and_list([f"{names[d]} {w5[d]:.2f} (people {US5[d]:.2f})" for d, _ in sorted(DIMS, key=lambda x: -US5[x[0]])])
                   + f". It weighs {names[top_j]} most; people weigh pain.",
            evidence=f"{t.height} states; 90% interval on the mean gap {boot(gap)}; Jev's 'most people' answers: rank "
                     f"correlation {spearmanr(t['guess'], t['u']).statistic:.2f}",
            numbers={"rho": rho, "mean_gap": float(gap.mean()), "worse_jev": worse_j, "worse_people": worse_p,
                     "weights_jev": w5, "weights_people": US5}, n=t.height,
            chart={"type": "dots", "domain": [0, 0.8], "rows": [{"label": names[d], "value": round(w5[d], 3), "people": US5[d]}
                                                               for d, _ in sorted(DIMS, key=lambda x: -US5[x[0]])],
                   "x": "utility lost at the worst level"},
            examples=seeded(t.sort((pl.col("jev") - pl.col("u")).abs(), descending=True).head(6)["id"].to_list(), "tto", 2))
    return spec, run


def health_pairs():
    spec = Spec(
        id="language_health_pairs", family="language", title="Which health state is worse?",
        question="Given two health states, does Jev pick the one Americans value lower, and how much does that depend "
                 "on how far apart they are?",
        why="The direct comparison is easier than putting a number on a state; if Jev still disagrees with people, it "
            "weighs pain, mobility and mood differently, not just reads the scale differently.",
        sourcing="New questions (sources/health_states): 150 random pairs of EQ-5D-5L states, 50 each with a utility "
                 "gap under 0.1, 0.1-0.3 and over 0.3 in the US value set (Pickard et al. 2019).",
        collection="150 new questions, each asked with the states in both orders (averaged).",
        scoring="Share where Jev's pick (averaged over both orders) is the state with the lower utility, by gap band with "
                "90% bootstrap intervals; for misses, which dimension the state Jev called worse was worse on.",
        chart="Bars: agreement by gap band.",
        compared_with="The US EQ-5D-5L value set (Pickard et al. 2019)",
        limits="Small gaps (under 0.1) are within the value set's own uncertainty.", new_questions=150,
        sources=["health_states"])

    def run():
        rows, miss_dims = [], {}
        for r in with_meta("health_states"):
            if r["m"].get("set") != "pair":
                continue
            j = robust(r)
            right = j.get(truth(r), 0) > 0.5
            rows.append({"id": r["id"], "band": r["m"]["band"], "right": right})
            if not right:  # the state Jev called worse: on which dimensions is it worse than the other?
                picked, other = (r["m"]["a"], r["m"]["b"]) if truth(r) == "state_b" else (r["m"]["b"], r["m"]["a"])
                for i, (d, _) in enumerate(DIMS):
                    if int(picked[i]) > int(other[i]):
                        miss_dims[d] = miss_dims.get(d, 0) + 1
        t = pl.DataFrame(rows)
        by = [{"label": b, "right": float(g["right"].mean()), "n": g.height, "ci": boot(g["right"].cast(float).to_numpy())}
              for b in ("small", "medium", "large") for g in [t.filter(pl.col("band") == b)]]
        names = dict(DIMS)
        n_miss = int((~t["right"]).sum())
        top_d = sorted(miss_dims.items(), key=lambda x: -x[1])[:2]
        return Result(
            result=f"Jev picks the state Americans value lower {t['right'].mean():.0%} of the time: {by[0]['right']:.0%} "
                   f"when the two are close (gap under 0.1), {by[1]['right']:.0%} for middling gaps and "
                   f"{by[2]['right']:.0%} for large ones."
                   + (f" In its {n_miss} misses, the state it calls worse is often the one with worse "
                      + and_list([f"{names[d]} ({c})" for d, c in top_d]) + "." if top_d else ""),
            evidence=f"{t.height} pairs; 90% interval {boot(t['right'].cast(float).to_numpy())}",
            numbers={"by_band": by, "miss_dims": miss_dims}, n=t.height,
            chart={"type": "bars", "rows": [{"label": f"gap {lab}", "value": b["right"], "ci": b["ci"]}
                                            for b, lab in zip(by, ("under 0.1", "0.1-0.3", "over 0.3"))], "domain": [0, 1]},
            examples=seeded(t.filter(~pl.col("right"))["id"].to_list(), "hpairs", 2))
    return spec, run


# ---- 4. hex colors (known limit) --------------------------------------------------------------------------------------
def hex_colors():
    spec = Spec(
        id="language_hex_colors", family="language", title="Name that hex code",
        question="Given a color as a hex code (#fffe40) and four names from the xkcd color survey, how often does Jev "
                 "pick the survey's name, and does it fall for the nearest similar color?",
        why="TypeSafe documents raw hex and RGB values as a weak spot (01-jev §6 item 2). This puts a number on it with "
            "a crowd-sourced answer key, and separates 'no idea of the color' from 'right family, wrong shade'.",
        sourcing="New questions (sources/xkcd_colors): 150 of the 949 colors in the xkcd color survey (CC0), each with "
                 "its survey name, the nearest other survey color at least 40 RGB units away, and two far ones.",
        collection="150 new questions, each asked with the names in three shuffled orders (averaged).",
        scoring="Share where Jev's top name is the survey's (chance 25%), with a 90% bootstrap interval; share of "
                "misses that go to the near distractor (right family) vs the far ones.",
        chart="Bars: survey name, near distractor, far distractors, as shares of Jev's picks.",
        compared_with="The xkcd color survey's names (about 222,500 people naming colors)",
        limits="Known limit, not a discovery (01-jev §6 item 2). The near distractor can be a genuinely close shade.",
        new_questions=150, sources=["xkcd_colors"])

    def run():
        rows = []
        for r in with_meta("xkcd_colors"):
            j = robust(r)
            pick = top(j)
            near = r["m"]["near"].replace("'", "").replace("/", "_").replace(" ", "_")
            rows.append({"id": r["id"], "kind": "survey" if pick == truth(r) else "near" if pick == near else "far",
                         "p_true": j.get(truth(r), 0)})
        t = pl.DataFrame(rows)
        share = {k: float((t["kind"] == k).mean()) for k in ("survey", "near", "far")}
        return Result(
            result=f"Given a hex code, Jev picks the survey's name for the color {share['survey']:.0%} of the time "
                   f"(chance is 25%), and every miss goes to the nearest similar shade, never to a far color "
                   f"({share['near']:.0%} near, {share['far']:.0%} far). Hex codes are a weak spot TypeSafe documents "
                   "(01-jev §6); this measures it.",
            evidence=f"{t.height} colors; 90% interval {boot((t['kind'] == 'survey').cast(float).to_numpy())}",
            numbers={"share": share}, n=t.height,
            chart={"type": "bars", "rows": [{"label": lab, "value": share[k]} for k, lab in
                                            (("survey", "the survey's name"), ("near", "nearest similar color"),
                                             ("far", "a far color"))], "domain": [0, 1]},
            examples=seeded(t.filter(pl.col("kind") == "far")["id"].to_list(), "hex", 2))
    return spec, run


EXPERIMENTS = [implicature(), headlines(), health_tto(), health_pairs(), hex_colors()]
