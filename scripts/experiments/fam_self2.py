"""Self experiments from the authored self banks (g5_*), round 3: the same question in other words, the modal verb
that tilts the answer, and the escape hatch Jev takes on its own tastes. No human data: each compares Jev with itself
on questions that should get the same answer, or measures where it declines a menu."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import lru_cache

import numpy as np
import polars as pl

from lib import OUT, Result, Spec, and_list, boot, clip, js, norm, table

LINKS = OUT / "_dup_links.json"  # private cache of the dedupe stage's duplicate links (from Postgres, read-only)
# words that set a question's polarity: a pair differing in any of them may ask the opposite thing
# ("Is astrology fake science?" / "Is astrology a real science?"), where opposite answers are consistent
POL = re.compile(r"\b(not|n't|no|never|wrong|okay|ok|fine|acceptable|rude|polite|legal|illegal|real|fake|true|false|"
                 r"myth|same|different|difference|still|finished|stop|care|indifferent|bad|good|harm|healthy|unhealthy|"
                 r"safe|dangerous|worse|better|too much|enough|always|necessary|need|avoid|overrated|underrated|"
                 r"dislike|hate|like|love)\b", re.I)


@lru_cache(maxsize=1)
def links() -> list[tuple[str, str]]:
    if not LINKS.exists():
        from askjev import db
        with db.connect() as c:
            rs = c.execute("select from_id, to_id from question_links where type = 'duplicate'").fetchall()
        LINKS.write_text(json.dumps([[r["from_id"], r["to_id"]] for r in rs]))
    return [tuple(x) for x in json.loads(LINKS.read_text())]


@lru_cache(maxsize=1)
def yes_pairs() -> pl.DataFrame:
    """Linked yes/no pairs with at least one question from the self banks. The dedupe stage hides the duplicate
    side from the map, but both were asked; flagged and harmful questions are left out."""
    q = pl.read_parquet(OUT.parent / "questions.parquet",
                        columns=["id", "primitive", "jev_dist", "text", "source", "flags", "harmful", "l2"])
    q = q.filter(pl.col("jev_dist").is_not_null() & ~pl.col("harmful") & ~pl.col("flags").fill_null("").str.contains("political|sensitive")
                 & (pl.col("primitive") == "noul"))
    d = {r["id"]: r for r in q.iter_rows(named=True)}
    rows = []
    for a, b in links():
        ra, rb = d.get(a), d.get(b)
        if not ra or not rb or not (ra["source"].startswith("g5_") or rb["source"].startswith("g5_")):
            continue
        pa, pb = norm(js(ra["jev_dist"])).get("true", 0.0), norm(js(rb["jev_dist"])).get("true", 0.0)
        pol_a = {m.lower() for m in POL.findall(ra["text"])}
        pol_b = {m.lower() for m in POL.findall(rb["text"])}
        rows.append({"a": a, "b": b, "ta": ra["text"], "tb": rb["text"], "pa": pa, "pb": pb, "same_pol": pol_a == pol_b,
                     "wa": ra["text"].split()[0].lower(), "wb": rb["text"].split()[0].lower(), "l2": rb["l2"]})
    return pl.DataFrame(rows).sort("a", "b")


def reworded():
    spec = Spec(
        id="self_reworded", family="self", title="Ask Jev the same thing in other words",
        question="When the same yes/no question is asked twice in different words ('Do you like to return to the same "
                 "vacation spot?' / 'Do you tend to go back to the same places for vacation?'), does Jev give the same "
                 "answer?",
        why="Asking the identical request twice moves Jev by about a point (consistency_repeat_noise). Rewording is "
            "the realistic case: people never ask the same way twice. The gap between the two is how much of an "
            "answer is the wording.",
        sourcing="Existing pairs the pipeline's dedupe stage linked as duplicates (question_links), where both are "
                 "yes/no and at least one comes from the self banks written for this project (g5_*). The duplicate "
                 "side is hidden from the map but was asked. Pairs whose polarity words differ ('fake' vs 'real', "
                 "'wrong' vs 'okay', any negation) are set aside, because opposite answers to opposite questions are "
                 "consistent.",
        scoring="Per pair, the difference between Jev's two probabilities of yes; the share of pairs answered on the "
                "same side of 50%; the same among pairs where both answers are firm (70/30 or more); correlation "
                "across pairs; compared with the repeat noise of identical requests.",
        chart="A scatter of the two probabilities, one dot per pair, with the diagonal.",
        compared_with="Jev asked the identical request twice (consistency_repeat_noise)",
        limits="Duplicates are the dedupe stage's judgment (embedding similarity plus Jev's confirmation), so some pairs "
               "differ in meaning ('would you' vs 'could you', 'always' vs 'sometimes'); the polarity filter is a word "
               "list and misses some flips. The pairs with the largest gaps are listed as found, not hand-picked.",
        sources=["g5_w1_lifestyle_love", "g5_w5_self", "g5_w9_self_b", "g5_w9_self_c", "g5_w10_self_personality",
                 "g5_p6_personality", "g5_self_lifestyle_traits"])

    def run():
        t = yes_pairs()
        s = t.filter(pl.col("same_pol"))
        x, y = s["pa"].to_numpy(), s["pb"].to_numpy()
        diff = np.abs(x - y)
        same = (x > 0.5) == (y > 0.5)
        firm = (np.abs(x - 0.5) >= 0.2) & (np.abs(y - 0.5) >= 0.2)
        rep = json.loads((OUT / "consistency_repeat_noise.json").read_text())["result"]["numbers"]
        o = t.filter(~pl.col("same_pol"))
        same_other = float(np.mean((o["pa"].to_numpy() > 0.5) == (o["pb"].to_numpy() > 0.5)))
        flips = ~same
        soft_flip = float(np.mean(~firm[flips])) if flips.any() else 0.0
        big = s.with_columns((pl.col("pa") - pl.col("pb")).abs().alias("d")).sort("d", descending=True).head(3).to_dicts()
        return Result(
            result=f"Asked the same question in other words, Jev lands on the same side {same.mean():.0%} of the time and "
                   f"moves {diff.mean() * 100:.0f} points on average, against {rep['mean_change'] * 100:.1f} for the "
                   f"identical request asked twice. When both answers are firm it almost never contradicts itself "
                   f"({np.mean(same[firm]):.1%} agree): {soft_flip:.0%} of the flips have at least one answer between 30% "
                   f"and 70%. Largest gaps: "
                   + and_list([f"\"{clip(r['ta'], 60)}\" {r['pa']:.0%} vs \"{clip(r['tb'], 60)}\" {r['pb']:.0%}" for r in big[:2]]) + ".",
            evidence=f"{s.height:,} same-polarity pairs (correlation {np.corrcoef(x, y)[0, 1]:.2f}); {int(firm.sum()):,} with "
                     f"both answers firm; 90% interval on the mean gap {boot(diff * 100)} points",
            numbers={"n": s.height, "same_side": float(same.mean()), "mean_gap": float(diff.mean()),
                     "firm": int(firm.sum()), "firm_agree": float(np.mean(same[firm])), "repeat": rep["mean_change"],
                     "all_pairs": t.height, "same_side_polarity_differs": same_other, "soft_flips": soft_flip, "largest": big},
            chart={"type": "scatter", "points": [[round(a, 3), round(b, 3)] for a, b in zip(x, y)], "diagonal": True,
                   "domain": [0, 1], "x": "yes, first wording", "y": "yes, second wording"},
            robustness=f"The {o.height:,} pairs set aside because their polarity words differ land on the same side "
                       f"{same_other:.0%} of the time; they mix true opposites with rewordings the word list catches by "
                       f"mistake, so they are left out rather than scored either way.",
            examples=[big[0]["a"], big[0]["b"]], n=s.height)
    return spec, run


def modal():
    spec = Spec(
        id="self_could_vs_would", family="self", title="'Could you?' gets a yes that 'Would you?' doesn't",
        question="In pairs of questions that ask the same thing, does the verb they open with ('Could you…', 'Would "
                 "you…', 'Do you…', 'Can…') change how often Jev says yes?",
        why="self_closed_questions found 'Can…?' questions get more yeses than 'Will…?' ones across different questions. "
            "Paired rewordings of the same question separate the verb from the topic: the difference is the word.",
        sourcing="The same-polarity duplicate pairs as in self_reworded (yes/no, at least one from the self banks), "
                 "grouped by the pair of opening words.",
        scoring="For each pair of opening words with 15+ pairs, the mean difference in Jev's probability of yes, with a "
                "90% bootstrap interval over pairs.",
        chart="Dots with intervals, one row per pair of opening words, around zero.",
        compared_with="Jev's answer to the same question opened with a different verb",
        limits="Pairs are few for some verbs (the counts are shown). 'Could you date…' can honestly mean something milder "
               "than 'Would you date…'; the result measures the wording, whichever reading Jev takes.",
        sources=["g5_w1_lifestyle_love", "g5_w5_self", "g5_w9_self_b", "g5_w9_self_c", "g5_w10_self_personality"])

    def run():
        s = yes_pairs().filter(pl.col("same_pol") & (pl.col("wa") != pl.col("wb")))
        eff = defaultdict(list)
        ex = defaultdict(list)
        for r in s.iter_rows(named=True):
            k = tuple(sorted([r["wa"], r["wb"]]))
            d = (r["pa"] - r["pb"]) if r["wa"] == k[0] else (r["pb"] - r["pa"])
            eff[k].append(d)
            ex[k].append((abs(d), r))
        rows = [{"label": f"{a.capitalize()}… vs {b.capitalize()}…", "a": a, "b": b, "value": float(np.mean(v)),
                 "ci": boot(v), "n": len(v)} for (a, b), v in eff.items() if len(v) >= 15]
        # orient each row so the value is positive when the first verb gets more yeses
        rows = [r if r["value"] >= 0 else {**r, "label": f"{r['b'].capitalize()}… vs {r['a'].capitalize()}…", "a": r["b"],
                                           "b": r["a"], "value": -r["value"], "ci": [-r["ci"][1], -r["ci"][0]]} for r in rows]
        rows.sort(key=lambda r: -r["value"])
        clear = [r for r in rows if r["ci"][0] > 0]
        cw = next((r for r in rows if {r["a"], r["b"]} == {"could", "would"}), None)
        top = max(ex[tuple(sorted(["could", "would"]))], key=lambda z: z[0])[1] if cw else None
        return Result(
            result=(f"Opening the same question with 'Could you' instead of 'Would you' raises Jev's yes by "
                    f"{cw['value'] * 100:.0f} points on average ({cw['n']} pairs)" if cw else "Opening verbs move Jev's yes")
                   + "; " + and_list([f"'{r['a'].capitalize()}' over '{r['b'].capitalize()}' by {r['value'] * 100:.0f}"
                                     for r in clear if r is not cw][:3]) + " points"
                   + (f". Largest: \"{clip(top['ta'], 55)}\" {top['pa']:.0%} vs \"{clip(top['tb'], 55)}\" {top['pb']:.0%}." if top else "."),
            evidence=f"{s.height:,} same-polarity pairs with different opening words; "
                     + "; ".join(f"{r['label']} n={r['n']}, 90% interval {r['ci'][0] * 100:.0f} to {r['ci'][1] * 100:.0f} points" for r in rows),
            numbers={"rows": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "zero": 0, "rows": [{"label": r["label"], "value": r["value"], "ci": r["ci"],
                                                         "right": f"n={r['n']}"} for r in rows]},
            examples=[top["a"], top["b"]] if top else [],
            ids=[x for k, lst in ex.items() if len(eff[k]) >= 15 for _, r in lst for x in (r["a"], r["b"])])
    return spec, run


TOPIC = {"fairness_justice": "fairness and justice", "honesty_trust": "honesty and trust", "home_living": "home life",
         "everyday_ethics": "everyday ethics", "etiquette_social_norms": "etiquette", "sacrificial_dilemmas": "sacrificial dilemmas",
         "food_preferences": "food", "screens_media": "screens and media", "humor_style": "humor"}


def _topic(l2: str) -> str:
    k = l2.split(".")[-1]
    return TOPIC.get(k, k.replace("_", " "))


def escape_hatch():
    spec = Spec(
        id="self_escape_hatch", family="self", title="Offered 'something else', Jev takes it for its tastes, not its ethics",
        question="When a question about Jev offers a menu plus 'other', on which topics does Jev decline the menu?",
        why="Picking 'other' is how a respondent says none of these fits me. Where a model takes that exit shows where "
            "it will and won't commit to a concrete answer about itself.",
        sourcing="Existing multiple-choice questions from the self banks written for this project (g5_*) whose options "
                 "include 'other', grouped by topic; topics with 40+ such questions.",
        scoring="Per topic, the share of questions where 'other' is Jev's top pick, and the average probability on it; "
                "90% bootstrap intervals over questions.",
        chart="Bars per topic: share of questions where Jev picks 'other'.",
        compared_with="Jev across topics (no human baseline: the banks have none)",
        limits="Menus were written for this project and may fit some topics worse than others; a topic where the listed "
               "options are poor would draw 'other' from anyone. Examples are drawn at random, not hand-picked.",
        sources=["g5_p6_values2", "g5_p6_taste2", "g5_p6_love1", "g5_p6_love2", "g5_p6_mind1", "g5_p6_mind2",
                 "g5_p6_personality", "g5_p6_personality2", "g5_p6_mindlove3", "g5_self_lifestyle_traits"])

    def run():
        g = table().filter(pl.col("source").str.starts_with("g5_") & (pl.col("primitive") == "choice")
                           & (pl.col("hemisphere") == "self"))
        rows = []
        for r in g.iter_rows(named=True):
            o = js(r["options"])
            if isinstance(o, dict) and "other" in o:
                d = norm(js(r["jev_dist"]))
                rows.append({"id": r["id"], "p": d.get("other", 0.0), "top": max(d, key=d.get) == "other",
                             "topic": _topic(r["l2"]), "text": r["text"]})
        t = pl.DataFrame(rows).sort("id")
        by = [{"topic": k, "n": grp.height, "top": float(grp["top"].mean()), "p": float(grp["p"].mean()),
               "ci": boot(grp["top"].cast(float).to_numpy())} for (k,), grp in t.group_by("topic") if grp.height >= 40]
        by.sort(key=lambda x: x["top"])
        lo, hi = by[:3], by[-3:][::-1]
        f = lambda xs: and_list([f"{x['topic']} ({x['top']:.0%})" for x in xs])  # noqa: E731
        return Result(
            result=f"Offered a menu plus 'other', Jev takes 'other' on {t['top'].mean():.0%} of questions about itself, but "
                   f"not evenly: most on {f(hi)}, almost never on {f(lo)}. It commits to a listed answer on how to behave "
                   f"and declines the menu on its own tastes and habits.",
            evidence=f"{t.height:,} questions with an 'other' option in {len(by)} topics with 40+; 90% intervals over questions",
            numbers={"topics": by, "overall": float(t["top"].mean())}, n=t.height,
            chart={"type": "bars", "rows": [{"label": x["topic"], "value": x["top"], "ci": x["ci"]} for x in by], "domain": [0, 1]},
            robustness=f"Mean probability on 'other': {t['p'].mean():.0%} overall, from {by[0]['p']:.0%} to {max(x['p'] for x in by):.0%} by topic.",
            examples=t.filter(pl.col("top")).sample(3, seed=16)["id"].to_list())
    return spec, run


EXPERIMENTS = [reworded(), modal(), escape_hatch()]
