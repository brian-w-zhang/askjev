"""Choices and judgments on new questions: fair prices and wages (Kahneman, Knetsch & Thaler 1986), human or AI
poems (Porter & Machery 2024), rules read by their words or their purpose (Struchiner et al. 2020), and forecasting
what motivates effort against 208 experts (DellaVigna & Pope 2018)."""

from __future__ import annotations

import json

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, clip, js, norm, with_meta


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes (same keys, different order)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def truth(r: dict):
    t = r.get("truth")
    return json.loads(t) if isinstance(t, str) and t else t


def p_yes(r: dict, col: str = "jev_dist") -> float | None:
    d = norm(js(r[col]) or {})
    return d.get("true") if d else None


# ---- 1. fair prices ---------------------------------------------------------------------------------------------------
FAIR_LIMITS = ("Telephone surveys of Toronto and Vancouver residents in 1984-85 (about 100-195 per scenario); the paper "
               "reports only the grouped share rating an action acceptable, so Jev's four-way answer is grouped the same "
               "way. Prices and wages are 1980s amounts.")


FAIR_LABEL = {  # short names for the KKT 1986 scenarios, for the result sentence
    "10": "marking up peanut butter already in stock", "11A": "passing on only half a cost cut",
    "11B": "keeping the price when costs fall", "12": "an apple auction in a shortage",
    "15": "auctioning the last doll before Christmas", "15U": "auctioning the last doll for UNICEF",
    "5A": "charging $200 over list in a shortage", "5B": "dropping a $200 car discount in a shortage",
    "7": "passing on a higher lettuce cost",
}


def _fair_rows() -> list[dict]:
    rows = []
    for r in with_meta("fair_prices"):
        d = robust(r)
        g = norm(js(r["people_dist"]) or {})
        rows.append({"id": r["id"], "q": r["m"]["question"], "text": r["text"], "pair": r["m"].get("pair"),
                     "jev": d.get("completely_fair", 0) + d.get("acceptable", 0),
                     "guess": (g.get("completely_fair", 0) + g.get("acceptable", 0)) if g else None,
                     "people": r["m"]["people_acceptable"]})
    return sorted(rows, key=lambda x: x["q"])


def fairness():
    spec = Spec(
        id="choices_fair_prices", family="choices", title="Is it fair to raise prices when you can? Jev vs the 1986 public",
        question="On the price and wage scenarios Kahneman, Knetsch and Thaler put to the public in 1986 (snow shovels "
                 "after a blizzard, cutting a worker's pay when others work for less), does Jev find the same actions "
                 "fair and unfair as people did?",
        why="These scenarios are the classic evidence that people hold firms to a sense of fairness: passing on costs is "
            "fine, exploiting a shortage is not. A model advising businesses or customers carries some version of that "
            "rulebook; this shows whose.",
        sourcing="New questions (sources/fair_prices): the paper's own wording for 22 scenarios (Questions 1-16) plus its "
                 "UNICEF variant of the doll auction, each rated completely fair / acceptable / unfair / very unfair as "
                 "in the survey, with the paper's share of respondents rating it acceptable.",
        collection="23 new questions, each asked as written, for 'most people', and with the four options in shuffled "
                   "orders (averaged).",
        scoring="Jev's probability on 'completely fair' or 'acceptable' vs the share of respondents; rank correlation "
                "across scenarios, mean gap with a 90% bootstrap interval, and agreement on which side of 50% each "
                "scenario falls; the scenarios where they differ most.",
        chart="A dot plot, one row per scenario ordered by people's share: people's share acceptable and Jev's.",
        compared_with="Canadian adults surveyed by telephone (Kahneman, Knetsch & Thaler 1986)",
        limits=FAIR_LIMITS, new_questions=23, sources=["fair_prices"])

    def run():
        rows = _fair_rows()
        if len(rows) < 8:
            return None
        j, p = np.array([r["jev"] for r in rows]), np.array([r["people"] for r in rows])
        rho = spearmanr(j, p).statistic
        side = float(np.mean((j > 0.5) == (p > 0.5)))
        gap = j - p
        big = sorted(rows, key=lambda r: -abs(r["jev"] - r["people"]))[:3]
        f = lambda r: f"{FAIR_LABEL.get(r['q'], clip(r['text'], 60))} ({r['jev']:.0%} vs {r['people']:.0%})"  # noqa: E731
        shovel = next((r for r in rows if r["q"] == "1"), None)
        return Result(
            result=(f"Jev is more forgiving of businesses than the 1986 public: on {len(rows)} price and wage scenarios it "
                    f"puts {abs(gap.mean()) * 100:.0f} points {'more' if gap.mean() > 0 else 'less'} on 'acceptable' on average, "
                    f"though it orders them {agree_word(rho)} like people (rank correlation {rho:.2f}) and lands on the same "
                    f"side of 50% in {side:.0%}. ")
                   + (f"Raising the price of snow shovels after a storm: acceptable {shovel['jev']:.0%} for Jev, "
                      f"{shovel['people']:.0%} for people. " if shovel else "")
                   + f"It differs most on {and_list([f(r) for r in big])} (Jev vs people).",
            evidence=f"{len(rows)} of 23 scenarios (the screen hid the other {23 - len(rows)}, mostly the wage ones), about "
                     f"100-150 respondents each; 90% interval on the mean gap {boot(gap)}",
            numbers={"rows": [{k: v for k, v in r.items() if k != "text"} for r in rows], "rho": rho, "same_side": side,
                     "mean_gap": float(gap.mean())},
            n=len(rows),
            chart={"type": "dots", "domain": [0, 1], "rows": [
                {"label": f"Q{r['q']} {clip(r['text'].split(' Please rate')[0], 48)}", "value": r["jev"], "people": r["people"],
                 "guess": r["guess"]} for r in sorted(rows, key=lambda r: r["people"])]},
            examples=[r["id"] for r in big])
    return spec, run


