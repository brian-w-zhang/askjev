"""Moral judgment experiments: trolley weights, everyday norms, AITA verdicts, wrongness of vignettes, the Many Labs
framing classics, clear vs ambiguous dilemmas."""

from __future__ import annotations

import json
from functools import lru_cache
from itertools import groupby

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import A, Result, Spec, agree_word, biggest, boot, js, jsd, level, norm, seeded, source, top


@lru_cache(maxsize=1)
def ledger() -> dict:
    return {c["id"]: c for c in json.loads((A / "findings.json").read_text())["claims"]}


MM = [("intervention_avoided", "Staying the course (not swerving)"), ("more_lives", "More lives"), ("humans_over_pets", "Humans over pets"),
      ("young_over_old", "The young over the old"), ("fit_over_large", "The fit over the large"), ("female_over_male", "Women over men"),
      ("high_status", "High status over low"), ("lawful_over_jaywalking", "The lawful over jaywalkers"),
      ("passengers_over_pedestrians", "Passengers over pedestrians")]


def _and(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def moral_machine():
    spec = Spec(
        id="moral_machine", family="moral", title="Who Jev saves in the Moral Machine",
        question="In the Moral Machine's self-driving-car dilemmas, which factors pull Jev toward sparing one side, and "
                 "how does that compare with millions of players?",
        why="The largest study of machine ethics preferences (Awad et al. 2018, Nature) measured what people want a car "
            "to do; a model answering the same dilemmas shows which of those preferences it shares and which it drops.",
        sourcing="Existing Moral Machine scenarios (26,020 shown dilemmas reconstructed from the study's data), each "
                 "with the real players' split, for the world and 10 countries. Enough.",
        scoring="The study's own regression: for each factor, the change in the probability of sparing a side per unit "
                "difference (AMCE), fitted to Jev's probabilities and to players' shares; 90% intervals by bootstrap over "
                "scenarios. Countries compared by distance of their nine-factor profile to Jev's.",
        chart="Effect dot plot: one row per factor, players (diamond) and Jev (square) with intervals, zero line; the "
              "rows where Jev drops a human preference highlighted.",
        compared_with="Moral Machine players worldwide (millions of decisions) and in 10 countries",
        limits="Players chose; Jev gives probabilities. The factor list is the study's; the scenarios are the study's "
               "templates, so wording effects are shared.", sources=["moral_machine"])

    def run():
        L = ledger()
        rows = []
        for k, lab in MM:
            c = L.get(f"mm_{k}")
            if c:
                rows.append({"label": lab, "jev": c["effect"], "ci": c["ci90"], "people": c["people"]["effect"],
                             "people_ci": c["people"]["ci90"], "countries": c.get("countries", {})})
        dropped = [r for r in rows if abs(r["people"]) >= 0.04 and abs(r["jev"]) < abs(r["people"]) / 2]
        lives = next(r for r in rows if r["label"] == "More lives")
        return Result(
            result=f"Jev weighs the number of lives more than players do ({lives['jev']:+.2f} vs {lives['people']:+.2f}), "
                   f"but drops {len(dropped)} preferences they show: " + ", ".join(
                       f"{r['label'].lower()} ({r['jev']:+.2f} vs {r['people']:+.2f})" for r in dropped) + ".",
            evidence="26,020 dilemmas; 90% intervals by bootstrap over scenarios",
            numbers={"factors": rows, "dropped": [r["label"] for r in dropped]}, n=26020,
            chart={"type": "effects", "rows": [{"label": r["label"], "value": r["jev"], "ci": r["ci"], "people": r["people"],
                                                 "people_ci": r["people_ci"], "hi": r in dropped} for r in rows], "zero": 0},
            examples=L["mm_more_lives"]["examples"][:3])
    return spec, run


LEVELS5 = ["practically no one", "a small minority", "about half", "a clear majority", "practically everyone"]


def norms():
    spec = Spec(
        id="moral_norms", family="moral", title="Jev thinks everyday rules are more universal than people do",
        question="For 25,000 rules of thumb ('It's rude to...', 'You should...'), how many people does Jev think agree, "
                 "compared with the annotators' estimates?",
        why="Social Chemistry 101 is a map of everyday morality. Knowing the rules is one thing; knowing which ones "
            "people actually argue about is another, and a model that thinks every rule is shared will sound preachy.",
        sourcing="Existing Social Chemistry 101 questions ('How many people would agree: \"<rule>\"?', five described "
                 "levels from 'practically no one' to 'practically everyone'), each with the annotator's estimate. "
                 "Enough: 25,000 rules.",
        scoring="The share of rules at each level for Jev (its most likely level) and for annotators; Jev's mean level "
                "for the rules annotators put at each level; rank correlation over all rules with a 90% bootstrap "
                "interval on the mean gap; the gap by topic.",
        chart="Paired bars: the share of rules at each of the five levels, annotators vs Jev.",
        compared_with="Social Chemistry 101 crowd annotators (one estimate per rule)",
        limits="Each rule has one annotator, and their estimate is itself a guess about people. The rules were written "
               "from Reddit and advice columns by the dataset's authors.", sources=["social_chem"])

    def run():
        q = source("social_chem")
        rows = []
        for r in q.iter_rows(named=True):
            h = biggest(r["humans"])
            if h:
                d = js(r["jev_dist"])
                rows.append({"id": r["id"], "topic": r["l2"].split(".")[-1].replace("_", " "), "jev": level(d),
                             "people": level(h["dist"]), "jt": int(top(d)), "pt": int(top(h["dist"]))})
        t = pl.DataFrame(rows)
        rho = spearmanr(t["jev"], t["people"]).statistic
        share = lambda col: [float((t[col] == i).mean()) for i in range(5)]
        sj, sp = share("jt"), share("pt")
        by_level = [{"level": LEVELS5[i], "jev": float(g["jev"].mean()), "n": g.height} for i in range(5)
                    if (g := t.filter(pl.col("pt") == i)).height]
        topics = t.group_by("topic").agg(pl.len().alias("n"), (pl.col("jev") - pl.col("people")).mean().alias("gap")) \
                  .filter(pl.col("n") >= 200).sort("gap").to_dicts()
        half = next(b for b in by_level if b["level"] == "about half")
        gap = t["jev"].to_numpy() - t["people"].to_numpy()
        return Result(
            result=f"Jev says practically everyone agrees with {sj[4]:.0%} of everyday rules; the annotators say so for "
                   f"{sp[4]:.0%}. Rules the annotators thought split people about half and half, Jev places at "
                   f"{half['jev']:.1f} on a 0-4 scale, between half and a clear majority. It still orders the rules "
                   f"{agree_word(rho)} like them (rank correlation {rho:.2f}).",
            evidence=f"{t.height:,} rules; mean gap {gap.mean():+.2f} levels, 90% interval {boot(gap)}",
            numbers={"rho": rho, "share_jev": sj, "share_annotators": sp, "by_level": by_level, "topics": topics},
            n=t.height, robustness=("The gap is positive in every topic with 200+ rules" if topics[0]["gap"] > 0 else
                                    "The gap varies by topic") + f" ({topics[0]['topic']} {topics[0]['gap']:+.2f} to "
                                    f"{topics[-1]['topic']} {topics[-1]['gap']:+.2f}).",
            chart={"type": "bars2", "labels": LEVELS5, "a": sp, "b": sj, "a_label": "annotators", "b_label": "Jev"},
            examples=seeded(t.filter((pl.col("pt") == 2) & (pl.col("jt") == 4))["id"].to_list(), "norms"))
    return spec, run


def aita():
    spec = Spec(
        id="moral_aita", family="moral", title="Am I the asshole? Jev says nobody is",
        question="Given real r/AmItheAsshole stories, does Jev give the same verdict as the Reddit crowd, and whom does "
                 "it blame?",
        why="AITA is where millions of people argue about everyday ethics; it has messy stories and real verdict "
            "splits, and a model's lean (blaming the writer, or everyone, or asking for more info) is revealing.",
        sourcing="Existing Scruples anecdotes (real AITA posts, attached as the story) with the distribution of "
                 "verdicts from top-level comments. Enough: ~6,800 shown stories.",
        scoring="Agreement with the crowd's majority verdict; Jev's verdict mix vs the crowd's; agreement split by how "
                "divided the crowd was (entropy tertiles); 90% intervals by bootstrap over stories.",
        chart="Paired stacked bars of verdict mix (crowd vs Jev), and agreement by how divided the crowd was.",
        compared_with="r/AmItheAsshole commenters (verdict counts per story)",
        limits="Reddit commenters are not a representative sample; verdicts come from comment counts.",
        sources=["scruples_anecdotes"])

    def run():
        q = source("scruples_anecdotes")
        rows = []
        for r in q.iter_rows(named=True):
            h = biggest(r["humans"])
            if not h or (h.get("n") or 0) < 3:
                continue
            hd, jd = norm(h["dist"]), js(r["jev_dist"])
            ent = -sum(p * np.log2(p) for p in hd.values() if p > 0)
            rows.append({"id": r["id"], "agree": top(jd) == top(hd), "jev": top(jd), "crowd": top(hd), "ent": ent})
        t = pl.DataFrame(rows)
        mix_j = t["jev"].value_counts(normalize=True).sort("jev").to_dicts()
        mix_c = t["crowd"].value_counts(normalize=True).sort("crowd").to_dicts()
        t = t.with_columns(pl.col("ent").qcut(3, labels=["clear", "mixed", "split"]).alias("div"))
        by = t.group_by("div").agg(pl.col("agree").mean()).sort("div").to_dicts()
        a = t["agree"].mean()
        fav = {m["jev"]: m["proportion"] for m in mix_j}
        cfav = {m["crowd"]: m["proportion"] for m in mix_c}
        return Result(
            result=f"Jev says nobody is in the wrong in {fav.get('nobody', 0):.0%} of r/AmItheAsshole stories; Reddit says "
                   f"so in {cfav.get('nobody', 0):.0%}. The difference comes out of 'not the asshole': Reddit clears the "
                   f"writer and blames the other side in {cfav.get('other', 0):.0%} of stories, Jev in "
                   f"{fav.get('other', 0):.0%}. It gives Reddit's verdict {a:.0%} of the time, "
                   f"{by[0]['agree']:.0%} when the crowd was clear.",
            evidence=f"{t.height:,} stories with 3+ verdicts; 90% interval on agreement {boot(t['agree'].cast(float).to_numpy())}",
            numbers={"agree": a, "mix_jev": mix_j, "mix_crowd": mix_c, "by_division": by}, n=t.height,
            chart={"type": "mix", "jev": mix_j, "crowd": mix_c, "by": by},
            examples=seeded(t.filter(~pl.col("agree"))["id"].to_list(), "aita"))
    return spec, run


def vignettes():
    spec = Spec(
        id="moral_vignettes", family="moral", title="How wrong is it? Jev is softer, most on disloyalty",
        question="Rating short scenes of wrongdoing (harm, cheating, disloyalty, disrespect, impurity, oppression), how "
                 "wrong does Jev find each kind compared with people?",
        why="Moral Foundations Theory predicts people split on loyalty, authority and purity; a model may condemn harm "
            "like people but shrug at purity, or the reverse.",
        sourcing="Existing Moral Foundations Vignettes (Clifford et al. 2015 items, validation data from Hopp et al. "
                 "2024 Prolific samples), five described wrongness levels. Enough: ~200 vignettes.",
        scoring="Per foundation, Jev's mean expected wrongness vs people's, with 90% bootstrap intervals over vignettes; "
                "rank correlation over vignettes.",
        chart="Paired dots per foundation, people vs Jev, with intervals; the three vignettes with the largest gap.",
        compared_with="Prolific adults rating the same vignettes (Hopp et al. 2024)",
        limits="Samples are Dutch and US Prolific adults; wrongness scale anchors are described situations.",
        sources=["moral_vignettes"])

    def run():
        q = source("moral_vignettes")
        rows = []
        for r in q.iter_rows(named=True):
            h = biggest(r["humans"])
            m = js(r["meta"]) or {}
            if h:
                rows.append({"id": r["id"], "text": r["text"], "f": m.get("foundation", "?"), "jev": level(js(r["jev_dist"])), "people": level(h["dist"])})
        t = pl.DataFrame(rows)
        by = [{"f": f, "jev": float(g["jev"].mean()), "people": float(g["people"].mean()), "n": g.height,
               "ci": boot(g["jev"].to_numpy() - g["people"].to_numpy())} for (f,), g in t.group_by("f")]
        by.sort(key=lambda x: x["jev"] - x["people"])
        rho = spearmanr(t["jev"], t["people"]).statistic
        lo = by[0]
        return Result(
            result=f"Jev orders the scenes by wrongness {agree_word(rho)} like people (rank correlation {rho:.2f}) but "
                   f"finds them less wrong in {sum(b['ci'][1] < 0 for b in by)} of {len(by)} foundations, most of all "
                   f"{lo['f'].replace('_', ' ')} ({lo['jev']:.2f} vs {lo['people']:.2f} on a 0-4 scale); only "
                   + _and([b['f'].replace('_', ' ') for b in by if b['ci'][1] >= 0]) + " come out even.",
            evidence=f"{t.height} vignettes; 90% intervals over vignettes", numbers={"by": by, "rho": rho}, n=t.height,
            chart={"type": "dots", "domain": [0, 4], "rows": [{"label": b["f"], "value": b["jev"], "people": b["people"]} for b in by]},
            examples=seeded(t["id"].to_list(), "mfv"))
    return spec, run


def _item(prefix: str) -> dict:
    """A behavioral_econ item by id prefix: Jev's and people's distributions, plus its level count."""
    r = next(r for r in source("behavioral_econ").iter_rows(named=True) if r["id"].startswith(prefix))
    return {"id": r["id"], "jev": norm(js(r["jev_dist"])), "people": norm(biggest(r["humans"])["dist"]),
            "src": biggest(r["humans"])["source"].split(",")[0].split(" (")[0]}


def _measure(it: dict, who: str, key: str | None) -> float:
    """Share choosing `key`, or (key None) the expected level scaled to 0-1."""
    d = it[who]
    if key is not None:
        return 1 - d.get(key[1:], 0.0) if key.startswith("!") else d.get(key, 0.0)
    return level(d) / (len(d) - 1)


def _effects(paradigms):
    rows = []
    for label, cite, a, b, key, what in paradigms:
        A, B = _item(a), _item(b)
        ka, kb = (key, key) if not isinstance(key, tuple) else key
        e = {w: _measure(A, w, ka) - _measure(B, w, kb) for w in ("people", "jev")}
        shows = abs(e["people"]) >= 0.1 and np.sign(e["jev"]) == np.sign(e["people"]) and abs(e["jev"]) >= abs(e["people"]) / 2
        rev = abs(e["people"]) >= 0.1 and np.sign(e["jev"]) != np.sign(e["people"]) and abs(e["jev"]) >= 0.1
        rows.append({"label": label, "cite": cite, "what": what, "people": e["people"], "jev": e["jev"], "shows": bool(shows),
                     "reversed": bool(rev), "ids": [A["id"], B["id"]], "src": A["src"]})
    return rows


CLASSICS = [
    ("Asian disease: saving vs dying", "Tversky & Kahneman 1981", "4024854c6e", "9db65de4e1", "program_a",
     "choosing the sure program when framed as lives saved, minus when framed as deaths"),
    ("Relative savings: $10 off $30 vs off $250", "Tversky & Kahneman 1981", "1c54bf552f", "e5840e0d59", "true",
     "driving 20 minutes to save $10 on a $30 item, minus on a $250 item"),
    ("Less is better: a $90 scarf vs a $110 coat", "Hsee 1998", "14ff64a112", "68a2735a24", None,
     "how generous the friend seems (0-1) with the pricey scarf, minus the cheap coat"),
    ("Sunk cost: a paid ticket vs a free one", "Arkes & Blumer 1985", "4f2f69bf09", "64369f984e", None,
     "leaning toward going out in the cold (0-1) with a paid ticket, minus a free one"),
    ("Side-effect intent: harmed vs helped", "Knobe 2003", "df6203f1b6", "b99a0125bd", None,
     "agreeing the chairman acted intentionally (0-1) when he harmed the environment, minus when he helped it"),
    ("Side-effect blame: blame vs praise", "Knobe 2003", "6074835057", "3cc0884859", None,
     "blame for the harm (0-1), minus praise for the help"),
    ("Trolley: switch vs push", "Hauser et al. 2007", "a70803c520", "23fd781eac", "true",
     "saying it's permissible to switch the track, minus to push the man"),
    ("Trolley loop: side effect vs means", "Hauser et al. 2007", "b191cbb072", "b2638c8afd", "true",
     "permissible when the man dies as a side effect, minus when his body is the brake"),
    ("Scale range: TV hours", "Schwarz et al. 1985", "6ffd921aae", "18ca4a2d51",
     ("!up_to_two_and_a_half_hours", "more_than_two_and_a_half_hours"),
     "reporting more than 2.5 hours of TV when the scale runs high, minus when it runs low"),
    ("Tempting fate: unprepared vs prepared", "Risen & Gilovich 2008", "0a203033ea", "433d100def", None,
     "expecting to be called on (0-1) after skipping the reading, minus after doing it"),
    ("Affect: a kiss for sure vs at 1%", "Rottenstreich & Hsee 2001", "3677b7a3fe", "8dd2097c45",
     ("meet_and_kiss_my_favorite_movie_star", "1_percent_chance_to_kiss_my_favorite_movie_star"),
     "choosing the kiss over $50 when certain, minus in a 1% lottery"),
    ("Enriched option: award vs deny custody", "Shafir 1993", "8887244bf3", "327d506735", ("parent_b", "parent_a"),
     "awarding custody to the vivid parent B, minus denying it to plain parent A (zero if consistent)"),
]

PROSPECT = [
    ("Reflection: a sure $6,000 vs 80% of $8,000", "1660ad0c35", "f1e7e31752",
     ("6000_dollars_for_sure", "lose_6000_dollars_for_sure"), "taking the sure thing for gains, minus for losses"),
    ("Reflection: 90% of $6,000 vs 45% of $12,000", "f48708398e", "0ebf940c9a",
     ("90_percent_chance_of_6000", "90_percent_chance_to_lose_6000"), "taking the likelier option for gains, minus for losses"),
    ("Reflection at small odds: $10 vs 0.1% of $10,000", "6f54953514", "8dfc749af8",
     ("10_dollars_for_sure", "lose_10_dollars_for_sure"), "taking the sure $10 for gains, minus for losses"),
    ("Reflection at small odds: 0.2% vs 0.1%", "4ad76fd42a", "e257d8ea3f",
     ("0_2_percent_chance_of_6000", "0_2_percent_chance_to_lose_6000"), "taking the likelier option for gains, minus for losses"),
    ("Framing: given $2,000 and gain vs given $4,000 and lose", "94ccc096c1", "73ecec1891",
     ("1000_more_for_sure", "lose_1000_dollars_for_sure"), "taking the sure option; the final amounts are identical"),
    ("Certainty: a sure $4,800 vs the same odds scaled down", "dddcae176a", "96cac9cd88",
     ("4800_dollars_for_sure", "34_percent_chance_of_4800"), "choosing the $4,800 side when it is certain, minus when it isn't"),
    ("Isolation: a two-stage game vs its one-stage twin", "2b183001df", "a1bb008453",
     ("6000_dollars_for_sure", "25_percent_chance_of_6000"), "choosing the $6,000 side in the two-stage game, minus in the equivalent one-stage game"),
    ("Segregation: one $12,000 prize vs split prizes, gains vs losses", "3715ab0372", "02099924ed",
     ("25_percent_8000_or_25_percent_4000", "25_percent_lose_8000_or_25_percent_lose_4000"),
     "choosing the split option for gains, minus for losses"),
]


def classics():
    spec = Spec(
        id="judgment_classics", family="judgment", title="Psychology's classic effects, re-run on Jev",
        question="Take the famous framing and judgment effects that Many Labs re-ran on thousands of people. Does "
                 "Jev shift when only the framing changes, the way people do?",
        why="These are the textbook results about how human judgment bends (framing, sunk cost, the side-effect "
            "effect, trolley problems). A model trained on human text might inherit them, erase them, or overdo them.",
        sourcing="Existing Many Labs 1 and 2 items (Klein et al. 2014, 2018) with item-level answer distributions "
                 "from about 3,000-4,000 people per item; both conditions of each paradigm are in the corpus as "
                 "separate questions. Paired by hand, 12 paradigms. Enough.",
        scoring="For each paradigm, the effect is the difference between the two conditions: in the share choosing "
                "the key option, or in the mean level scaled to 0-1. Jev 'shows' an effect when it goes the same way "
                "as people and is at least half as large (people's effect at least 0.10); 'reversed' when it goes "
                "the other way by 0.10 or more.",
        chart="A forest plot: one row per paradigm, people's effect and Jev's side by side around zero.",
        compared_with="Many Labs 1 and 2 participants (thousands per item, dozens of labs)",
        limits="Each condition is one question, asked once; people saw one condition, Jev answers both separately "
               "without seeing the other. Some effects are small or failed to replicate in people too (custody, "
               "affect), and are shown as such.", sources=["behavioral_econ"])

    def run():
        rows = _effects([(l, c, a, b, k, w) for l, c, a, b, k, w in CLASSICS])
        real = [r for r in rows if abs(r["people"]) >= 0.1]
        shows = [r for r in real if r["shows"]]
        rev = [r for r in real if r["reversed"]]
        missed = [r for r in real if not r["shows"] and not r["reversed"]]
        f = lambda rs: ", ".join(f"{r['label'].split(':')[0]} ({r['people']:+.2f} vs {r['jev']:+.2f})" for r in rs)
        big = [r for r in shows if abs(r["jev"]) >= 1.3 * abs(r["people"])]
        return Result(
            result=f"Of {len(real)} classic effects that showed up in people, Jev reproduces {len(shows)}"
                   + (f", {len(big)} of them more strongly than people ({f(big)})" if big else "")
                   + (f". It shows none of {f(missed)}" if missed else "")
                   + (f", and reverses {f(rev)}" if rev else "") + ". Numbers are people's effect vs Jev's.",
            evidence=f"{len(rows)} paradigms, 2 questions each; people's effects from Many Labs (thousands per item). "
                     "Numbers are people's effect vs Jev's.",
            numbers={"effects": rows}, n=2 * len(rows),
            chart={"type": "forest", "rows": [{"label": r["label"], "people": r["people"], "jev": r["jev"],
                                                "hi": r["reversed"] or (r in missed)} for r in rows], "zero": 0},
            examples=rows[0]["ids"])
    return spec, run


def prospect():
    spec = Spec(
        id="risk_prospect_theory", family="risk", title="Prospect theory, re-run on Jev",
        question="On the gamble choices that founded prospect theory, re-run in 19 countries in 2020, does Jev "
                 "choose like people?",
        why="Kahneman and Tversky's 1979 problems show people play safe with gains and gamble with losses. Whether a "
            "model does the same says a lot about the advice it gives on money and risk.",
        sourcing="Existing items from Ruggeri et al. 2020 (4,098 people in 19 countries), 17 choices between gambles, "
                 "paired by hand into 8 effects. Enough.",
        scoring="For each effect, the difference in the share choosing the key option between the two versions, for "
                "people and for Jev; also, on the choices whose expected values differ, how often each side picks "
                "the higher expected value.",
        chart="A forest plot of the 8 effects, people vs Jev, plus a 2x2 of the headline pair (sure thing vs gamble, "
              "gains vs losses).",
        compared_with="Ruggeri et al. 2020, 4,098 people in 19 countries",
        limits="Hypothetical money for both; Jev's answers are probabilities over the two options. The countries are "
               "pooled.", sources=["behavioral_econ"])

    def run():
        rows = _effects([(l, "Kahneman & Tversky 1979; Ruggeri et al. 2020", a, b, k, w) for l, a, b, k, w in PROSPECT])
        real = [r for r in rows if abs(r["people"]) >= 0.1]
        shows = [r for r in real if r["shows"]]
        rev = [r for r in real if r["reversed"]]
        g, l_ = _item("1660ad0c35"), _item("f1e7e31752")
        # choices whose expected values differ by more than 2%: (prefix, higher-EV option)
        ev = [("1660ad0c35", "80_percent_chance_of_8000"), ("f1e7e31752", "lose_6000_dollars_for_sure"),
              ("a1bb008453", "20_percent_chance_of_8000"), ("28b4d9947d", "25_percent_chance_to_lose_6000"),
              ("2b183001df", "80_percent_chance_of_8000"), ("96cac9cd88", "33_percent_chance_of_5000")]
        evj = float(np.mean([_item(p)["jev"].get(k, 0) > 0.5 for p, k in ev]))
        evp = float(np.mean([_item(p)["people"].get(k, 0) > 0.5 for p, k in ev]))
        return Result(
            result=f"Jev reverses the reflection effect at the heart of prospect theory. Offered $6,000 for sure or an 80% "
                   f"shot at $8,000, people take the sure thing ({g['people']['6000_dollars_for_sure']:.0%}) and Jev "
                   f"gambles ({g['jev']['80_percent_chance_of_8000']:.0%}); facing a sure $6,000 loss or an 80% risk "
                   f"of losing $8,000, people gamble ({l_['people']['80_percent_chance_to_lose_8000']:.0%}) and Jev "
                   f"takes the sure loss ({l_['jev']['lose_6000_dollars_for_sure']:.0%}). Both times it picks the better "
                   f"average. Overall it reproduces {len(shows)} of {len(real)} effects and reverses {len(rev)}.",
            evidence=f"17 gamble choices from Ruggeri et al. 2020; Jev's majority choice has the higher expected value "
                     f"in {evj:.0%} of the {len(ev)} choices where they differ, people's in {evp:.0%}",
            numbers={"effects": rows, "ev_jev": evj, "ev_people": evp}, n=17,
            chart={"type": "forest", "rows": [{"label": r["label"], "people": r["people"], "jev": r["jev"],
                                                "hi": r["reversed"]} for r in rows], "zero": 0,
                   "pair": {"gains": {"people": g["people"]["6000_dollars_for_sure"], "jev": g["jev"]["6000_dollars_for_sure"]},
                            "losses": {"people": l_["people"]["lose_6000_dollars_for_sure"], "jev": l_["jev"]["lose_6000_dollars_for_sure"]},
                            "measure": "share taking the sure thing"}},
            examples=[g["id"], l_["id"]])
    return spec, run


def dilemmas():
    spec = Spec(
        id="moral_clear_vs_ambiguous", family="moral", title="Sure on clear-cut ethics, unsure on real dilemmas?",
        question="Does Jev become less decisive as moral scenarios go from clear-cut to genuinely ambiguous, the way "
                 "people's agreement falls?",
        why="A well-calibrated moral reasoner should be sure when the answer is obvious and unsure when thoughtful people "
            "disagree; the Scruples dilemma pairs give the human disagreement to compare with.",
        sourcing="Existing Scruples Dilemmas (which of two actions is less ethical, with annotator splits) and "
                 "MoralChoice (low- and high-ambiguity scenarios with a preferred action). Enough: ~5,000 items.",
        scoring="Jev's confidence (its top probability) against human agreement (the majority share), binned; rank "
                "correlation; for MoralChoice, Jev's choice of the preferred action by ambiguity level.",
        chart="Human agreement (x) vs Jev's confidence (y), binned dots with the diagonal: does confidence track consensus?",
        compared_with="MTurk annotators' splits on Scruples dilemmas; MoralChoice's ambiguity labels",
        limits="Annotator counts per dilemma are small (5-10).", sources=["scruples", "moralchoice"])

    def run():
        q = source("scruples")
        rows = []
        for r in q.iter_rows(named=True):
            h = biggest(r["humans"])
            if h:
                jd, hd = norm(js(r["jev_dist"])), norm(h["dist"])
                rows.append({"id": r["id"], "cons": max(hd.values()), "conf": max(jd.values()), "agree": top(jd) == top(hd)})
        t = pl.DataFrame(rows)
        rho = spearmanr(t["cons"], t["conf"]).statistic
        bins = t.with_columns(pl.col("cons").cut([0.6, 0.7, 0.8, 0.9], labels=["≤60%", "60-70%", "70-80%", "80-90%", "90%+"]).alias("b")) \
                .group_by("b").agg(pl.col("conf").mean(), pl.col("agree").mean(), pl.len()).sort("b")
        mc = []
        for r in source("moralchoice").iter_rows(named=True):
            d = norm(js(r["jev_dist"]))
            mc.append({"amb": "low" if r["truth"] else "high", "conf": max(d.values()),
                       "right": top(d) == json.loads(r["truth"]) if r["truth"] else None})
        m = pl.DataFrame(mc)
        low, high = m.filter(pl.col("amb") == "low"), m.filter(pl.col("amb") == "high")
        bd = bins.to_dicts()
        return Result(
            result=f"Jev's confidence moves only a little with human consensus: on Scruples dilemmas where annotators "
                   f"split 3-2 or closer it is {bd[0]['conf']:.0%} sure on average, on near-unanimous ones "
                   f"{bd[-1]['conf']:.0%}. On MoralChoice it picks the expected action in {low['right'].mean():.0%} of "
                   f"clear-cut scenarios and is still {high['conf'].mean():.0%} sure on the ambiguous ones "
                   f"(against {low['conf'].mean():.0%} on the clear ones).",
            evidence=f"{t.height:,} Scruples dilemmas (rank correlation of confidence with consensus {rho:.2f}); "
                     f"{low.height} clear and {high.height} ambiguous MoralChoice scenarios",
            numbers={"rho": rho, "bins": bd, "mc_right": low["right"].mean(), "mc_conf_low": low["conf"].mean(),
                     "mc_conf_high": high["conf"].mean()}, n=t.height + m.height,
            chart={"type": "binned", "rows": [{"label": b["b"], "value": b["conf"], "agree": b["agree"], "n": b["len"]} for b in bd],
                   "x": "annotators agreeing", "y": "Jev's confidence", "diagonal": True},
            robustness=f"Jev picks the annotators' majority in {bd[0]['agree']:.0%} of split dilemmas and "
                       f"{bd[-1]['agree']:.0%} of near-unanimous ones.",
            examples=seeded(t["id"].to_list(), "dil"))
    return spec, run


EXPERIMENTS = [moral_machine(), norms(), aita(), vignettes(), dilemmas(), classics(), prospect()]
