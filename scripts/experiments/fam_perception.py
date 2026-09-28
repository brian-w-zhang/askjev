"""Perception experiments on new questions (docs/13): probability and amount words, names, adjective intensity,
what jobs are like (O*NET), reading implications with 100 people per item (ChaosNLI), funny words."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, jsd, level, norm, seeded, top, with_meta

# ---- shared ----------------------------------------------------------------------------------------------------------
PCT = [f"p{v:03d}" for v in range(0, 101, 5)]


def pct_median(d: dict) -> float:
    """Median of a distribution over the 5%-step keys, in percent."""
    d = norm(d)
    c = 0.0
    for k in PCT:
        c += d.get(k, 0.0)
        if c >= 0.5:
            return float(k[1:])
    return 100.0


def pct_quantile(d: dict, q: float) -> float:
    d = norm(d)
    c = 0.0
    for k in PCT:
        c += d.get(k, 0.0)
        if c >= q:
            return float(k[1:])
    return 100.0


def ordered_median(d: dict, keys: list[str]) -> int:
    """Index of the median bin over ordered keys."""
    d = norm(d)
    c = 0.0
    for i, k in enumerate(keys):
        c += d.get(k, 0.0)
        if c >= 0.5:
            return i
    return len(keys) - 1


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes (same keys, different order)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


PERCEPTION_LIMITS = ("46 people answered the original survey on Reddit's r/samplesize in 2015: a small, online, "
                     "English-speaking sample. Each person gave one number; Jev gives a probability over the bins, and its "
                     "median is compared with theirs.")


# ---- 1. probability words ---------------------------------------------------------------------------------------------
def probability():
    spec = Spec(
        id="perception_probability", family="perception", title="What 'probably' means to Jev",
        question="When someone says 'highly likely', 'we doubt' or 'about even', what probability does Jev read into "
                 "it, and does it read the phrases the way people do?",
        why="Probability words are how forecasts, doctors and intelligence reports talk. A model that reads them "
            "differently from people will mistranslate every hedge in both directions.",
        sourcing="New questions (sources/perception_words): the zonination survey's own wording, 'What probability "
                 "would you assign to the phrase \"<phrase>\"?', for its 17 phrases, answered as 21 ordered bins (0%, "
                 "5%, ..., 100%). Each of the 46 respondents' answers is put in the same bins.",
        collection="17 new questions, each asked as written, for 'most people', and with the bins in three shuffled "
                   "orders (the shuffles are averaged).",
        scoring="Per phrase, the median of Jev's distribution vs the respondents' median; rank correlation of the medians; "
                "the median absolute gap in points; the spread (10th to 90th percentile) of each; similarity of the "
                "two distributions (1 - Jensen-Shannon distance).",
        chart="A ridge chart like the zonination original: one row per phrase, people's distribution as a ridge and "
              "Jev's as a second ridge, ordered by people's median.",
        compared_with="46 Reddit respondents (zonination 2015)", limits=PERCEPTION_LIMITS, new_questions=17,
        sources=["perception_words"])

    def run():
        rows = []
        for r in with_meta("perception_words"):
            if r["m"].get("set") != "probability":
                continue
            h = biggest(r["humans"])
            j = robust(r)
            rows.append({"id": r["id"], "phrase": r["m"]["item"], "jev": pct_median(j), "people": pct_median(h["dist"]),
                         "jev_lo": pct_quantile(j, 0.1), "jev_hi": pct_quantile(j, 0.9),
                         "ppl_lo": pct_quantile(h["dist"], 0.1), "ppl_hi": pct_quantile(h["dist"], 0.9),
                         "guess": pct_median(js(r["people_dist"]) or {}), "sim": 1 - jsd(j, norm(h["dist"])),
                         "jev_dist": j, "ppl_dist": norm(h["dist"])})
        rows.sort(key=lambda x: -x["people"])
        rho = spearmanr([r["jev"] for r in rows], [r["people"] for r in rows]).statistic
        gaps = np.array([r["jev"] - r["people"] for r in rows])
        big = sorted(rows, key=lambda r: -abs(r["jev"] - r["people"]))[:3]
        w_j = np.mean([r["jev_hi"] - r["jev_lo"] for r in rows])
        w_p = np.mean([r["ppl_hi"] - r["ppl_lo"] for r in rows])
        f = lambda r: f"\"{r['phrase'].lower()}\" ({r['jev']:.0f}% vs {r['people']:.0f}%)"  # noqa: E731
        return Result(
            result=f"Jev puts the {len(rows)} phrases in {agree_word(rho)} the same order as people (rank correlation {rho:.2f}), "
                   f"with a median gap of {np.median(np.abs(gaps)):.0f} points. It parts from them most on "
                   f"{and_list([f(r) for r in big])}. Its readings are narrower: the middle 80% of its answer spans "
                   f"{w_j:.0f} points on average, people's {w_p:.0f}.",
            evidence=f"{len(rows)} of the survey's 17 phrases (the screen hid one question), 46 respondents each; "
                     f"90% interval on the mean gap {boot(gaps)} points",
            numbers={"rows": [{k: v for k, v in r.items() if not k.endswith("_dist")} for r in rows], "rho": rho,
                     "median_abs_gap": float(np.median(np.abs(gaps))), "width_jev": w_j, "width_people": w_p},
            n=len(rows), robustness="Medians use Jev's distribution averaged over the base question and three shuffled "
                                    "orders of the bins. Its guess for 'most people' is kept alongside.",
            chart={"type": "ridge", "bins": [int(k[1:]) for k in PCT], "rows": [
                {"label": r["phrase"], "people": [round(r["ppl_dist"].get(k, 0), 3) for k in PCT],
                 "jev": [round(r["jev_dist"].get(k, 0), 3) for k in PCT], "jev_median": r["jev"],
                 "people_median": r["people"]} for r in rows]},
            examples=[r["id"] for r in big])
    return spec, run


def round_trip():
    spec = Spec(
        id="perception_round_trip", family="perception", title="Number to word and back",
        question="Given a probability (0%, 5%, ..., 100%), which phrase does Jev choose for it, and do the phrases "
                 "survive the round trip from word to number and back?",
        why="Reading 'likely' as 70% is half the job; the other half is saying 'likely' when the chance is 70%. A "
            "model that reads well but writes with only a few favorite phrases will flatten every forecast it writes.",
        sourcing="New questions (sources/perception_words): 'An event has a <p>% chance of happening. Which phrase "
                 "describes that chance best?' for each 5% step, with the 17 survey phrases as options. No human data "
                 "exists for this direction.",
        collection="21 new questions, each asked with the phrases in three shuffled orders (averaged).",
        scoring="Per probability, Jev's top phrase. Per phrase, the probabilities where it is Jev's top pick. The round "
                "trip: a phrase's median from the probability experiment, rounded to 5%, then the phrase Jev picks for "
                "that number; a phrase survives when it comes back.",
        chart="A strip from 0% to 100% colored by Jev's chosen phrase, with each phrase's forward median marked above.",
        compared_with="Jev's own forward readings (perception_probability); no human data in this direction",
        limits="Several phrases mean nearly the same thing ('likely', 'probable', 'probably'), so a phrase can lose the "
               "round trip to a near-synonym; the result lists which.", new_questions=21, sources=["perception_words"])

    def run():
        rev, fwd, slug = {}, {}, {}
        for r in with_meta("perception_words"):
            s = r["m"].get("set")
            if s == "reverse":
                rev[int(r["m"]["value"])] = robust(r)
                slug.update(js(r["options"]) if isinstance(r["options"], str) else r["options"])
            elif s == "probability":
                fwd[r["m"]["item"]] = pct_median(robust(r))
        picks = {v: slug[top(d)] for v, d in sorted(rev.items())}
        used = sorted(set(picks.values()), key=lambda p: min(v for v, q in picks.items() if q == p))
        never = [p for p in slug.values() if p not in used]
        trip = {p: picks[int(5 * round(m / 5))] for p, m in fwd.items()}  # phrases with a shown forward question
        survive = [p for p, q in trip.items() if q == p]
        lost = {p: q for p, q in trip.items() if q != p}
        return Result(
            result=f"Asked to put 21 probabilities into words, Jev uses only {len(used)} of the 17 phrases ("
                   f"{and_list([p.lower() for p in used])}). Going from phrase to number and back, {len(survive)} of {len(trip)} "
                   f"come home; " + and_list([f"\"{p.lower()}\" comes back as \"{q.lower()}\"" for p, q in list(lost.items())[:3]])
                   + ".",
            evidence="21 probabilities x 17 phrases, each averaged over three option orders; the round trip covers the "
                     f"{len(trip)} phrases whose forward question is shown (the screen hid the rest)",
            numbers={"picks": picks, "used": used, "never": never, "trip": trip, "survive": survive}, n=21,
            chart={"type": "wordstrip", "values": [{"p": v, "phrase": q} for v, q in picks.items()],
                   "forward": [{"phrase": p, "p": m} for p, m in fwd.items()]},
            examples=[])
    return spec, run


def settings():
    spec = Spec(
        id="perception_settings", family="perception", title="Does 'likely' mean less when it's a side effect?",
        question="Does Jev read the same probability phrase differently in a weather forecast, a doctor's warning about "
                 "side effects, and an intelligence report?",
        why="For people, the same word shifts with the stakes and the base rate of the event (Weber & Hilton 1990). A "
            "model that reads 'likely' identically everywhere is simpler, but not how people talk.",
        sourcing="New questions (sources/perception_words): each of the 17 phrases in three settings, e.g. 'A doctor "
                 "describes the chance that a new medication causes a side effect with the phrase \"likely\". What "
                 "probability does that suggest?', same 21 bins. No human data for the settings.",
        collection="51 new questions, each asked with the bins in three shuffled orders (averaged).",
        scoring="Per phrase and setting, Jev's median minus its median for the bare phrase; mean shift per setting with "
                "a 90% bootstrap interval over phrases; the phrases that move most.",
        chart="A dot plot: one row per phrase, the bare reading and the three settings as colored dots.",
        compared_with="Jev's own reading of the bare phrase (perception_probability)",
        limits="Jev only; the shifts are not compared with people here.", new_questions=51, sources=["perception_words"])

    def run():
        base, by = {}, {}
        for r in with_meta("perception_words"):
            s, p = r["m"].get("set"), r["m"].get("item")
            if s == "probability":
                base[p] = pct_median(robust(r))
            elif s and s.startswith("probability_"):
                by.setdefault(s.split("_", 1)[1], {})[p] = pct_median(robust(r))
        shift = {s: {p: v - base[p] for p, v in d.items() if p in base} for s, d in by.items()}
        mean = {s: (float(np.mean(list(d.values()))), boot(list(d.values()))) for s, d in shift.items()}
        moved = sorted(((abs(v), s, p, v) for s, d in shift.items() for p, v in d.items()), reverse=True)[:3]
        still = float(np.mean([abs(v) for d in shift.values() for v in d.values()]))
        order = sorted(mean.items(), key=lambda x: x[1][0])
        return Result(
            result=f"Jev barely changes its reading with the setting: on average a phrase moves {still:.0f} points; "
                   + "; ".join(f"in {s} it reads phrases {abs(m):.0f} point{'' if round(abs(m)) == 1 else 's'} {'lower' if m < 0 else 'higher'}"
                               for s, (m, _) in order) + ". The biggest moves: "
                   + and_list([f"\"{p.lower()}\" in {s} ({v:+.0f})" for _, s, p, v in moved]) + ".",
            evidence=f"{len(base)} phrases x 3 settings; 90% intervals over phrases: "
                     + "; ".join(f"{s} {ci}" for s, (_, ci) in mean.items()),
            numbers={"base": base, "settings": by, "mean_shift": {s: m for s, (m, _) in mean.items()}}, n=51,
            chart={"type": "dots", "rows": [{"label": p, "value": base[p], "others": {s: by[s].get(p) for s in by}}
                                             for p in sorted(base, key=lambda p: -base[p])], "domain": [0, 100]},
            robustness=f"{len(base)} of 17 phrases: the screen hid the rest of the bare-phrase questions, so their settings "
                       "have nothing to be compared with." if len(base) < 17 else "")
    return spec, run


# ---- 2. amount words --------------------------------------------------------------------------------------------------
AMOUNT = ["n1", "n2", "n3", "n4", "n5", "n6_7", "n8_10", "n11_15", "n16_25", "n26_50", "n51_100", "n101_250",
          "n251_500", "n501_1000", "n1001"]
AMOUNT_LABEL = ["1", "2", "3", "4", "5", "6-7", "8-10", "11-15", "16-25", "26-50", "51-100", "101-250", "251-500",
                "501-1,000", "1,000+"]


def amount():
    spec = Spec(
        id="perception_amount", family="perception", title="How many is 'a few'?",
        question="How many does Jev think 'a couple', 'a few', 'several', 'many', 'dozens', 'scores of' and 'hundreds "
                 "of' are, compared with people?",
        why="Amount words are vaguer than probability words, and some have old literal meanings ('a score' is 20) "
            "that most people no longer use. Which way a model reads them shows whether it goes by the dictionary or "
            "by usage.",
        sourcing="New questions (sources/perception_words): 'What number would you assign to the phrase \"<phrase>\"?' "
                 "for 9 of the survey's 10 phrases ('fractions of' is left out: the bins hold counts), with 15 ordered "
                 "bins from 1 to more than 1,000. Respondents' numbers are put in the same bins.",
        collection="9 new questions, asked as written, for 'most people', and in three shuffled orders (averaged).",
        scoring="Per phrase, the bin holding Jev's median vs the bin holding people's median; rank correlation of the "
                "medians; the phrases where they differ.",
        chart="A ridge chart on a log axis: one row per phrase, people's and Jev's distributions over the bins.",
        compared_with="46 Reddit respondents (zonination 2015)", limits=PERCEPTION_LIMITS, new_questions=9,
        sources=["perception_words"])

    def run():
        rows = []
        for r in with_meta("perception_words"):
            if r["m"].get("set") != "amount":
                continue
            h, j = norm(biggest(r["humans"])["dist"]), robust(r)
            rows.append({"id": r["id"], "phrase": r["m"]["item"].strip(), "jev": ordered_median(j, AMOUNT),
                         "people": ordered_median(h, AMOUNT), "jev_dist": j, "ppl_dist": h})
        rows.sort(key=lambda x: x["people"])
        rho = spearmanr([r["jev"] for r in rows], [r["people"] for r in rows]).statistic
        same = [r for r in rows if r["jev"] == r["people"]]
        diff = sorted([r for r in rows if r["jev"] != r["people"]], key=lambda r: -abs(r["jev"] - r["people"]))
        f = lambda r: f"\"{r['phrase'].lower()}\" ({AMOUNT_LABEL[r['jev']]} vs {AMOUNT_LABEL[r['people']]})"
        return Result(
            result=f"Jev's median lands in the same bin as people's for {len(same)} of {len(rows)} phrases and orders "
                   f"them {agree_word(rho)} like people (rank correlation {rho:.2f})."
                   + (f" It differs on {and_list([f(r) for r in diff])} (Jev vs people)." if diff else ""),
            evidence=f"{len(rows)} phrases, 46 respondents each",
            numbers={"rows": [{k: v for k, v in r.items() if not k.endswith("_dist")} for r in rows], "rho": rho}, n=len(rows),
            chart={"type": "ridge", "bins": AMOUNT_LABEL, "log": True, "rows": [
                {"label": r["phrase"], "people": [round(r["ppl_dist"].get(k, 0), 3) for k in AMOUNT],
                 "jev": [round(r["jev_dist"].get(k, 0), 3) for k in AMOUNT]} for r in rows]},
            examples=[r["id"] for r in diff[:2]])
    return spec, run


def amount_settings():
    spec = Spec(
        id="perception_amount_settings", family="perception", title="Does 'a few' grow with the crowd?",
        question="Does 'a few', 'several' or 'many' mean a bigger number to Jev when the thing counted is bigger (a "
                 "stadium crowd vs a dinner party, grains of rice vs years)?",
        why="People scale vague amounts to what's being counted (many grains of rice is more than many years). "
            "Whether a model does is a simple test of whether it reads words or situations.",
        sourcing="New questions (sources/perception_words): the three words in five settings, e.g. 'Someone says \"A "
                 "few people were at the stadium when the gates opened.\" How many people is that?', same 15 bins. No "
                 "human data for the settings.",
        collection="15 new questions, each in three shuffled orders (averaged).",
        scoring="Per word and setting, the bin of Jev's median; the range from the smallest to the largest setting.",
        chart="Small multiples: one panel per word, the five settings as dots on the log axis.",
        compared_with="Jev's own reading across settings; no human data here",
        limits="Jev only. The settings were chosen to differ in scale by orders of magnitude.", new_questions=15,
        sources=["perception_words"])

    def run():
        grid = {}
        for r in with_meta("perception_words"):
            s = r["m"].get("set", "")
            if s.startswith("amount_"):
                grid.setdefault(r["m"]["item"], {})[s.split("_", 1)[1]] = ordered_median(robust(r), AMOUNT)
        lab = lambda i: AMOUNT_LABEL[i]
        parts = []
        for w in ("A few", "Several", "Many"):
            g = grid.get(w, {})
            lo, hi = min(g, key=g.get), max(g, key=g.get)
            parts.append(f"\"{w.lower()}\" is {lab(g[lo])} in every setting" if g[lo] == g[hi] else
                         f"\"{w.lower()}\" runs from {lab(g[lo])} ({lo}) to {lab(g[hi])} ({hi})")
        spread = sum(max(g.values()) - min(g.values()) for g in grid.values())
        return Result(
            result=("Jev scales vague amounts to the thing counted: " if spread >= 3 else
                    "Jev barely scales vague amounts to the thing counted: ") + "; ".join(parts) + ".",
            evidence="3 words x 5 settings",
            numbers={"grid": {w: {s: lab(i) for s, i in g.items()} for w, g in grid.items()}}, n=15,
            chart={"type": "grid", "rows": [{"label": w, "cells": {s: lab(i) for s, i in g.items()}} for w, g in grid.items()]})
    return spec, run


# ---- 3. names ---------------------------------------------------------------------------------------------------------
SHARE = ["f00", "f10", "f20", "f30", "f40", "f50", "f60", "f70", "f80", "f90", "f100"]
SHARE_MID = {k: (2.5 if k == "f00" else 97.5 if k == "f100" else float(k[1:])) for k in SHARE}


def names_share():
    spec = Spec(
        id="names_share_girls", family="names", title="Jordan, Avery, Riley: boy or girl?",
        question="For names given to both boys and girls, how well does Jev know what share of US babies with the name "
                 "were recorded as girls?",
        why="Names carry information people use without thinking; a model that assumes every name is one or the "
            "other will misgender people in its writing. The records say exactly how mixed each name is.",
        sourcing="New questions (sources/baby_names): 'Of all the babies born in the US and named \"<name>\" since "
                 "1880, what share were recorded as girls?', 11 bins (under 5%, 5-15%, ..., over 95%). 60 mixed names "
                 "(10-90% girls, 20,000+ babies) and 40 clear ones. Truth from SSA birth records, 1880-2017.",
        collection="100 new questions, each in three shuffled orders (averaged).",
        scoring="Jev's expected share (bin midpoints) vs the records; mean absolute error for mixed and clear names; "
                "rank correlation on the mixed names; whether errors pull toward one sex or toward the middle.",
        chart="A scatter: records' share (x) vs Jev's share (y) for the mixed names, labeled at the extremes, diagonal.",
        compared_with="US Social Security Administration birth records, 1880-2017",
        limits="Records count sex recorded at birth, summed over 1880-2017; a name's mix today can differ from its "
               "all-time mix. No claim is made about anyone's identity.", new_questions=100, sources=["baby_names"])

    def run():
        rows = []
        for r in with_meta("baby_names"):
            if r["m"].get("set") != "share_girls":
                continue
            j = robust(r)
            est = sum(SHARE_MID[k] * v for k, v in j.items())
            rows.append({"id": r["id"], "name": r["m"]["name"], "true": 100 * r["m"]["girls_share"], "jev": est})
        t = pl.DataFrame(rows).with_columns(((pl.col("true") > 2) & (pl.col("true") < 98)).alias("mixed"))
        mx = t.filter(pl.col("true").is_between(10, 90))
        err = (mx["jev"] - mx["true"]).to_numpy()
        rho = spearmanr(mx["jev"], mx["true"]).statistic
        mae_c = float((t.filter(~pl.col("true").is_between(10, 90))["jev"] - t.filter(~pl.col("true").is_between(10, 90))["true"]).abs().mean())
        toward_mid = float(np.mean(np.abs(mx["jev"].to_numpy() - 50) < np.abs(mx["true"].to_numpy() - 50)))
        miss = mx.with_columns((pl.col("jev") - pl.col("true")).alias("e")).sort("e")
        lo, hi = miss.head(2).to_dicts(), miss.tail(2).reverse().to_dicts()
        f = lambda r: f"{r['name']} ({r['jev']:.0f}% vs {r['true']:.0f}%)"
        return Result(
            result=f"For names given to both sexes, Jev's estimate is off by {np.mean(np.abs(err)):.0f} points on "
                   f"average (rank correlation {rho:.2f} with the records); for clearly one-sex names, {mae_c:.0f}. It "
                   f"pulls {toward_mid:.0%} of mixed names toward 50/50. Biggest misses: {and_list([f(r) for r in hi + lo])} "
                   f"(Jev vs records).",
            evidence=f"{mx.height} mixed and {t.height - mx.height} clear names; 90% interval on the mean error {boot(err)}",
            numbers={"rows": rows, "mae_mixed": float(np.mean(np.abs(err))), "mae_clear": mae_c, "rho": rho,
                     "toward_middle": toward_mid}, n=t.height,
            chart={"type": "scatter", "points": [[round(r["true"], 1), round(r["jev"], 1)] for r in mx.to_dicts()],
                   "labels": [{"label": r["name"], "x": r["true"], "y": r["jev"]} for r in hi + lo],
                   "x": "records: % girls", "y": "Jev: % girls", "diagonal": True, "domain": [0, 100]},
            examples=[r["id"] for r in hi[:1] + lo[:1]])
    return spec, run


DECADES = [f"d{d}" for d in range(1880, 2011, 10)]


def names_decade():
    spec = Spec(
        id="names_peak_decade", family="names", title="When was every Agnes born?",
        question="Given a first name, does Jev know the decade when it was most popular for US babies?",
        why="FiveThirtyEight's 'how to tell someone's age when all you know is her name' made this famous: names "
            "carry a birth year. A model that knows the curves can tell a Mildred from a Madison.",
        sourcing="New questions (sources/baby_names): 'In which decade were the most US babies named \"<name>\" born?', "
                 "options the 1880s to the 2010s; about 10 names peaking in each decade (30,000+ babies, a clear peak). "
                 "Truth from SSA birth records.",
        collection="107 new questions, each in three shuffled orders (averaged).",
        scoring="Share where Jev's top decade is the peak; share within one decade; mean error in decades, by the "
                "true decade (does it know old names as well as new ones?); direction of the misses.",
        chart="A confusion strip: true peak decade (x) vs Jev's decade (y), dot size = names; plus ridges for a few "
              "names (records' births by decade vs Jev's distribution).",
        compared_with="US Social Security Administration birth records, 1880-2017",
        limits="Births, not living people: a name that peaked in the 1910s has few living bearers.", new_questions=107,
        sources=["baby_names"])

    def run():
        rows = []
        for r in with_meta("baby_names"):
            if r["m"].get("set") != "peak_decade":
                continue
            j = robust(r)
            t, p = DECADES.index(r["truth"].strip('"')), DECADES.index(top(j))
            rows.append({"id": r["id"], "name": r["m"]["name"], "true": 1880 + 10 * t, "jev": 1880 + 10 * p,
                         "err": p - t, "exp": 1880 + 10 * sum(DECADES.index(k) * v for k, v in j.items())})
        t = pl.DataFrame(rows)
        exact, near = float((t["err"] == 0).mean()), float((t["err"].abs() <= 1).mean())
        by = t.with_columns((pl.col("true") < 1950).alias("old")).group_by("old").agg(
            (pl.col("err") == 0).mean().alias("exact"), pl.col("err").mean().alias("bias"), pl.len()).sort("old").to_dicts()
        old, new = next(b for b in by if b["old"]), next(b for b in by if not b["old"])
        miss = t.filter(pl.col("err").abs() >= 2).sort(pl.col("err").abs(), descending=True).head(3).to_dicts()
        return Result(
            result=f"Jev names the peak decade for {exact:.0%} of {t.height} names and is within a decade for {near:.0%}. "
                   + (f"It knows names that peaked before 1950 about as well ({old['exact']:.0%} exact) as later ones ({new['exact']:.0%})"
                      if abs(old["exact"] - new["exact"]) < 0.15 else
                      f"It knows names that peaked {'after' if new['exact'] > old['exact'] else 'before'} 1950 better "
                      f"({max(old['exact'], new['exact']):.0%} exact) than {'older' if new['exact'] > old['exact'] else 'newer'} ones "
                      f"({min(old['exact'], new['exact']):.0%})")
                   + (f"; its misses lean {'late' if t['err'].mean() > 0 else 'early'} ({t['err'].mean():+.1f} decades on average)"
                      if abs(t["err"].mean()) >= 0.15 else "; its misses lean neither early nor late")
                   + (". Farthest off: " + and_list([f"{r['name']} (Jev says the {r['jev']}s, the records the {r['true']}s)" for r in miss]) if miss else "") + ".",
            evidence=f"{t.height} names; 90% interval on exact {boot(t['err'].eq(0).cast(float).to_numpy())}",
            numbers={"rows": rows, "exact": exact, "within_one": near, "by_era": by}, n=t.height,
            chart={"type": "heat", "cells": [{"y": c["true"], "x": c["jev"], "len": c["len"]} for c in t.group_by("true", "jev").len().to_dicts()],
                   "x": "Jev's decade", "y": "records' peak decade"},
            examples=[r["id"] for r in miss[:2]])
    return spec, run


# ---- 4. adjectives ----------------------------------------------------------------------------------------------------
def adjectives():
    spec = Spec(
        id="perception_adjectives", family="perception", title="Good, great, excellent: which is stronger?",
        question="Given two adjectives from the same scale ('warm' and 'hot', 'big' and 'vast'), does Jev pick the "
                 "stronger one the way linguists and crowd workers ordered them?",
        why="Intensity is how people grade things in words, and it is subtle: 'dim' vs 'dark', 'content' vs 'pleased'. "
            "A model that gets the order wrong will misread reviews, feedback and hedges.",
        sourcing="New questions (sources/scalar_adjectives): 'Which word expresses a stronger degree of the same "
                 "quality: \"<a>\" or \"<b>\"?' for every pair of differently ranked words in three gold sets: de Melo "
                 "& Bansal 2013 (linguists), Wilkinson & Oates 2016, and Cocos et al. 2018 (crowd). 749 pairs.",
        collection="1,498 new questions: each pair with the two words in both orders in the question text, each also "
                   "asked with the options shuffled (all averaged).",
        scoring="Per pair, Jev's probability for the stronger word averaged over both word orders; share of pairs where "
                "that is above one half, by set and by how far apart the words sit on their scale; the same share per "
                "word order, to show how much naming a word first helps it; the scales where it errs most.",
        chart="Bars: agreement by gold set and by distance on the scale, with 90% intervals.",
        compared_with="Three published gold orderings (linguists and crowd workers)",
        limits="Gold orderings disagree with each other on some scales; a 'miss' can be a defensible order.",
        new_questions=1498, sources=["scalar_adjectives"])

    def run():
        rows = []
        for r in with_meta("scalar_adjectives"):
            j = robust(r)
            truth = r["truth"].strip('"')
            other = next(k for k in (js(r["options"]) if isinstance(r["options"], str) else r["options"]) if k != truth)
            rows.append({"id": r["id"], "set": r["m"]["set"], "gap": min(r["m"]["gap"], 3), "scale": r["m"]["scale"],
                         "order": r["m"].get("order", "weaker_first"), "p": j.get(truth, 0.0),
                         "pair": f'"{other}" < "{truth}"'})
        q = pl.DataFrame(rows)
        # a pair's answer is the average over both orders of the words in the question
        t = q.group_by("set", "scale", "pair", "gap").agg(pl.col("p").mean(), pl.len().alias("orders"),
                                                         pl.col("id").first()).sort("set", "scale", "pair")
        t = t.with_columns((pl.col("p") > 0.5).alias("right"))
        by_order = {o: float((g["p"] > 0.5).mean()) for (o,), g in q.group_by("order")}
        by_set = t.group_by("set").agg(pl.col("right").mean(), pl.len()).sort("right").to_dicts()
        by_gap = t.group_by("gap").agg(pl.col("right").mean(), pl.len()).sort("gap").to_dicts()
        worst = t.group_by("scale").agg(pl.col("right").mean(), pl.len()).filter(pl.col("len") >= 3).sort("right").head(3).to_dicts()
        wrong_sure = t.filter(pl.col("p") < 0.1).sort("p").head(3).to_dicts()
        a = float(t["right"].mean())
        return Result(
            result=f"Jev picks the stronger adjective for {a:.0%} of {t.height} pairs: {by_gap[0]['right']:.0%} for neighbors on "
                   f"a scale, {by_gap[-1]['right']:.0%} for words three or more steps apart. By gold set it runs from "
                   f"{by_set[0]['right']:.0%} ({by_set[0]['set']}) to {by_set[-1]['right']:.0%} ({by_set[-1]['set']}). "
                   f"The order of the words matters: it is right {by_order.get('stronger_first', 0):.0%} of the time when "
                   f"the stronger word is named first and {by_order.get('weaker_first', 0):.0%} when it is named second."
                   + (f" It is surest and wrong on {and_list([w['pair'] for w in wrong_sure[:2]])}." if wrong_sure else ""),
            evidence=f"{t.height} pairs, each asked with the words in both orders (averaged); 90% interval "
                     f"{boot(t['right'].cast(float).to_numpy())}",
            numbers={"acc": a, "by_order": by_order, "by_set": by_set, "by_gap": by_gap, "worst_scales": worst,
                     "wrong_sure": wrong_sure}, n=t.height,
            chart={"type": "bars", "rows": [{"label": f"{b['gap']}{'+' if b['gap'] == 3 else ''} step{'s' if b['gap'] > 1 else ''} apart",
                                             "value": b["right"], "n": b["len"]} for b in by_gap]
                   + [{"label": "stronger word named first", "value": by_order.get("stronger_first", 0)},
                      {"label": "stronger word named second", "value": by_order.get("weaker_first", 0)}], "domain": [0, 1]},
            robustness="Each question is also asked with its two options in shuffled order (averaged); that moves nothing. "
                       "The words' order in the question text is what moves Jev, so every pair is asked both ways.",
            examples=[w["id"] for w in wrong_sure[:2]])
    return spec, run


# ---- 5. O*NET ---------------------------------------------------------------------------------------------------------
def jobs():
    spec = Spec(
        id="work_what_jobs_are_like", family="work", title="What jobs are like, according to Jev and to the workers",
        question="How often does a nurse deal with angry people, a web developer face deadlines, a roofer work in the "
                 "weather? Does Jev know what jobs are like, compared with what the people doing them report?",
        why="Models are asked about careers constantly. O*NET asks incumbent workers directly, so the gap between Jev "
            "and them is the gap between a job's reputation and its reality.",
        sourcing="New questions (sources/onet_context): 12 O*NET Work Context items (angry people, conflict, weather, "
                 "deadlines, public speaking, email, disease, sitting, freedom to decide, cost of mistakes, automation, "
                 "competition) for 46 well-known occupations, with O*NET's own five answers; the human distribution is "
                 "the share of surveyed workers choosing each (O*NET 29.0, CC BY 4.0).",
        collection="495 new questions (rows O*NET marks as unreliable are left out), each asked as written, for 'most "
                   "people', and with the levels reversed (averaged).",
        scoring="Per item, rank correlation across occupations between Jev's expected level and the workers' mean "
                "level, and the mean gap (Jev minus workers) with a 90% bootstrap interval over occupations; the "
                "occupation-item pairs with the largest gaps.",
        chart="A dot plot, one row per item: the mean gap with its interval, and the rank correlation as a label.",
        compared_with="US workers in each occupation (O*NET 29.0 incumbent surveys)",
        limits="O*NET answers come from samples of incumbents (median a few dozen per occupation); Jev answers about a "
               "typical member of the occupation.", new_questions=495, sources=["onet_context"])

    def run():
        rows = []
        for r in with_meta("onet_context"):
            h = biggest(r["humans"])
            if not h:
                continue
            base = level(js(r["jev_dist"]))
            rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v["kind"] == "reversed_levels"), None)
            rows.append({"id": r["id"], "item": r["m"]["element"], "occ": r["m"]["occupation"],
                         "jev": (base + rev) / 2 if rev is not None else base, "people": level(h["dist"])})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("people")).alias("gap"))
        items = []
        for (it,), g in t.group_by("item"):
            items.append({"item": it, "rho": float(spearmanr(g["jev"], g["people"]).statistic), "gap": float(g["gap"].mean()),
                          "ci": boot(g["gap"].to_numpy()), "n": g.height})
        items.sort(key=lambda x: x["gap"])
        rho_all = spearmanr(t["jev"], t["people"]).statistic
        over = t.sort("gap", descending=True).head(3).to_dicts()
        under = t.sort("gap").head(3).to_dicts()
        best = max(items, key=lambda x: x["rho"])
        worst = min(items, key=lambda x: x["rho"])
        f = lambda r: f"{r['occ'].split(',')[0].lower()} / {r['item'].lower()} ({r['jev']:.1f} vs {r['people']:.1f})"
        return Result(
            result=f"Jev ranks occupations {agree_word(rho_all)} like their workers (rank correlation {rho_all:.2f} over "
                   f"{t.height} answers), best on {best['item'].lower()} ({best['rho']:.2f}) and worst on "
                   f"{worst['item'].lower()} ({worst['rho']:.2f}). It overstates {items[-1]['item'].lower()} most "
                   f"({items[-1]['gap']:+.2f} levels on 0-4) and understates {items[0]['item'].lower()} most "
                   f"({items[0]['gap']:+.2f}). Biggest single gaps: {f(over[0])} and {f(under[0])} (Jev vs workers).",
            evidence=f"{t.height} occupation-item pairs over {t['occ'].n_unique()} occupations; 90% intervals over occupations",
            numbers={"items": items, "rho": rho_all, "over": over, "under": under}, n=t.height,
            chart={"type": "dots", "zero": 0, "rows": [{"label": x["item"], "value": x["gap"], "ci": x["ci"],
                                                        "right": f"ρ {x['rho']:.2f}"} for x in items]},
            examples=[over[0]["id"], under[0]["id"]])
    return spec, run


# ---- 6. ChaosNLI ------------------------------------------------------------------------------------------------------
def chaos():
    spec = Spec(
        id="perception_crowd_of_100", family="perception", title="Reading between the lines, against 100 people",
        question="When 100 people read the same two sentences and split on whether the second follows, does Jev's "
                 "probability look like the crowd's split, and does it side with the majority as often as a typical "
                 "person does?",
        why="Most datasets give one 'right' label; ChaosNLI shows that many items have none. That makes it possible "
            "to ask a better question than accuracy: does the model know when people disagree?",
        sourcing="New questions (sources/chaosnli): 600 items from ChaosNLI (Nie, Zhou & Bansal 2020), 300 each from "
                 "SNLI and MNLI, sampled evenly across how split the 100 labels are. Options in plain words (the "
                 "second sentence is true / might or might not be / is false, given the first).",
        collection="600 new questions, each asked as written and with the three options in shuffled orders (averaged).",
        scoring="Agreement with the crowd's majority, overall and by how split the crowd is (entropy terciles), against "
                "the typical person's agreement with the majority (the majority's share); rank correlation between "
                "Jev's confidence and the crowd's agreement; similarity of the distributions.",
        chart="Binned dots: the crowd's majority share (x) vs Jev's probability on that answer (y), with the diagonal "
              "and the typical person's agreement line.",
        compared_with="100 crowd workers per item (ChaosNLI)",
        limits="The options are paraphrased from the NLI labels; ChaosNLI's workers saw the standard labels.",
        new_questions=600, sources=["chaosnli"])

    def run():
        rows = []
        for r in with_meta("chaosnli"):
            h = norm(biggest(r["humans"])["dist"])
            j = robust(r)
            maj = top(h)
            rows.append({"id": r["id"], "maj_share": h[maj], "jev_on_maj": j.get(maj, 0), "agree": top(j) == maj,
                         "conf": max(j.values()), "ent": r["m"]["entropy"], "sim": 1 - jsd(j, h), "set": r["m"]["set"]})
        t = pl.DataFrame(rows).with_columns(pl.col("ent").qcut(3, labels=["clear", "mixed", "split"]).alias("div"))
        by = t.group_by("div").agg(pl.col("agree").mean(), pl.col("maj_share").mean(), pl.col("conf").mean(), pl.len()).sort("div").to_dicts()
        rho = spearmanr(t["conf"], t["maj_share"]).statistic
        a, person = float(t["agree"].mean()), float(t["maj_share"].mean())
        bins = t.with_columns(pl.col("maj_share").cut([0.5, 0.6, 0.7, 0.8, 0.9], labels=["<50%", "50-60%", "60-70%", "70-80%", "80-90%", "90%+"]).alias("b")) \
                .group_by("b").agg(pl.col("jev_on_maj").mean(), pl.len()).sort("b").to_dicts()
        return Result(
            result=f"Jev sides with the crowd's majority on {a:.0%} of items, where a typical person does {person:.0%}; "
                   f"on the most divided third it is {by[-1]['agree']:.0%} vs {by[-1]['maj_share']:.0%}. But its "
                   f"confidence barely tracks how divided people are (rank correlation {rho:.2f}): it is "
                   f"{by[-1]['conf']:.0%} sure on the items that split people most, {by[0]['conf']:.0%} on the clear ones.",
            evidence=f"{t.height} items, 100 labels each; 90% interval on agreement {boot(t['agree'].cast(float).to_numpy())}",
            numbers={"agree": a, "person": person, "by_division": by, "rho": rho, "bins": bins,
                     "sim": float(t["sim"].mean())}, n=t.height,
            chart={"type": "binned", "rows": [{"label": b["b"], "value": b["jev_on_maj"], "n": b["len"]} for b in bins],
                   "x": "crowd's majority share", "y": "Jev's probability on the majority answer", "diagonal": True},
            examples=seeded(t.filter(~pl.col("agree"))["id"].to_list(), "chaos"))
    return spec, run


# ---- 7. funny words ---------------------------------------------------------------------------------------------------
def funny_words():
    spec = Spec(
        id="words_funny", family="words", title="Is 'nincompoop' funny? Jev vs 800 raters",
        question="Rating single English words for how funny they are, does Jev find the same words funny as people do?",
        why="Jev can barely tell which joke or caption is funnier (humor family). Single words strip humor down to sound "
            "and meaning; if it can tell a funny word, the problem with jokes is elsewhere.",
        sourcing="New questions (sources/humor_words): 'How funny is the word \"<word>\" on its own?', five described "
                 "levels, for 600 of the 4,997 words in Engelthaler & Hills 2018, spread evenly over the range of "
                 "people's ratings (1-5, about 35 raters per word).",
        collection="599 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Rank correlation between Jev's expected level (base and reversed averaged) and people's mean rating, "
                "with a 90% bootstrap interval; the words it finds much funnier or much less funny than people.",
        chart="A scatter: people's mean (x) vs Jev's level (y), with the biggest disagreements labeled.",
        compared_with="US adults rating the words (Engelthaler & Hills 2018)",
        limits="Only people's means are published, so the comparison is ranks, not distributions.", new_questions=599,
        sources=["humor_words"])

    def run():
        rows = []
        for r in with_meta("humor_words"):
            base = level(js(r["jev_dist"]))
            rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v["kind"] == "reversed_levels"), None)
            rows.append({"id": r["id"], "word": r["text"].split('"')[1], "jev": (base + rev) / 2 if rev is not None else base,
                         "people": r["m"]["human_mean"]})
        t = pl.DataFrame(rows)
        rho = spearmanr(t["jev"], t["people"]).statistic
        idx = np.arange(t.height)
        ci = boot(idx, stat=lambda ii: spearmanr(t["jev"].to_numpy()[ii.astype(int)], t["people"].to_numpy()[ii.astype(int)]).statistic, b=300)
        t = t.with_columns((pl.col("jev").rank() / t.height - pl.col("people").rank() / t.height).alias("d"))
        more, less = t.sort("d", descending=True).head(4).to_dicts(), t.sort("d").head(4).to_dicts()
        tj, tp = t.sort("jev", descending=True).head(5)["word"].to_list(), t.sort("people", descending=True).head(5)["word"].to_list()
        return Result(
            result=f"Jev finds the same words funny as people {agree_word(rho)} (rank correlation {rho:.2f}). Its "
                   f"funniest: {and_list(tj)}; people's: {and_list(tp)}. It is far more amused than people by "
                   f"{and_list([m['word'] for m in more[:3]])}, and far less by {and_list([m['word'] for m in less[:3]])}.",
            evidence=f"{t.height} words; 90% interval {ci[0]:.2f} to {ci[1]:.2f}",
            numbers={"rho": rho, "ci90": ci, "more": more, "less": less, "top_jev": tj, "top_people": tp}, n=t.height,
            chart={"type": "scatter", "points": t.select("people", "jev").to_numpy().round(2).tolist(),
                   "labels": [{"label": m["word"], "x": m["people"], "y": m["jev"]} for m in more[:4] + less[:4]],
                   "x": "people's mean (1-5)", "y": "Jev's level (0-4)"},
            examples=[more[0]["id"], less[0]["id"]])
    return spec, run


EXPERIMENTS = [probability(), round_trip(), settings(), amount(), amount_settings(), names_share(), names_decade(),
               adjectives(), jobs(), chaos(), funny_words()]