PAIRS = {  # pair id: (condition A, condition B, what the contrast tests)
    "incumbent_vs_new": ("2A", "2B", "cutting a current worker's wage vs paying a new hire less"),
    "cut_vs_raise": ("4A", "4B", "a 7% nominal cut vs a 5% raise under 12% inflation"),
    "surcharge_vs_discount": ("5A", "5B", "$200 over list vs dropping a $200 discount"),
    "wage_vs_bonus": ("6A", "6B", "a 10% wage cut vs dropping a 10% bonus"),
    "profit_vs_loss": ("9A", "9B", "a 5% cut while making money vs while losing money"),
    "auction_unicef": ("15", "15U", "auctioning a doll vs auctioning it for UNICEF"),
}


def fairness_frames():
    spec = Spec(
        id="choices_fair_frames", family="choices", title="The same pay cut, framed two ways: Jev vs the 1986 public",
        question="People judged the same economic outcome very differently depending on the frame: a wage cut vs an "
                 "unmatched raise, a surcharge vs a lost discount. Does Jev shift between the frames the way they did?",
        why="Kahneman, Knetsch and Thaler used these pairs to show fairness is judged against a reference point, not "
            "outcomes. A model that reads outcomes would give both frames the same answer; one that absorbed human "
            "judgments would shift like people.",
        sourcing="The six contrasts in sources/fair_prices whose two versions differ only in the frame (Questions 2, 4, "
                 "5, 6, 9 and the doll auction with and without UNICEF), with the paper's shares.",
        collection="Uses the fair_prices questions (no further calls).",
        scoring="Per pair, the effect is the share rating version B acceptable minus version A, for people and for Jev. "
                "Jev 'shows' an effect when it goes the same way and is at least half as large.",
        chart="A forest plot, one row per pair: people's effect and Jev's.",
        compared_with="Canadian adults surveyed by telephone (Kahneman, Knetsch & Thaler 1986)",
        limits=FAIR_LIMITS + " The UNICEF version's N is not reported.", sources=["fair_prices"])

    def run():
        rows = {r["q"]: r for r in _fair_rows()}
        eff = []
        for pid, (a, b, what) in PAIRS.items():
            if a in rows and b in rows:
                ep, ej = rows[b]["people"] - rows[a]["people"], rows[b]["jev"] - rows[a]["jev"]
                eff.append({"pair": pid, "what": what, "people": ep, "jev": ej,
                            "shows": bool(np.sign(ep) == np.sign(ej) and abs(ej) >= abs(ep) / 2), "ids": [rows[a]["id"], rows[b]["id"]]})
        if len(eff) < 3:
            return None
        shows = [e for e in eff if e["shows"]]
        miss = [e for e in eff if not e["shows"]]
        f = lambda e: f"{e['what']} ({e['people']:+.0%} vs {e['jev']:+.0%})"  # noqa: E731
        return Result(
            result=f"Jev shifts with the frame like people in {len(shows)} of {len(eff)} contrasts"
                   + (f"; it misses or shrinks {and_list([f(e) for e in miss])}" if miss else "")
                   + ". Effects are the change in the share rating the action acceptable, people vs Jev.",
            evidence=f"{len(eff)} paired scenarios from the 1986 survey",
            numbers={"effects": eff}, n=2 * len(eff),
            chart={"type": "forest", "zero": 0, "rows": [{"label": e["what"], "people": e["people"], "jev": e["jev"],
                                                          "hi": not e["shows"]} for e in eff]},
            examples=[i for e in eff[:2] for i in e["ids"]])
    return spec, run


