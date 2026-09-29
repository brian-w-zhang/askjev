"""Knowledge experiments: what kinds of facts Jev knows, where it thins out, and whether its confidence knows it.

Indicators, not a benchmark: every experiment compares kinds of knowledge with each other (or confidence with
accuracy), never a total score. Many sources keep their raw values (populations, nutrient amounts, page views) only in
the normalized files, so `full_meta` reads those; the parquet keeps a trimmed meta.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import polars as pl

from lib import Result, Spec, boot, js, seeded, source

NORM = Path("data/normalized")


@lru_cache(maxsize=None)
def full_meta(name: str) -> dict:
    """id -> full meta for one source, from its normalized file."""
    out = {}
    for line in (NORM / f"{name}.jsonl").open():
        r = json.loads(line)
        out[r["id"]] = r.get("meta") or {}
    return out


def rows_of(name: str, template: str | None = None):
    """Shown questions of a source with their full meta; political items (meta.flags) skipped."""
    M = full_meta(name)
    q = source(name)
    if template:
        q = q.filter(pl.col("template_id") == template)
    for r in q.iter_rows(named=True):
        m = M.get(r["id"], {})
        if "political" in (m.get("flags") or []) or r["correct"] is None:
            continue
        yield r, m


def pick(r: dict) -> str:
    d = js(r["jev_dist"])
    return max(d, key=d.get)


def acc(values) -> tuple[float, list[float]]:
    v = np.asarray(values, dtype=float)
    return float(v.mean()), boot(v)


# ---- 1. calibration ------------------------------------------------------------------------------------------------
FACT_SOURCES = ["wikidata_g4", "wikidata_companies", "wikidata_memes", "pantheon_history", "pantheon_sports",
                "worldbank_pairs", "usda_nutrients", "anage_pairs", "mmlu", "arc", "sciq", "openbookqa", "medmcqa",
                "head_qa", "truthfulqa", "uscis_civics", "opentdb", "strategyqa", "boolq", "hotpot_compare",
                "natural_questions_yn", "ham_radio_pools", "uscg_mariner"]


NICE = {"wikidata_memes": "which internet meme is better known", "natural_questions_yn": "yes/no search questions",
        "medmcqa": "medical entrance exams", "mmlu": "school and college exams", "boolq": "yes/no reading questions",
        "strategyqa": "multi-step yes/no questions", "opentdb": "pub trivia"}


def calibration():
    spec = Spec(
        id="knowledge_calibration", family="knowledge", title="When Jev says 70% on a fact, it's right about 70% of the time",
        question="Across 120,000 questions with a known right answer, does Jev's confidence match how often it is right?",
        why="A model that knows when it doesn't know is far more useful than one that is merely accurate. TypeSafe "
            "publishes no calibration numbers (01-jev.md §6 lists this as open ground), so this is new.",
        sourcing="Every shown fact question with a right answer across 23 sources (Wikidata, Pantheon, World Bank, USDA, "
                 "AnAge, school and professional exams, trivia, yes/no reading questions). Enough: 120,000 questions.",
        scoring="Jev's probability on its top option, binned; in each bin, the share of questions it got right, with a "
                "90% bootstrap interval. The gap between confidence and accuracy is summarized as the average absolute "
                "gap weighted by bin size (expected calibration error), and per source as mean confidence minus accuracy.",
        chart="A reliability diagram: confidence bins on x, accuracy on y, the diagonal as perfect calibration, dot size by "
              "count.",
        compared_with="the right answers (Wikidata, exam keys, dataset labels)",
        limits="Answer keys contain some errors (MMLU virology is known for them), which make Jev look overconfident. The "
               "mix of sources sets the overall curve; the per-source gaps are the fairer comparison.",
        sources=FACT_SOURCES)

    def run():
        q = source(*FACT_SOURCES).filter(pl.col("correct").is_not_null())
        edges = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
        labels = ["under 50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-95%", "95-99%", "99%+"]
        q = q.with_columns(pl.col("p_top").cut(edges, labels=labels, left_closed=True).alias("b"))
        bins = []
        for lab in labels:
            g = q.filter(pl.col("b") == lab)
            if g.height:
                a, ci = acc(g["correct"].to_numpy())
                bins.append({"label": lab, "conf": float(g["p_top"].mean()), "acc": a, "ci": ci, "n": g.height})
        ece = sum(abs(b["conf"] - b["acc"]) * b["n"] for b in bins) / q.height
        per = q.group_by("source").agg(pl.len().alias("n"), pl.col("correct").mean().alias("acc"),
                                        pl.col("p_top").mean().alias("conf")) \
               .with_columns((pl.col("conf") - pl.col("acc")).alias("over")).sort("over").to_dicts()
        over = [p for p in per if p["over"] >= 0.02]
        mid = next(b for b in bins if b["label"] == "70-80%")
        return Result(
            result=f"Jev's confidence on facts is close to honest: when it is 70-80% sure it is right "
                   f"{mid['acc']:.0%} of the time, and across all {q.height:,} questions its confidence is off by "
                   f"{ece * 100:.1f} points on average. It overstates itself most on "
                   + ", ".join(f"{NICE.get(p['source'], p['source'])} ({p['conf']:.0%} sure, {p['acc']:.0%} right)"
                               for p in over[::-1][:3]) + ".",
            evidence=f"{q.height:,} questions from {len(per)} sources; 90% intervals by bootstrap within each bin",
            numbers={"bins": bins, "ece": ece, "per_source": per}, n=q.height,
            chart={"type": "binned", "rows": [{"label": b["label"], "value": b["acc"], "x": b["conf"], "ci": b["ci"],
                                                "n": b["n"]} for b in bins],
                   "x": "Jev's confidence", "y": "share right", "diagonal": True},
            robustness=f"Most sources sit within 2 points of their confidence ({sum(abs(p['over']) < 0.02 for p in per)} "
                       f"of {len(per)}); none is underconfident by more than {-per[0]['over'] * 100:.1f} points.",
            examples=seeded(q.filter(~pl.col("correct") & (pl.col("p_top") >= 0.95))["id"].to_list(), "calib"))
    return spec, run


# ---- 2. the wealth rule of thumb -----------------------------------------------------------------------------------
def wealth():
    spec = Spec(
        id="knowledge_wealth_rule", family="knowledge", title="Jev answers country questions with 'the richer one'",
        question="Asked which of two countries has more doctors, internet users, unemployment or smokers, does Jev "
                 "know the numbers, or lean on which country is richer?",
        why="A rule of thumb (rich countries have more of the good things) gets most such questions right and fails "
            "exactly where the world is surprising. Where accuracy splits on whether the truth fits the rule, the model "
            "is using the rule, not the fact.",
        sourcing="Existing World Bank pairs (24 indicators, 2019-2023 averages; CC BY 4.0), each with the two values; "
                 "GDP per person taken from the same corpus's GDP questions. Pairs touching contested politics are "
                 "flagged and left out. Enough: 8,000 pairs.",
        scoring="For each indicator, whether the richer country usually has the higher value (the rule's direction, from "
                "the data). Each pair is 'fits the rule' when the right answer is the side the rule predicts, else "
                "'against the rule'. Accuracy in each group, per indicator and overall, with 90% bootstrap intervals.",
        chart="A dumbbell per indicator: accuracy when the answer fits the wealth rule vs when it goes against it, "
              "sorted by the gap.",
        compared_with="World Bank World Development Indicators",
        limits="GDP per person is known for 150 countries; pairs without it are skipped. Some indicators barely follow "
               "wealth (forest cover, rainfall); they're shown as the control.", sources=["worldbank_pairs"])

    def run():
        gdp = {}
        for r, m in rows_of("worldbank_pairs", "worldbank_pairs.gdp_per_person"):
            gdp.update(m.get("values") or {})
        rows = []
        for r, m in rows_of("worldbank_pairs"):
            v = m.get("values") or {}
            if len(v) != 2 or not all(n in gdp for n in v):
                continue
            opts = js(r["options"])
            key = {n: next((k for k, lab in opts.items() if lab == n or n in lab or lab in n), None) for n in v}
            if None in key.values():
                continue
            rich = key[max(v, key=gdp.get)]
            vals = [x for x in v.values() if x]
            rows.append({"id": r["id"], "ind": r["template_id"].split(".")[-1].replace("_", " "),
                         "truth_rich": js(r["truth"]) == rich, "jev_rich": pick(r) == rich, "correct": r["correct"],
                         "ratio": max(vals) / min(vals) if len(vals) == 2 and min(vals) > 0 else None})
        t = pl.DataFrame(rows)
        direction = {d["ind"]: d["truth_rich"] >= 0.5 for d in t.group_by("ind").agg(pl.col("truth_rich").mean()).to_dicts()}
        t = t.with_columns(pl.struct("ind", "truth_rich").map_elements(
            lambda s: s["truth_rich"] == direction[s["ind"]], return_dtype=pl.Boolean).alias("fits"))
        per = []
        for (ind,), g in t.group_by("ind"):
            f, a = g.filter(pl.col("fits")), g.filter(~pl.col("fits"))
            if a.height < 15:
                continue
            per.append({"label": ind, "fits": float(f["correct"].mean()), "against": float(a["correct"].mean()),
                        "n_against": a.height, "share_fits": f.height / g.height})
        per.sort(key=lambda x: x["against"] - x["fits"])
        fa, fci = acc(t.filter(pl.col("fits"))["correct"].to_numpy())
        aa, aci = acc(t.filter(~pl.col("fits"))["correct"].to_numpy())
        top3 = per[:3]
        w = t.filter(pl.col("ratio") >= 2)
        wide = {"fits": float(w.filter(pl.col("fits"))["correct"].mean()),
                "against": float(w.filter(~pl.col("fits"))["correct"].mean())}
        return Result(
            result=f"When the right answer is the country that wealth predicts (the richer one has more doctors, the "
                   f"poorer one more farming), Jev gets World Bank comparisons right {fa:.0%} of the time; when the "
                   f"world goes against that pattern, {aa:.0%}. The split "
                   f"is widest for " + ", ".join(f"{p['label']} ({p['fits']:.0%} vs {p['against']:.0%})" for p in top3)
                   + ".",
            evidence=f"{t.height:,} pairs over {len(per)} indicators; 90% intervals {fci} and {aci}",
            numbers={"fits": fa, "against": aa, "ci_fits": fci, "ci_against": aci, "per_indicator": per, "wide": wide}, n=t.height,
            chart={"type": "dumbbell", "marks": {"a": "jevo", "b": "jev"}, "rows": [{"label": p["label"], "a": p["fits"], "b": p["against"]} for p in per],
                   "a_label": "fits the wealth rule", "b_label": "against it", "domain": [0, 1]},
            robustness=f"Pairs against the pattern are closer on average, so the split is partly about closeness: on "
                       f"pairs at least 2x apart it is {wide['fits']:.0%} vs {wide['against']:.0%}. Jev picks the richer "
                       f"country {t['jev_rich'].mean():.0%} of the time; the right answer is the richer one "
                       f"{t['truth_rich'].mean():.0%} of the time.",
            examples=seeded(t.filter(~pl.col("fits") & ~pl.col("correct"))["id"].to_list(), "wealth"))
    return spec, run


# ---- 3. categories vs quantities -----------------------------------------------------------------------------------
SIZE_TEMPLATES = ["g4.more_people", "g4.larger_area", "g4.longer_river", "g4.higher_mountain", "g4.stadium_capacity",
                  "g4.animal_heavier"]
CATEGORY_TEMPLATES = ["g4.continent", "g4.country_of", "g4.capital", "g4.language", "g4.citizenship", "g4.field",
                      "g4.sport", "g4.team_sport", "g4.team_country", "g4.competition_sport", "g4.animal_class",
                      "g4.food_origin", "g4.food_ingredient", "g4.food_cuisine", "g4.game_developer", "g4.developed_by",
                      "g4.made_by", "g4.animal_endemic", "g4.event_country"]


def quantities():
    spec = Spec(
        id="knowledge_close_calls", family="knowledge", title="Jev knows what things are, less how big they are",
        question="Jev rarely misses which country, sport or category something belongs to. How does it do when it "
                 "has to compare two sizes, and how close can the sizes get before it guesses?",
        why="Knowing that the Main is a German river is a different skill from knowing it is longer than the Pilica. "
            "The accuracy curve over the size ratio shows how finely the model's sense of magnitude is resolved, and "
            "whether its confidence drops as the call gets closer.",
        sourcing="Existing Wikidata questions: 13,000 category facts (continent, capital, sport, food origin...) and "
                 "7,500 size comparisons (city populations, areas, rivers, mountains, stadiums, animal weights) with both "
                 "values stored. Enough.",
        scoring="Accuracy of the category facts; for comparisons, accuracy and mean confidence by the ratio of the "
                "larger value to the smaller, binned, with 90% bootstrap intervals; the ratio at which accuracy "
                "crosses 90%.",
        chart="A psychometric curve: size ratio (log scale) on x, share right on y, with Jev's mean confidence as a "
              "second line and the category-fact accuracy as a reference line.",
        compared_with="Wikidata values",
        limits="Wikidata values can be stale or disputed (city populations, stadium capacities). Comparisons pair "
               "items of the same kind only.", sources=["wikidata_g4"])

    def run():
        cat_rows = [r for t in CATEGORY_TEMPLATES for r, _ in rows_of("wikidata_g4", t)]
        cats = [r["correct"] for r in cat_rows]
        rows = []
        for t in SIZE_TEMPLATES:
            for r, m in rows_of("wikidata_g4", t):
                v = m.get("values") or []
                if len(v) == 2 and min(v) > 0:
                    rows.append({"id": r["id"], "kind": t.split(".")[-1], "ratio": max(v) / min(v),
                                 "correct": r["correct"], "conf": r["p_top"]})
        d = pl.DataFrame(rows)
        edges = [1.1, 1.25, 1.5, 2, 3, 5, 10]
        labels = ["<1.1x", "1.1-1.25x", "1.25-1.5x", "1.5-2x", "2-3x", "3-5x", "5-10x", "10x+"]
        d = d.with_columns(pl.col("ratio").cut(edges, labels=labels).alias("b"))
        bins = []
        for lab in labels:
            g = d.filter(pl.col("b") == lab)
            if g.height >= 30:
                a, ci = acc(g["correct"].to_numpy())
                bins.append({"label": lab, "acc": a, "ci": ci, "conf": float(g["conf"].mean()), "n": g.height})
        ca, cci = acc(cats)
        cross = next((b["label"] for b in bins if b["acc"] >= 0.9 and all(x["acc"] >= 0.9 for x in bins[bins.index(b):])), None)
        close = d.filter(pl.col("ratio") < 1.5)
        cl, clci = acc(close["correct"].to_numpy())
        return Result(
            result=f"Jev gets {ca:.1%} of {len(cats):,} category facts right (which country, which sport, which "
                   f"continent), but comparing two sizes within 1.5x of each other (which city is bigger, which river "
                   f"longer) only {cl:.0%}, and it stays above 90% only from about {cross} apart. Its confidence falls "
                   f"less than its accuracy: at {bins[0]['label']} apart it is {bins[0]['conf']:.0%} sure and "
                   f"{bins[0]['acc']:.0%} right.",
            evidence=f"{len(cats):,} category facts, {d.height:,} comparisons; 90% intervals {cci} and {clci}",
            numbers={"category_acc": ca, "bins": bins, "close_acc": cl, "by_kind": d.group_by("kind").agg(
                pl.len().alias("n"), pl.col("correct").mean().alias("acc"), pl.col("ratio").median().alias("median_ratio")).to_dicts()},
            n=len(cats) + d.height,
            chart={"type": "binned", "rows": [{"label": b["label"], "value": b["acc"], "ci": b["ci"], "conf": b["conf"],
                                                "n": b["n"]} for b in bins],
                   "x": "how many times bigger the larger one is", "y": "share right", "reference": ca,
                   "reference_label": "category facts"},
            robustness="Confidence vs accuracy by gap: " + "; ".join(
                f"{b['label']} {b['conf']:.0%} sure, {b['acc']:.0%} right" for b in bins) + ".",
            examples=seeded(close.filter(~pl.col("correct"))["id"].to_list(), "close"),
            ids=[r["id"] for r in cat_rows] + d["id"].to_list())
    return spec, run


# ---- 4. nature's numbers: nutrients and animal lives ---------------------------------------------------------------
def nature_numbers():
    spec = Spec(
        id="knowledge_nature_numbers", family="knowledge", title="Jev knows calories and fat, not vitamin C or incubation",
        question="Comparing two foods by a nutrient, or two animals by lifespan, gestation or clutch size, which "
                 "quantities does Jev know and which does it guess?",
        why="Everyday health and nature questions are exactly these comparisons ('does kale have more calcium than "
            "milk?'). Holding the size of the gap fixed separates what the model knows from what is just hard.",
        sourcing="Existing USDA FoodData Central pairs (13 nutrients per 100 g; CC0) and AnAge pairs (5 life-history "
                 "traits; CC BY 3.0), each with both values. Only pairs where one value is at least twice the other "
                 "are scored, so every quantity is judged on clear-cut cases. Enough: 9,000 such pairs.",
        scoring="Accuracy per quantity on pairs at least 2x apart, with 90% bootstrap intervals; for nutrients, accuracy "
                "when the richer food is from the food group that is usually richer vs when it isn't.",
        chart="Ranked dots: one row per quantity, accuracy with its interval, foods and animals colored apart.",
        compared_with="USDA FoodData Central and AnAge values",
        limits="USDA values include fortified and cured foods (cured ham carries added vitamin C), which is part of "
               "what the model must know. AnAge values are maximum recorded, not typical.",
        sources=["usda_nutrients", "anage_pairs"])

    def run():
        rows, food = [], []
        for name, domain in (("usda_nutrients", "food"), ("anage_pairs", "animal")):
            for r, m in rows_of(name):
                v = list((m.get("values_per_100g") or {}).values()) if domain == "food" else (m.get("values") or [])
                if len(v) != 2 or min(v) <= 0 or max(v) / min(v) < 2:
                    continue
                q = r["template_id"].split(".")[-1].replace("_", " ").replace("vitamin c", "vitamin C").replace("vitamin a", "vitamin A")
                rows.append({"id": r["id"], "q": q, "domain": domain, "correct": r["correct"]})
                if domain == "food" and m.get("groups"):
                    vals = m["values_per_100g"]
                    keys = list(vals)
                    food.append({"q": q, "groups": m["groups"], "vals": [vals[k] for k in keys],
                                 "truth_idx": keys.index(js(r["truth"])) if js(r["truth"]) in keys else None,
                                 "correct": r["correct"]})
        t = pl.DataFrame(rows)
        per = []
        for (q, dom), g in t.group_by("q", "domain"):
            a, ci = acc(g["correct"].to_numpy())
            per.append({"label": q, "domain": dom, "acc": a, "ci": ci, "n": g.height})
        per.sort(key=lambda x: x["acc"])
        # food-group rule of thumb: mean value per (nutrient, group) from the data itself
        gm: dict = {}
        for f in food:
            for gname, val in zip(f["groups"], f["vals"]):
                gm.setdefault((f["q"], gname), []).append(val)
        gm = {k: float(np.median(v)) for k, v in gm.items()}
        fits, against = [], []
        for f in food:
            if f["truth_idx"] is None or f["groups"][0] == f["groups"][1]:
                continue
            typical = int(gm[(f["q"], f["groups"][1])] > gm[(f["q"], f["groups"][0])])
            (fits if typical == f["truth_idx"] else against).append(f["correct"])
        lo, hi = per[:3], per[-3:]
        fa, aa = float(np.mean(fits)), float(np.mean(against))
        return Result(
            result="Even when one value is at least twice the other, Jev's hit rate runs from "
                   + ", ".join(f"{p['label']} {p['acc']:.0%}" for p in hi[::-1]) + " down to "
                   + ", ".join(f"{p['label']} {p['acc']:.0%}" for p in lo) + ".",
            evidence=f"{t.height:,} pairs at least 2x apart over {len(per)} quantities; food-group split over "
                     f"{len(fits) + len(against):,} cross-group pairs ({len(against)} against the usual group)",
            numbers={"per_quantity": per, "group_fits": fa, "group_against": aa, "n_against": len(against)}, n=t.height,
            chart={"type": "dots", "domain": [0.5, 1], "rows": [{"label": p["label"], "value": p["acc"], "ci": p["ci"],
                                                                  "group": p["domain"]} for p in per]},
            robustness=f"Not a food-group stereotype: between foods from different groups it is right {fa:.0%} when the "
                       f"answer comes from the group usually richer in that nutrient and {aa:.0%} when it doesn't "
                       f"(90% intervals {boot(np.asarray(fits, float))} and {boot(np.asarray(against, float))}).",
            examples=seeded(t.filter(~pl.col("correct") & pl.col("q").is_in([p["label"] for p in lo]))["id"].to_list(), "nature"))
    return spec, run


# ---- 5. what it can put in order -----------------------------------------------------------------------------------
def dating():
    spec = Spec(
        id="knowledge_what_came_first", family="knowledge", title="Jev can date video games to the year, not memes",
        question="Asked which of two things came first (games, software, companies, memes, historical events), how "
                 "close in time can they be before Jev loses track, and does that depend on what they are?",
        why="Knowing roughly when things happened is a sign of how densely a kind of thing is covered in what the "
            "model learned. Holding the gap in years fixed shows which worlds it knows in fine detail.",
        sourcing="Existing Wikidata 'which came first' questions with both years stored: video games, software and "
                 "products, companies, historical states and events, births, and internet memes. Enough: 9,000 pairs.",
        scoring="Accuracy by the gap in years (binned), and, for pairs 1-5 years apart, accuracy per kind of thing with "
                "90% bootstrap intervals.",
        chart="Dots: accuracy on close pairs (1-5 years apart) per kind of thing, with the overall curve by gap as an "
              "inset.",
        compared_with="Wikidata dates (release, founding, inception)",
        limits="TypeSafe documents weak date comparison (01-jev.md §6.3) when dates are given in the question; here the "
               "dates are recalled, not given, so this measures memory of when things happened. Wikidata dates can be "
               "disputed for memes and old states.", sources=["wikidata_g4", "wikidata_memes"])

    NAMES = {"game_released_first": "video games", "released_first": "software and products",
             "founded_first": "companies", "born_first": "people's births", "event_first": "historical events",
             "state_founded": "states and dynasties", "came_first": "internet memes"}

    def run():
        rows = []
        for name in ("wikidata_g4", "wikidata_memes"):
            for r, m in rows_of(name):
                t = r["template_id"].split(".")[-1]
                if t not in NAMES:
                    continue
                v = m.get("values") if name == "wikidata_g4" else m.get("years")
                if not v or len(v) != 2 or v[0] == v[1]:
                    continue
                rows.append({"id": r["id"], "kind": NAMES[t], "gap": abs(v[0] - v[1]), "correct": r["correct"]})
        d = pl.DataFrame(rows)
        close = d.filter(pl.col("gap") <= 5)
        per = []
        for (k,), g in close.group_by("kind"):
            if g.height >= 40:
                a, ci = acc(g["correct"].to_numpy())
                per.append({"label": k, "acc": a, "ci": ci, "n": g.height})
        per.sort(key=lambda x: -x["acc"])
        d = d.with_columns(pl.col("gap").cut([5, 10, 25, 50, 100], labels=["1-5", "6-10", "11-25", "26-50", "51-100", "100+"]).alias("b"))
        curve = [{"label": b, "acc": float(g["correct"].mean()), "n": g.height}
                 for b in ["1-5", "6-10", "11-25", "26-50", "51-100", "100+"] if (g := d.filter(pl.col("b") == b)).height]
        return Result(
            result=f"Given two {per[0]['label']} released within five years of each other, Jev says which came first "
                   f"{per[0]['acc']:.0%} of the time; for " + " and ".join(f"{p['label']}, {p['acc']:.0%}" for p in per[1:])
                   + ".",
            evidence=f"{close.height:,} pairs 1-5 years apart, {d.height:,} pairs in all; 90% intervals over pairs",
            numbers={"close": per, "curve": curve}, n=d.height,
            chart={"type": "dots", "domain": [0.5, 1], "rows": [{"label": p["label"], "value": p["acc"], "ci": p["ci"]} for p in per],
                   "inset": {"type": "binned", "rows": [{"label": c["label"], "value": c["acc"], "n": c["n"]} for c in curve],
                             "x": "years apart", "y": "share right"}},
            robustness="With all gaps pooled, accuracy climbs from " + f"{curve[0]['acc']:.0%} at 1-5 years to "
                       f"{curve[-1]['acc']:.0%} at 100+ years.",
            examples=seeded(close.filter(~pl.col("correct") & (pl.col("kind") == per[-1]["label"]))["id"].to_list(), "dates"),
            ids=d["id"].to_list())
    return spec, run


# ---- 6. fame: history vs the internet ------------------------------------------------------------------------------
def fame():
    spec = Spec(
        id="knowledge_fame_online", family="knowledge", title="Jev knows who's famous in history, not what's famous online",
        question="Asked which of two people, athletes or internet phenomena is better known, how often does Jev pick "
                 "the one the world actually looks up more, and is it as sure as it should be?",
        why="Fame is a fact about people's attention, not about the thing itself. A model trained on text has seen the "
            "famous more often, so it should know fame well; where it doesn't, its picture of what people care about "
            "is out of date or thin.",
        sourcing="Existing questions: Pantheon historical figures and athletes (fame by the Historical Popularity "
                 "Index: Wikipedia languages and page views; CC BY-SA 4.0) and Wikidata internet phenomena (fame by "
                 "English Wikipedia page views 2023-2025; CC0). Politicians flagged political are left out. Enough: "
                 "7,000 pairs.",
        scoring="Accuracy and mean confidence per domain with 90% bootstrap intervals; for memes, accuracy by how many "
                "times more views the better-known one had.",
        chart="Paired bars per domain: Jev's confidence vs its accuracy, so overconfidence shows as a gap.",
        compared_with="Wikipedia attention (Pantheon HPI, page views)",
        limits="Page views are a proxy for fame and favor recent and English-language interest.",
        sources=["pantheon_history", "pantheon_sports", "wikidata_memes"])

    def run():
        groups = {"historical figures": list(rows_of("pantheon_history", "pantheon_history.better_known")),
                  "athletes": list(rows_of("pantheon_sports")),
                  "internet phenomena": list(rows_of("wikidata_memes", "wikidata_memes.better_known"))}
        per = []
        for k, rs in groups.items():
            a, ci = acc([r["correct"] for r, _ in rs])
            per.append({"label": k, "acc": a, "ci": ci, "conf": float(np.mean([r["p_top"] for r, _ in rs])), "n": len(rs)})
        memes = [(max(m["enwiki_pageviews_2023_2025"]) / max(1, min(m["enwiki_pageviews_2023_2025"])), r)
                 for r, m in groups["internet phenomena"]]
        big = [r["correct"] for x, r in memes if x >= 30]
        h, mm = per[0], per[2]
        return Result(
            result=f"Jev picks the better-known of two historical figures {h['acc']:.0%} of the time, but of two internet "
                   f"phenomena only {mm['acc']:.0%}, while being {mm['conf']:.0%} sure. Even when one meme had 30 times "
                   f"the page views of the other, it picks it only {np.mean(big):.0%} of the time.",
            evidence=f"{sum(p['n'] for p in per):,} pairs; 90% intervals: " + "; ".join(f"{p['label']} {p['ci']}" for p in per),
            numbers={"domains": per, "memes_30x": float(np.mean(big)), "memes_30x_n": len(big)}, n=sum(p["n"] for p in per),
            chart={"type": "bars2", "labels": [p["label"] for p in per], "a": [p["conf"] for p in per],
                   "b": [p["acc"] for p in per], "a_label": "Jev's confidence", "b_label": "share right"},
            robustness=f"Athletes land between the two ({per[1]['acc']:.0%} right, {per[1]['conf']:.0%} sure).",
            examples=seeded([r["id"] for x, r in memes if x >= 30 and not r["correct"]], "fame"),
            ids=[r["id"] for rs in groups.values() for r, _ in rs])
    return spec, run


# ---- 7. trivia by category -----------------------------------------------------------------------------------------
def trivia():
    spec = Spec(
        id="knowledge_pop_trivia", family="knowledge", title="Jev's trivia gap: science easy, video games and anime hard",
        question="On pub-quiz trivia, which categories does Jev know and which does it miss, and does it find the "
                 "questions people rated hard harder?",
        why="Trivia spans the whole of general culture in one format, so category differences are about knowledge, not "
            "question style; the human difficulty ratings give an outside check.",
        sourcing="Existing Open Trivia Database questions (CC BY-SA 4.0) with their category and the contributor's "
                 "difficulty rating. Enough: 2,800 questions, categories with 40+ questions shown.",
        scoring="Accuracy per category with 90% bootstrap intervals; accuracy by the easy/medium/hard rating.",
        chart="Ranked dots: one row per category, with the difficulty ratings as a small three-bar inset.",
        compared_with="Open Trivia DB answer keys and difficulty ratings",
        limits="Difficulty is one contributor's rating; categories are the database's.", sources=["opentdb"])

    def run():
        M = full_meta("opentdb")
        rows = [{"id": r["id"], "cat": M[r["id"]].get("category", "?").replace("Entertainment: ", "").replace("Science: ", ""),
                 "diff": M[r["id"]].get("difficulty"), "correct": r["correct"]} for r, _ in rows_of("opentdb")]
        t = pl.DataFrame(rows)
        per = []
        for (c,), g in t.group_by("cat"):
            if g.height >= 40:
                a, ci = acc(g["correct"].to_numpy())
                per.append({"label": c, "acc": a, "ci": ci, "n": g.height})
        per.sort(key=lambda x: x["acc"])
        diff = {d: float(t.filter(pl.col("diff") == d)["correct"].mean()) for d in ("easy", "medium", "hard")}
        return Result(
            result=f"Jev misses pop-culture trivia most: it gets {per[0]['label'].lower().replace('video games', 'video game')} questions right "
                   f"{per[0]['acc']:.0%} of the time, {per[1]['label'].lower()} {per[1]['acc']:.0%} and "
                   f"{per[2]['label'].lower()} {per[2]['acc']:.0%}, against {per[-3]['acc']:.0%}-{per[-1]['acc']:.0%} "
                   f"for {per[-3]['label'].lower()}, {per[-2]['label'].lower()} and {per[-1]['label'].lower()}. Questions "
                   f"rated easy, medium and hard go {diff['easy']:.0%}, {diff['medium']:.0%}, {diff['hard']:.0%}.",
            evidence=f"{t.height:,} questions in {len(per)} categories with 40+; 90% intervals by bootstrap",
            numbers={"categories": per, "difficulty": diff}, n=t.height,
            chart={"type": "dots", "domain": [0.5, 1], "rows": [{"label": p["label"], "value": p["acc"], "ci": p["ci"]} for p in per],
                   "inset": {"type": "bars", "labels": ["easy", "medium", "hard"], "values": [diff[d] for d in ("easy", "medium", "hard")]}},
            robustness="The same gap shows in Wikidata: see knowledge_fame_online for internet culture.",
            examples=seeded(t.filter(~pl.col("correct") & (pl.col("cat") == per[0]["label"]))["id"].to_list(), "trivia"))
    return spec, run


# ---- 8. misconceptions vs stories ----------------------------------------------------------------------------------
STORY = {"Fiction", "Myths and Fairytales", "Proverbs", "Superstitions"}
ATTRIB = {"Misquotations", "Confusion: People", "Confusion: Other", "Confusion: Places"}
SKIP = {"Religion", "Politics"}


def story_frames():
    spec = Spec(
        id="knowledge_story_frames", family="knowledge", title="Jev rejects misconceptions, but answers from inside the story",
        question="On TruthfulQA, where the tempting answer is a popular falsehood, which kinds of falsehood does Jev "
                 "fall for?",
        why="Rejecting 'you swallow eight spiders a year' is one skill; noticing that 'what happens if you speak of the "
            "Devil?' is asking about the real world, not the saying, is another. A model that answers inside the story "
            "is reading the question literally in a way the TruthfulQA authors count as false.",
        sourcing="Existing TruthfulQA multiple-choice questions (Lin et al. 2022, Apache 2.0) with their category; "
                 "religion and politics categories are left out. Enough: 730 questions.",
        scoring="Accuracy per group of categories (plain misconceptions and facts; stories, myths, proverbs and "
                "superstitions; misattributed quotes and confusable names) with 90% bootstrap intervals, and the mean "
                "confidence of its wrong answers.",
        chart="Three bars (share right per group) with the confidence of wrong answers marked, plus three example "
              "questions with Jev's pick.",
        compared_with="TruthfulQA's answer key",
        limits="TruthfulQA counts in-story answers ('Quasimodo rings the bells') as false by design; the finding is "
               "about which reading Jev chooses, not ignorance. Literal reading is documented (01-jev.md §6.1); this "
               "quantifies it on one kind of question.", sources=["truthfulqa"])

    def run():
        M = full_meta("truthfulqa")
        rows = []
        for r, _ in rows_of("truthfulqa"):
            c = M[r["id"]].get("category", "")
            if c in SKIP:
                continue
            grp = "stories, myths and sayings" if c in STORY else "quotes and confusable names" if c in ATTRIB \
                else "misconceptions and facts"
            rows.append({"id": r["id"], "g": grp, "correct": r["correct"], "conf": r["p_top"]})
        t = pl.DataFrame(rows)
        per = []
        for (g,), d in t.group_by("g"):
            a, ci = acc(d["correct"].to_numpy())
            per.append({"label": g, "acc": a, "ci": ci, "n": d.height,
                        "conf_wrong": float(d.filter(~pl.col("correct"))["conf"].mean()) if (~d["correct"]).any() else None})
        per.sort(key=lambda x: -x["acc"])
        m = next(p for p in per if p["label"] == "misconceptions and facts")
        s = next(p for p in per if p["label"] == "stories, myths and sayings")
        q = next(p for p in per if p["label"] == "quotes and confusable names")
        return Result(
            result=f"Jev turns down plain misconceptions {m['acc']:.0%} of the time, but on questions about stories, "
                   f"myths, proverbs and superstitions it gives the in-story answer in {1 - s['acc']:.0%} of cases (what "
                   f"do white rabbits carry? pocket watches), at {s['conf_wrong']:.0%} confidence on average. Misattributed quotes catch it {1 - q['acc']:.0%} of the time.",
            evidence=f"{t.height} questions; 90% intervals: " + "; ".join(f"{p['label']} {p['ci']}" for p in per),
            numbers={"groups": per}, n=t.height,
            chart={"type": "bars", "labels": [p["label"] for p in per], "values": [p["acc"] for p in per],
                   "marks": [p["conf_wrong"] for p in per], "mark_label": "confidence when wrong"},
            examples=seeded(t.filter(~pl.col("correct") & (pl.col("g") == s["label"]))["id"].to_list(), "story"))
    return spec, run


# ---- 9. medicine: the textbook vs the clinic -----------------------------------------------------------------------
BASIC = {"Biochemistry", "Physiology", "Anatomy", "Pathology", "Pharmacology", "Microbiology"}


def medicine():
    spec = Spec(
        id="knowledge_medicine_clinic", family="knowledge", title="Jev's medical knowledge thins out in the clinic, most in dentistry",
        question="Across 19 specialties of Indian medical entrance questions, where is Jev's medical knowledge solid "
                 "and where does it thin out?",
        why="Medical questions are a common real use, and a single average hides that a model can know biochemistry "
            "cold and still miss the clinical details that decide a treatment.",
        sourcing="Existing MedMCQA questions (Pal et al. 2022, AIIMS and NEET PG entrance exams; Apache 2.0) with their subject. "
                 "Enough: 4,900 questions, subjects with 60+ shown.",
        scoring="Accuracy per subject with 90% bootstrap intervals; basic sciences (biochemistry, physiology, anatomy, "
                "pathology, pharmacology, microbiology) vs clinical subjects; mean confidence vs accuracy per group.",
        chart="Ranked dots per subject, basic sciences and clinical subjects colored apart.",
        compared_with="MedMCQA answer keys",
        limits="Exam keys have some errors. This is exam knowledge, not clinical skill; nothing here is medical advice.",
        sources=["medmcqa"])

    def run():
        M = full_meta("medmcqa")
        rows = [{"id": r["id"], "s": M[r["id"]].get("subject"), "correct": r["correct"], "conf": r["p_top"]}
                for r, _ in rows_of("medmcqa")]
        t = pl.DataFrame(rows).with_columns(pl.col("s").is_in(list(BASIC)).alias("basic"))
        per = []
        for (s,), g in t.group_by("s"):
            if g.height >= 60:
                a, ci = acc(g["correct"].to_numpy())
                per.append({"label": s, "acc": a, "ci": ci, "n": g.height, "basic": s in BASIC})
        per.sort(key=lambda x: x["acc"])
        b, c = t.filter(pl.col("basic")), t.filter(~pl.col("basic"))
        ba, ca = float(b["correct"].mean()), float(c["correct"].mean())
        return Result(
            result=f"Jev gets basic medical science right {ba:.0%} of the time and clinical subjects {ca:.0%}, "
                   f"lowest in {per[0]['label'].lower()} ({per[0]['acc']:.0%}), {per[1]['label'].lower()} "
                   f"({per[1]['acc']:.0%}) and {per[2]['label'].lower()} ({per[2]['acc']:.0%}); on clinical questions it "
                   f"is {float(c['conf'].mean()):.0%} sure on average.",
            evidence=f"{t.height:,} questions in {len(per)} subjects; 90% intervals {boot(b['correct'].cast(float).to_numpy())} "
                     f"and {boot(c['correct'].cast(float).to_numpy())}",
            numbers={"subjects": per, "basic": ba, "clinical": ca, "clinical_conf": float(c["conf"].mean())}, n=t.height,
            chart={"type": "dots", "domain": [0.5, 1], "rows": [{"label": p["label"], "value": p["acc"], "ci": p["ci"],
                                                                  "group": "basic" if p["basic"] else "clinical"} for p in per]},
            examples=seeded(t.filter(~pl.col("correct") & (pl.col("s") == per[0]["label"]))["id"].to_list(), "med"))
    return spec, run


# ---- 10. licence exams ---------------------------------------------------------------------------------------------
def mariner_group(e: str) -> str:
    e = e.lower()
    if "rules_of_the_road" in e or "_ror" in e:
        return "rules of the road"
    if re.search(r"nav|great_lakes|river|oceans|coastal", e):
        return "navigation"
    if re.search(r"motor|steam|gas_turbine|electric|pump|oiler|refrig|engineer|general_subjects", e):
        return "engine room"
    return "deck, cargo and safety"


def licences():
    spec = Spec(
        id="knowledge_licence_exams", family="knowledge", title="Jev knows the engine room better than the rules of the road",
        question="On real US licensing question pools (ham radio, merchant mariner, citizenship), which kinds of "
                 "practical knowledge does Jev hold?",
        why="Licence pools are public, written by the licensing body, and cover knowledge people actually need for a "
            "job or a right. Within the mariner pools, textbook engineering and situational rules sit side by side.",
        sourcing="Existing questions from the FCC amateur radio pools (Technician, General, Extra), the US Coast Guard "
                 "merchant mariner question bank, and the 2025 USCIS civics test (public domain). Enough: 5,400 questions.",
        scoring="Accuracy per pool and, for the mariner bank, per area (engine room; navigation; rules of the road; deck, "
                "cargo and safety), with 90% bootstrap intervals. The passing marks (74% for FCC, 70% for USCG, 60% "
                "for USCIS) are shown as reference lines, not as a verdict.",
        chart="Dots per pool and mariner area with the passing marks as ticks.",
        compared_with="the official answer keys",
        limits="Real exams draw a sample of the pool, with figures and diagrams this corpus leaves out.",
        sources=["ham_radio_pools", "uscg_mariner", "uscis_civics"])

    def run():
        rows = []
        for name in ("ham_radio_pools", "uscg_mariner", "uscis_civics"):
            M = full_meta(name)
            for r, _ in rows_of(name):
                m = M.get(r["id"], {})
                label = (m.get("exam", "").replace("FCC Amateur ", "Ham radio: ").replace("FCC ", "Ham radio: ")
                         if name == "ham_radio_pools" else f"Mariner: {mariner_group(m.get('exam', ''))}"
                         if name == "uscg_mariner" else "US citizenship civics")
                rows.append({"id": r["id"], "g": label, "correct": r["correct"]})
        t = pl.DataFrame(rows)
        per = []
        for (g,), d in t.group_by("g"):
            a, ci = acc(d["correct"].to_numpy())
            per.append({"label": g, "acc": a, "ci": ci, "n": d.height})
        per.sort(key=lambda x: -x["acc"])
        get = lambda k: next(p for p in per if p["label"] == k)
        eng, ror, nav = get("Mariner: engine room"), get("Mariner: rules of the road"), get("Mariner: navigation")
        ham = [p for p in per if p["label"].startswith("Ham")]
        return Result(
            result=f"Jev answers the US citizenship civics questions {get('US citizenship civics')['acc']:.0%} right and "
                   f"the ham radio pools {min(p['acc'] for p in ham):.0%}-{max(p['acc'] for p in ham):.0%}. At sea it is "
                   f"stronger below deck than on the bridge: {eng['acc']:.0%} on engine-room questions, {nav['acc']:.0%} "
                   f"on navigation and {ror['acc']:.0%} on the rules of the road (who gives way to whom, which signal "
                   f"when).",
            evidence=f"{t.height:,} questions; 90% intervals: " + "; ".join(f"{p['label']} {p['ci']}" for p in per),
            numbers={"groups": per}, n=t.height,
            chart={"type": "dots", "domain": [0.5, 1], "rows": [{"label": p["label"], "value": p["acc"], "ci": p["ci"]} for p in per],
                   "ticks": {"FCC pass": 0.74, "USCG pass": 0.70}},
            examples=seeded(t.filter(~pl.col("correct") & (pl.col("g") == "Mariner: rules of the road"))["id"].to_list(), "lic"))
    return spec, run


# ---- 11. the hidden step: yes/no questions -------------------------------------------------------------------------
def hidden_step():
    spec = Spec(
        id="knowledge_hidden_step_no", family="knowledge", title="When a yes needs a hidden step, Jev says no",
        question="On yes/no questions whose answer needs an unstated step ('Could a llama birth twice during the War "
                 "in Vietnam?'), does Jev lean one way when it is unsure?",
        why="A consistent lean on hard yes/no questions changes what people hear: a model that defaults to 'no' will "
            "sound skeptical of true but non-obvious claims.",
        sourcing="Existing StrategyQA questions (Geva et al. 2021; MIT), which need an implicit chain of facts, and "
                 "BoolQ and Natural Questions yes/no questions (asked without their passage) as a direct-fact "
                 "comparison. Enough: 11,000 questions.",
        scoring="Share of questions Jev answers yes vs the share whose answer is yes; accuracy when the answer is yes "
                "vs no, with 90% bootstrap intervals, per dataset.",
        chart="Paired bars per dataset: accuracy on true-yes and true-no questions.",
        compared_with="the datasets' answer keys",
        limits="Yes/no questions are asked as Noul, which TypeSafe documents as not comparable to Choice (01-jev.md "
               "§6.8); comparisons here stay within Noul.",
        sources=["strategyqa", "boolq", "natural_questions_yn"])

    def run():
        per = []
        for name, label in (("strategyqa", "needs a hidden step (StrategyQA)"), ("boolq", "direct fact (BoolQ)"),
                            ("natural_questions_yn", "direct fact (Natural Questions)")):
            rs = [(r, js(r["truth"])) for r, _ in rows_of(name)]
            yes = [r["correct"] for r, tr in rs if tr is True]
            no = [r["correct"] for r, tr in rs if tr is False]
            says = float(np.mean([js(r["jev_dist"]).get("true", 0) > 0.5 for r, _ in rs]))
            per.append({"label": label, "yes_acc": float(np.mean(yes)), "no_acc": float(np.mean(no)),
                        "yes_ci": boot(np.asarray(yes, float)), "no_ci": boot(np.asarray(no, float)),
                        "says_yes": says, "truth_yes": len(yes) / len(rs), "n": len(rs)})
        s = per[0]
        wrong = [r["id"] for r, _ in rows_of("strategyqa") if js(r["truth"]) is True and not r["correct"]]
        return Result(
            result=f"On questions that need an unstated step, Jev says yes to {s['says_yes']:.0%} though {s['truth_yes']:.0%} "
                   f"are true: it gets the true ones right {s['yes_acc']:.0%} of the time and the false ones "
                   f"{s['no_acc']:.0%}. On direct yes/no facts the lean disappears ("
                   + "; ".join(f"{p['label'].split('(')[1][:-1]} {p['yes_acc']:.0%} vs {p['no_acc']:.0%}" for p in per[1:]) + ").",
            evidence=f"{sum(p['n'] for p in per):,} questions; StrategyQA 90% intervals {s['yes_ci']} (yes) and {s['no_ci']} (no)",
            numbers={"datasets": per}, n=sum(p["n"] for p in per),
            chart={"type": "bars2", "labels": [p["label"] for p in per], "a": [p["yes_acc"] for p in per],
                   "b": [p["no_acc"] for p in per], "a_label": "answer is yes", "b_label": "answer is no"},
            examples=seeded(wrong, "strat"))
    return spec, run


EXPERIMENTS = [calibration(), wealth(), quantities(), nature_numbers(), dating(), fame(), trivia(), story_frames(),
               medicine(), licences(), hidden_step()]
