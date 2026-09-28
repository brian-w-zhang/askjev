"""Recall experiments on new questions (round 3): knowing how widely a fact is known (Tauber et al. 2013 norms, the
NSF science-literacy items) and mental maps (which city is farther north or west)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, boot, js, norm, with_meta

EDGES = [0, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # sources/recall_norms bins
MID = {f"r{a:02d}": (a + b) / 2 for a, b in zip(EDGES, EDGES[1:])}
SHARE_MID = {f"s{v:02d}": v + 5 for v in range(0, 100, 10)}  # sources/science_literacy bins


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes (same keys, different order)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def expect(d: dict, mid: dict) -> float:
    return sum(mid[k] * v for k, v in d.items() if k in mid) / (sum(v for k, v in d.items() if k in mid) or 1)


def truth(r: dict):
    t = r["truth"]
    return js(t) if isinstance(t, str) else t


# ---- 1. how many people know it -------------------------------------------------------------------------------------
def who_knows():
    spec = Spec(
        id="recall_who_knows", family="recall", title="Does Jev know which facts people don't know?",
        question="Shown a general-knowledge question and its answer, can Jev tell what share of US college students "
                 "came up with that answer unaided, from 'zebra' (93%) to facts almost nobody recalls?",
        why="Knowing a fact is one thing; knowing that most people don't is what makes an explanation pitched right. A "
            "model that knows everything may assume everyone does.",
        sourcing="New questions (sources/recall_norms): the 299 questions of Tauber et al. 2013, each shown with its "
                 "answer, asking what share of the students recalled it, in 12 bins (0-2%, 2-5%, 5-10%, then 10-point "
                 "steps). Truth: the share of about 670 US college students who recalled it with no answer choices. The "
                 "per-item shares are a public transcription of the paper's table, checked against the German update's "
                 "reprint of the ranks (Spearman 0.99).",
        collection="299 new questions, each asked as written, for 'most people', and with the bins in three shuffled "
                   "orders (averaged).",
        scoring="Jev's expected share (bin midpoints) vs the real share: rank correlation with a 90% bootstrap "
                "interval; mean gap by third of the real share (rarely, sometimes, usually recalled); the questions "
                "with the largest gaps each way. As a check, the rank correlation with the German 2020 shares for the "
                "same questions.",
        chart="A scatter: real share (x) vs Jev's estimate (y), diagonal, the largest misses labeled.",
        compared_with="US college students, 2012 (Tauber et al. 2013)",
        limits="The students are one population (US college students, 2012); 'recall' means producing the answer with "
               "no options, which is harder than recognizing it. The answer is shown to Jev, so this measures its sense "
               "of how common the knowledge is, not its knowledge.", new_questions=299, sources=["recall_norms"])

    def run():
        rows = []
        for r in with_meta("recall_norms"):
            m = r["m"]
            rows.append({"id": r["id"], "q": r["text"].split('"')[1] if '"' in r["text"] else r["text"],
                         "answer": m.get("answer"), "real": 100 * m["recall_2012"], "jev": expect(robust(r), MID),
                         "german": 100 * m["german_2020"] if m.get("german_2020") is not None else None})
        t = pl.DataFrame(rows)
        rho = spearmanr(t["jev"], t["real"]).statistic
        idx = np.arange(t.height)
        ci = boot(idx, stat=lambda ii: spearmanr(t["jev"].to_numpy()[ii.astype(int)], t["real"].to_numpy()[ii.astype(int)]).statistic, b=300)
        t = t.with_columns((pl.col("jev") - pl.col("real")).alias("gap"))
        cuts = t["real"].quantile(1 / 3), t["real"].quantile(2 / 3)
        thirds = []
        for lab, g in (("rarely recalled", t.filter(pl.col("real") <= cuts[0])),
                       ("sometimes", t.filter((pl.col("real") > cuts[0]) & (pl.col("real") <= cuts[1]))),
                       ("usually recalled", t.filter(pl.col("real") > cuts[1]))):
            thirds.append({"label": lab, "real": float(g["real"].mean()), "jev": float(g["jev"].mean()), "n": g.height,
                           "ci": boot(g["gap"].to_numpy())})
        over = t.sort("gap", descending=True).head(3).to_dicts()
        under = t.sort("gap").head(3).to_dicts()
        tg = t.filter(pl.col("german").is_not_null())
        rho_de = spearmanr(tg["jev"], tg["german"]).statistic if tg.height > 20 else None
        f = lambda r: f"{r['answer']} ({r['jev']:.0f}% vs {r['real']:.0f}%)"  # noqa: E731
        lo = thirds[0]
        return Result(
            result=f"Jev knows which facts are common knowledge {agree_word(rho)} (rank correlation {rho:.2f} with the "
                   f"share of students who recalled them)"
                   + (f", but it thinks the obscure ones are far better known: for the third recalled least (recalled "
                      f"on average by {lo['real']:.0f}% of students) it guesses {lo['jev']:.0f}%. " if lo["jev"] - lo["real"] >= 10 else
                      f"; for the third recalled least (recalled on average by {lo['real']:.0f}% of students) it guesses "
                      f"{lo['jev']:.0f}%. ")
                   + f"It overestimates {and_list([f(r) for r in over])} most, and underestimates "
                   f"{and_list([f(r) for r in under])} (Jev vs students).",
            evidence=f"{t.height} questions; 90% interval on the rank correlation {ci[0]:.2f} to {ci[1]:.2f}",
            numbers={"rho": rho, "ci90": ci, "thirds": thirds, "over": over, "under": under, "rho_german": rho_de}, n=t.height,
            robustness=(f"Against the German 2020 shares for {tg.height} of the same questions the rank correlation is "
                        f"{rho_de:.2f}." if rho_de is not None else ""),
            chart={"type": "scatter", "points": t.select("real", "jev").to_numpy().round(1).tolist(),
                   "labels": [{"label": r["answer"], "x": r["real"], "y": r["jev"]} for r in over + under],
                   "x": "students who recalled it (%)", "y": "Jev's estimate (%)", "diagonal": True, "domain": [0, 100]},
            examples=[over[0]["id"], under[0]["id"]])
    return spec, run


# ---- 2. the public's science knowledge --------------------------------------------------------------------------------
def public_science():
    spec = Spec(
        id="recall_public_science", family="recall", title="Does Jev know what the public gets wrong about science?",
        question="On the science quiz the US has put to adults since 1988 ('antibiotics kill viruses', 'lasers work by "
                 "focusing sound waves'), does Jev know how many people answer correctly, and how that changed?",
        why="Science communication starts from what people already believe. The NSF items are the longest-running "
            "record of it, and some moved a lot (antibiotics: 25% right in 1988, 51% in 2016).",
        sourcing="New questions (sources/science_literacy): 9 items from NSF Science & Engineering Indicators 2018, "
                 "Appendix Table 7-9 (evolution and the big bang left out as religiously contested). Each asked as the "
                 "survey asked it, and as 'what share of US adults answered correctly' in 2016 and in 1988, in 10-point "
                 "bins.",
        collection="26 new questions (9 items, 9 shares for 2016, 8 for 1988), each asked as written, for 'most "
                   "people', and with options in shuffled orders where there are options (averaged).",
        scoring="Jev's own answers vs the key; its estimated share correct (bin midpoints) vs the real share, per item "
                "and year; the change it expects from 1988 to 2016 vs the real change.",
        chart="A dumbbell per item: the real share correct in 1988 and 2016, with Jev's two estimates beside them.",
        compared_with="US adults: NSF surveys 1988 (n=2,041) and the General Social Survey 2016 (n=1,390)",
        limits="Nine items; 'don't know' counts as incorrect in the real shares. The answer is shown in the share "
               "questions.", new_questions=26, sources=["science_literacy"])

    def run():
        items, shares = {}, {}
        for r in with_meta("science_literacy"):
            m = r["m"]
            if m["set"] == "item":
                d = robust(r) if r["primitive"] != "noul" else norm(js(r["jev_dist"]))
                t = truth(r)
                key = ("true" if t else "false") if isinstance(t, bool) else t
                items[m["item"]] = {"right": d.get(key, 0.0), "p16": m["pct_2016"], "p88": m.get("pct_1988")}
            else:
                shares.setdefault(m["item"], {})[m["year"]] = (expect(robust(r), SHARE_MID), m["pct"])
        rows = []
        for it, v in items.items():
            s = shares.get(it, {})
            rows.append({"item": it, "right": v["right"], "real16": v["p16"], "jev16": s.get(2016, (None,))[0],
                         "real88": v["p88"], "jev88": s.get(1988, (None,))[0]})
        t = pl.DataFrame(rows)
        known = t.filter(pl.col("jev16").is_not_null())
        gap16 = (known["jev16"] - known["real16"]).to_numpy()
        tr = t.filter(pl.col("jev88").is_not_null() & pl.col("real88").is_not_null())
        change_real = (tr["real16"] - tr["real88"]).to_numpy()
        change_jev = (tr["jev16"] - tr["jev88"]).to_numpy()
        worst = known.with_columns((pl.col("jev16") - pl.col("real16")).alias("g")).sort("g", descending=True).head(2).to_dicts()
        anti = t.filter(pl.col("item") == "antibiotics").to_dicts()
        a = anti[0] if anti else None
        name = {"earth_core": "the Earth's hot center", "continents": "moving continents", "earth_sun": "the Earth "
                "going around the Sun", "year": "a year per orbit", "radioactivity": "natural radioactivity",
                "electrons": "electrons smaller than atoms", "lasers": "lasers and sound", "fathers_gene":
                "the father's gene", "antibiotics": "antibiotics and viruses"}
        right = int((t["right"] > 0.5).sum())
        return Result(
            result=f"Jev answers {'all' if right == t.height else right} {'' if right == t.height else 'of the '}{t.height} items right "
                   f"itself. Its guess of how many US adults got each right is unbiased on average ({gap16.mean():+.0f} "
                   f"points, 90% interval {boot(gap16)[0]:+.0f} to {boot(gap16)[1]:+.0f}), but it overrates "
                   + and_list([f"{name.get(w['item'], w['item'])} ({w['jev16']:.0f}% vs {w['real16']}%)" for w in worst])
                   + f" most. From 1988 to 2016 it expects the scores to change by {round(change_jev.mean()):+d} points on "
                     f"average; they changed by {round(change_real.mean()):+d}"
                   + (f" (antibiotics: Jev {a['jev88']:.0f}% to {a['jev16']:.0f}%, real {a['real88']}% to {a['real16']}%)." if a and a["jev88"] is not None else "."),
            evidence=f"{t.height} items, {known.height} 2016 shares and {tr.height} 1988 shares; 90% interval on the "
                     f"mean 2016 gap {boot(gap16)}",
            numbers={"rows": rows, "gap2016": float(gap16.mean()), "change_real": float(change_real.mean()),
                     "change_jev": float(change_jev.mean())}, n=26,
            chart={"type": "dumbbell", "rows": [{"label": name.get(r["item"], r["item"]), "a": r["real16"], "b": r["jev16"]}
                                                for r in rows if r["jev16"] is not None],
                   "a_label": "real share correct, 2016", "b_label": "Jev's estimate", "domain": [0, 100]})
    return spec, run


# ---- 3. mental maps ---------------------------------------------------------------------------------------------------
def _k(label: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in label.lower()).strip("_")  # sources/mental_maps._key


def _maps() -> pl.DataFrame:
    rows = []
    for r in with_meta("mental_maps"):
        m = r["m"]
        d = robust(r)
        t = truth(r)
        opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
        first = next(k for k, v in opts.items() if v == m["a"])  # the city named first in the question text
        pick = max(d, key=d.get)
        rows.append({"id": r["id"], "set": m["set"], "right": d.get(t, 0.0) > 0.5, "p": d.get(t, 0.0), "a": m["a"],
                     "truth_first": t == first, "pick_first": pick == first,
                     "pick_na": m["set"] == "ns_eu_na" and opts[pick] != m.get("europe"),
                     "b": m["b"], "truth": t, "lat_gap": m["lat_gap"], "lon_gap": m["lon_gap"],
                     "europe_north": m.get("europe_north"), "europe": m.get("europe"), "misleads": m.get("state_misleads"),
                     "text": r["text"]})
    return pl.DataFrame(rows, infer_schema_length=None)


def maps_north():
    spec = Spec(
        id="recall_mental_map_north", family="recall", title="Jev's mental map puts Europe too far south",
        question="Asked which of two cities on different continents is farther north, does Jev share people's classic "
                 "error of placing Europe too far south of North America?",
        why="People's mental maps line Europe up with the US (Rome level with Washington), when Europe actually sits "
            "well north (Friedman & Brown 2000). A model reads maps only through text; whether it inherits the "
            "human distortion is a small window on how it stores geography.",
        sourcing="New questions (sources/mental_maps): 'Which city is farther north: <a> or <b>?' for well-known cities "
                 "(over 1.5 million people, or national capitals), from GeoNames coordinates: European vs North "
                 "American pairs 0.5-6 degrees apart, pairs across other regions, and US pairs as a control. Truth "
                 "only: no item-level human answers exist for these pairs.",
        collection="362 new questions, each asked with the two cities in both orders (averaged).",
        scoring="For Europe-North America pairs, how often Jev picks the North American city, and the share right when "
                "the European city is the northern one vs when it isn't (the human error predicts misses when Europe is "
                "north); a check that this isn't a lean toward the city named first; US pairs as a control.",
        chart="Bars: share right per set, and for Europe-North America split by which side is north.",
        compared_with="the coordinates (truth); the human pattern is from the literature, not item-level data",
        limits="No human answers to these exact pairs, so the comparison with people is with the published pattern, "
               "not a rate. Cities are identified by name and country (US: state).", new_questions=362,
        sources=["mental_maps"])

    def run():
        t = _maps().filter(pl.col("set") != "ew_us")
        by = t.group_by("set").agg(pl.col("right").mean(), pl.len()).sort("set").to_dicts()
        eu = t.filter(pl.col("set") == "ns_eu_na")
        en, es = eu.filter(pl.col("europe_north")), eu.filter(~pl.col("europe_north"))
        err = eu.filter(~pl.col("right"))
        south_err = float(err["europe_north"].mean()) if err.height else float("nan")
        worst = eu.sort("p").head(3).to_dicts()
        lab = {"ns_eu_na": "Europe vs North America", "ns_other": "other regions", "ns_us": "US vs US"}
        sets = {b["set"]: b for b in by}
        na = float(eu["pick_na"].mean())
        first_eu = float(eu["pick_first"].mean())
        oth = t.filter(pl.col("set") == "ns_other")
        of, os_ = oth.filter(pl.col("truth_first")), oth.filter(~pl.col("truth_first"))
        w0 = worst[0]
        right_c = w0["a"] if w0["truth"] == _k(w0["a"]) else w0["b"]  # the northern city, which Jev rejected
        wrong = w0["b"] if right_c == w0["a"] else w0["a"]
        result = (f"Asked which of a European and a North American city is farther north, Jev picks the North American "
                  f"one {na:.0%} of the time, though the European city is the northern one in "
                  f"{float(eu['europe_north'].mean()):.0%} of the pairs: it is right {float(en['right'].mean()):.0%} when "
                  f"Europe is north and {float(es['right'].mean()):.0%} when it is south. Like people's, its mental map "
                  f"puts Europe too far south: it is {1 - w0['p']:.0%} sure {wrong} is farther north than {right_c}, though "
                  f"{wrong} lies {w0['lat_gap']:.1f} degrees farther south. For two US cities it is right "
                  f"{sets['ns_us']['right']:.0%}.")
        return Result(
            result=result,
            evidence=f"{eu.height} Europe-North America pairs, {t.height} pairs in all; 90% interval on the Europe-North "
                     f"America share right {boot(eu['right'].cast(float).to_numpy())}",
            numbers={"pick_na": na, "pick_first": first_eu, "by_set": by, "europe_north_right": float(en["right"].mean()), "europe_south_right": float(es["right"].mean()),
                     "errors_europe_north": south_err, "worst": worst}, n=t.height,
            robustness=(f"Not an order effect here: Jev picks the city named first in {first_eu:.0%} of the Europe-North "
                        f"America pairs. It is elsewhere: on pairs from other regions it is right {float(of['right'].mean()):.0%} "
                        f"when the northern city is named first and {float(os_['right'].mean()):.0%} when it is named second "
                        f"(recall_mental_map_west). The human pattern is from Friedman & Brown 2000; there are no human "
                        f"answers to these pairs. Surest wrong: "
                        + "; ".join(f"{w['a']} vs {w['b']} ({1 - w['p']:.0%} on the wrong city)" for w in worst[:2]) + "."),
            chart={"type": "bars", "rows": [{"label": lab.get(b["set"], b["set"]), "value": b["right"]} for b in by]
                   + [{"label": "Europe-NA, Europe north", "value": float(en["right"].mean())},
                      {"label": "Europe-NA, Europe south", "value": float(es["right"].mean())}], "domain": [0, 1]},
            examples=[w["id"] for w in worst[:2]],
            ids=t["id"].to_list())
    return spec, run


def maps_west():
    spec = Spec(
        id="recall_mental_map_west", family="recall", title="West of what? Jev picks the city named first",
        question="For two US cities, does Jev judge which is farther west by the city, or by its state, the way people "
                 "do when they place Reno east of Los Angeles because Nevada lies east of California?",
        why="People store places hierarchically and reason from the state (Stevens & Coupe 1978). A model that does the "
            "same will be wrong exactly where the state misleads.",
        sourcing="New questions (sources/mental_maps): 'Which city is farther west: <a> or <b>?' for US cities over "
                 "150,000 people in different states, 0.3-5 degrees of longitude apart: every pair where the city in "
                 "the more western state (by its cities' average longitude) is actually the eastern one, and as many "
                 "ordinary pairs. Truth from GeoNames coordinates; no item-level human data.",
        collection="160 new questions, each asked with the two cities in both orders (averaged).",
        scoring="Share right when the state misleads vs when it doesn't, balanced for whether the western city is "
                "named first in the question; share right by which city is named first, with 90% bootstrap intervals.",
        chart="Bars: share right by which city is named first, and by whether the state misleads.",
        compared_with="the coordinates (truth); the human pattern is from the literature",
        limits="'The state misleads' uses the state's average city longitude, a proxy for where the state sits in the "
               "mind. No human answers to these exact pairs.", new_questions=160, sources=["mental_maps"])

    def run():
        t = _maps().filter(pl.col("set") == "ew_us")
        cell = lambda mis, tf: t.filter((pl.col("misleads") == mis) & (pl.col("truth_first") == tf))["right"]  # noqa: E731
        bal = lambda mis: float((cell(mis, True).mean() + cell(mis, False).mean()) / 2)  # noqa: E731
        am, ao = bal(True), bal(False)
        f1, f2 = float(t.filter(pl.col("truth_first"))["right"].mean()), float(t.filter(~pl.col("truth_first"))["right"].mean())
        worst = t.sort("p").head(3).to_dicts()
        return Result(
            result=f"Which of two US cities is farther west? The state doesn't mislead Jev ({am:.0%} right when it points "
                   f"the wrong way, {ao:.0%} when it doesn't, balanced for order), but the wording does: it is right "
                   f"{f1:.0%} of the time when the western city is named first in the question and {f2:.0%} when it is "
                   f"named second, below a coin flip.",
            evidence=f"{t.height} pairs ({int(t['misleads'].sum())} where the state misleads); 90% intervals, named first "
                     f"{boot(t.filter(pl.col('truth_first'))['right'].cast(float).to_numpy())}, named second "
                     f"{boot(t.filter(~pl.col('truth_first'))['right'].cast(float).to_numpy())}",
            numbers={"misleads_balanced": am, "ordinary_balanced": ao, "named_first": f1, "named_second": f2,
                     "worst": worst}, n=t.height,
            robustness="Swapping the two options' order in the answer list doesn't remove it: the lean follows the order "
                       "in the question sentence, which stayed fixed. No human answers to these pairs exist; the "
                       "state-misleads pattern is from Stevens & Coupe 1978.",
            chart={"type": "bars", "rows": [{"label": "western city named first", "value": f1},
                                            {"label": "western city named second", "value": f2},
                                            {"label": "state misleads (balanced)", "value": am},
                                            {"label": "ordinary pairs (balanced)", "value": ao}], "domain": [0, 1]},
            examples=[w["id"] for w in worst[:2]],
            ids=t["id"].to_list())
    return spec, run


EXPERIMENTS = [who_knows(), public_science(), maps_north(), maps_west()]