# ---- 2. human or AI poems ---------------------------------------------------------------------------------------------
def poetry():
    spec = Spec(
        id="choices_ai_poetry", family="choices", title="Can Jev tell a human poem from an AI one?",
        question="Given poems by Chaucer, Shakespeare, Byron, Whitman, Dickinson and others, mixed with ChatGPT poems "
                 "written in their style, does Jev tell which are human better than the 1,634 people who took the same "
                 "test, and does it fall for the same ones?",
        why="In Porter & Machery's study people did worse than chance: the AI poems, plainer and more regular, read as "
            "human, and the real ones, stranger, read as machine-made. A model is an interesting judge of its own kind.",
        sourcing="New questions (sources/ai_poetry): the study's wording and poems for the seven poets whose real poems "
                 "are in the public domain (Chaucer, Shakespeare, Samuel Butler, Byron, Whitman, Dickinson, early Eliot), "
                 "5 human and 5 AI poems each, with the study's split of answers per poem (about 160 people each).",
        collection="70 new questions, each asked as written, for 'most people', and with the two options in both orders "
                   "(averaged).",
        scoring="Share of poems where Jev's more likely answer is right, vs the crowd's majority and vs the average "
                "person (the share of people right per poem); the share saying 'human' for real vs AI poems, for Jev "
                "and people; per poet.",
        chart="Paired bars: the share of poems called human, for real poems and for AI poems, people vs Jev.",
        compared_with="US adults in Porter & Machery 2024, Study 1 (about 160 judgments per poem)",
        limits="Only public-domain poets are used, so the modern poets where people did worst (by the paper's account) "
               "are not in this set. The AI poems came from ChatGPT 3.5 in 2023; Jev may have seen the real poems in "
               "training, which helps it recognize them: read the result as recognizing famous poems plus spotting 2023-era ChatGPT style, not as a pure test of judgment. Line breaks were lost in the study's text export; poems are "
               "shown as running text to Jev.", new_questions=70, sources=["ai_poetry"])

    def run():
        rows = []
        for r in with_meta("ai_poetry"):
            d = robust(r)
            h = norm(biggest(r["humans"])["dist"])
            t = truth(r)
            rows.append({"id": r["id"], "poet": r["m"]["poet"], "truth": t, "jev_human": d.get("human", 0),
                         "ppl_human": h.get("human", 0), "jev_right": (d.get("human", 0) > 0.5) == (t == "human"),
                         "crowd_right": (h.get("human", 0) > 0.5) == (t == "human"), "person_right": h.get(t, 0)})
        t = pl.DataFrame(rows)
        if t.height < 20:
            return None
        acc, crowd, person = float(t["jev_right"].mean()), float(t["crowd_right"].mean()), float(t["person_right"].mean())
        by = t.group_by("truth").agg(pl.col("jev_human").mean(), pl.col("ppl_human").mean()).to_dicts()
        hu = next(b for b in by if b["truth"] == "human")
        ai = next(b for b in by if b["truth"] == "ai")
        poets = t.group_by("poet").agg(pl.col("jev_right").mean(), pl.col("person_right").mean()).sort("jev_right", "poet").to_dicts()
        return Result(
            result=f"Jev tells human from AI poems in {acc:.0%} of {t.height}, where the crowd's majority gets {crowd:.0%} and the "
                   f"average person {person:.0%}. People call AI poems human {ai['ppl_human']:.0%} of the time and real "
                   f"ones {hu['ppl_human']:.0%}; Jev puts {ai['jev_human']:.0%} and {hu['jev_human']:.0%} on 'human'. It "
                   f"does worst on {poets[0]['poet']} ({poets[0]['jev_right']:.0%}) and best on "
                   + and_list([p["poet"] for p in poets if p["jev_right"] == poets[-1]["jev_right"]])
                   + f" ({poets[-1]['jev_right']:.0%}).",
            evidence=f"{t.height} of 70 poems (the screen hid {70 - t.height}) by {t['poet'].n_unique()} poets, about 160 judgments each; 90% interval on Jev's "
                     f"accuracy {boot(t['jev_right'].cast(float).to_numpy())}",
            numbers={"acc": acc, "crowd": crowd, "person": person, "by_truth": by, "poets": poets}, n=t.height,
            chart={"type": "bars2", "labels": ["real poems called human", "AI poems called human"],
                   "a": [hu["ppl_human"], ai["ppl_human"]], "b": [hu["jev_human"], ai["jev_human"]],
                   "a_label": "people", "b_label": "Jev"},
            examples=t.filter(~pl.col("jev_right"))["id"].to_list()[:3])
    return spec, run


# ---- 3. rules: text or purpose ----------------------------------------------------------------------------------------
def rules():
    spec = Spec(
        id="choices_rule_text_vs_purpose", family="choices", title="No dogs in the restaurant: does Jev read a rule by its words or its purpose?",
        question="When a rule's words and its purpose come apart (a quiet dog in a purse under 'no dogs', a motorbike "
                 "under 'no cars in the park'), does Jev judge the rule broken by the text or by the purpose, compared "
                 "with people?",
        why="This is the oldest puzzle in legal philosophy (Hart's 'no vehicles in the park'). People mix the two, "
            "leaning on the text. A model that follows instructions literally, or by their intent, shows it here.",
        sourcing="New questions (sources/vehicles_park): the stimuli of Struchiner, Hannikainen & Almeida 2020, Study 1 "
                 "(8 cases under 'no dogs in the restaurant') and Study 2 (four rules, each with a core case, one where "
                 "only the text is broken, one where only the purpose is, and one where neither is), 'Did the person "
                 "break the rule?', with the share of respondents who said yes.",
        collection="22 new yes/no questions, each asked as written and for 'most people'.",
        scoring="Per case, Jev's probability of 'broken' vs the share of people; rank correlation; mean by kind of case: "
                "text broken but purpose kept (overinclusion), purpose broken but text kept (underinclusion). A reader "
                "who goes by the text says yes to the first and no to the second.",
        chart="Dots per case, grouped by kind: people's share and Jev's probability of 'the rule was broken'.",
        compared_with="Brazilian adults (Struchiner, Hannikainen & Almeida 2020, Studies 1 and 2)",
        limits="Participants answered in Portuguese; Jev reads the authors' English translation. About 45-50 people per "
               "case in Study 2 and 130-140 in Study 1.", new_questions=22, sources=["vehicles_park"])

    def run():
        rows = []
        for r in with_meta("vehicles_park"):
            j, h = p_yes(r), norm(biggest(r["humans"])["dist"]).get("true", 0)
            if j is None:
                continue
            tb, pb = r["m"].get("text_broken"), r["m"].get("purpose_broken")
            kind = ("both" if tb and pb else "text only" if tb and pb is False else "purpose only" if pb and tb is False
                    else "neither" if tb is False and pb is False else "unclear")
            rows.append({"id": r["id"], "case": r["m"]["case"], "rule": r["m"]["rule"], "kind": kind, "jev": j, "people": h,
                         "guess": p_yes(r, "people_dist"), "text": r["text"].split("\n\n")[1]})
        t = pl.DataFrame(rows)
        if t.height < 10:
            return None
        rho = spearmanr(t["jev"], t["people"]).statistic
        by = {k: (float(g["jev"].mean()), float(g["people"].mean()), g.height) for (k,), g in t.group_by("kind")}
        to, po = by.get("text only"), by.get("purpose only")
        big = t.with_columns((pl.col("jev") - pl.col("people")).abs().alias("g")).sort("g", descending=True).head(2).to_dicts()
        return Result(
            result=f"Jev judges rules {agree_word(rho)} like people (rank correlation {rho:.2f} over {t.height} cases)"
                   + (f". When only the words are broken (a quiet dog in a purse, a toy car), Jev says the rule was broken "
                      f"{to[0]:.0%} of the time on average, people {to[1]:.0%}; when only the purpose is (a robot dog, a "
                      f"motorbike), {po[0]:.0%} vs {po[1]:.0%}" if to and po else "")
                   + ". Biggest gaps: " + and_list([f"{clip(b['text'], 60)} ({b['jev']:.0%} vs {b['people']:.0%})" for b in big]) + ".",
            evidence=f"{t.height} of 22 cases (the screen hid {22 - t.height}), 45-141 people each",
            numbers={"rows": [{k: v for k, v in r.items()} for r in rows], "rho": rho, "by_kind": by}, n=t.height,
            chart={"type": "dots", "domain": [0, 1], "rows": [
                {"label": clip(r["text"], 46), "value": r["jev"], "people": r["people"], "guess": r["guess"], "group": r["kind"]}
                for r in sorted(rows, key=lambda r: (r["kind"], r["people"]))]},
            examples=[b["id"] for b in big])
    return spec, run


# ---- 4. what motivates effort -----------------------------------------------------------------------------------------
def effort():
    spec = Spec(
        id="choices_effort_forecast", family="choices", title="Forecasting what motivates effort: Jev vs 208 experts",
        question="Told how hard online workers typed with no bonus, 1 cent and 10 cents per 100 points, can Jev forecast "
                 "how hard they worked under 15 other incentives (charity, deadlines, losses, lotteries, praise) better "
                 "than the 208 economists and psychologists who forecast the same study?",
        why="DellaVigna and Pope asked experts to predict their experiment before revealing it: the experts were good at "
            "the order but underrated how well tiny piece rates work. Predicting what moves people is exactly the kind "
            "of advice a model gets asked for.",
        sourcing="New questions (sources/effort_forecasts): the 15 treatments of DellaVigna & Pope 2018 (about 550 MTurk "
                 "workers each), each with the paper's mean score and the experts' mean forecast (Table 4). Jev gets the "
                 "three benchmark results the experts got and answers in 50-point bins.",
        collection="15 new questions, each asked as written and with the bins in shuffled orders (averaged).",
        scoring="Jev's forecast = the expected score over its bins (bin midpoints). Against the actual means: mean "
                "absolute error and rank correlation, the same for the experts' mean forecast; the treatments where each "
                "misses most.",
        chart="A scatter: actual mean score (x) vs forecast (y), Jev and the experts, with the diagonal.",
        compared_with="The actual scores (9,861 MTurk workers) and 208 experts' mean forecasts",
        limits="15 treatments; the experts' number is their average, which is usually better than a single expert "
               "(the paper's wisdom-of-crowds finding). Jev may have read the paper.", new_questions=15,
        sources=["effort_forecasts"])

    def run():
        rows = []
        for r in with_meta("effort_forecasts"):
            d = robust(r)
            opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
            mid = {k: (1475 if k == "under_1500" else 2325 if k == "over_2300" else int(k[1:]) + 25) for k in opts}
            est = sum(mid[k] * v for k, v in d.items() if k in mid)
            w = r["text"].split("Another group's paragraph said: ")[1].split("\n\nWhat")[0].strip('"')
            rows.append({"id": r["id"], "cat": r["m"]["category"], "wording": w, "actual": r["m"]["effort"],
                         "jev": est, "experts": r["m"]["expert_forecast"]})
        t = pl.DataFrame(rows)
        if t.height < 8:
            return None
        mae_j = float((t["jev"] - t["actual"]).abs().mean())
        mae_e = float((t["experts"] - t["actual"]).abs().mean())
        rj, re_ = spearmanr(t["jev"], t["actual"]).statistic, spearmanr(t["experts"], t["actual"]).statistic
        miss = t.with_columns((pl.col("jev") - pl.col("actual")).alias("e")).sort(pl.col("e").abs(), descending=True).head(2).to_dicts()
        return Result(
            result=f"Jev's forecasts miss the actual scores by {mae_j:.0f} points on average; the experts' average forecast "
                   f"misses by {mae_e:.0f}. Jev orders the 15 incentives {agree_word(rj)} like the results (rank "
                   f"correlation {rj:.2f}; experts {re_:.2f}). Its biggest misses: "
                   + and_list([f"{clip(m['wording'], 60)} ({m['jev']:.0f} forecast vs {m['actual']} actual)" for m in miss]) + ".",
            evidence="15 treatments, about 550 workers each; experts: mean of 208 forecasts per treatment",
            numbers={"rows": rows, "mae_jev": mae_j, "mae_experts": mae_e, "rho_jev": rj, "rho_experts": re_}, n=t.height,
            chart={"type": "scatter", "points": [[r["actual"], round(r["jev"])] for r in rows],
                   "points_people": [[r["actual"], r["experts"]] for r in rows], "diagonal": True,
                   "x": "actual mean score", "y": "forecast (Jev; people = experts' mean)",
                   "labels": [{"label": clip(m["wording"], 30), "x": m["actual"], "y": m["jev"]} for m in miss]},
            examples=[m["id"] for m in miss])
    return spec, run


# fairness_frames() is cut: the screen hid one side of every framing pair, so no contrast can be computed.
EXPERIMENTS = [fairness(), poetry(), rules(), effort()]
