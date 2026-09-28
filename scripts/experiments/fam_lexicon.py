"""Lexicon experiments on new questions (research pass 2, ideas 2, 3, 7; docs/15 E43): emoji sentiment, the first
category member that comes to mind, typicality, idioms (familiarity, literal plausibility, completion) and
two-word metaphors (aptness, familiarity)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, jsd, level, norm, seeded, top, with_meta


def robust(r: dict) -> dict:
    """Jev's Choice distribution averaged over the base probe and the shuffled-order probes (same keys)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def score(r: dict) -> float | None:
    """Jev's expected level on a Score question, averaged with the reversed-levels probe (stored in original order)."""
    base = level(js(r["jev_dist"]))
    rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "reversed_levels" and v.get("dist")), None)
    if base is None:
        return None
    return (base + rev) / 2 if rev is not None else base


def rho_ci(a: np.ndarray, b: np.ndarray) -> list[float]:
    idx = np.arange(len(a))
    return boot(idx, stat=lambda ii: spearmanr(a[ii.astype(int)], b[ii.astype(int)]).statistic, b=300)


# ---- 1. emoji -------------------------------------------------------------------------------------------------------
def emoji():
    spec = Spec(
        id="lexicon_emoji_sentiment", family="lexicon", title="What an emoji says about a tweet, to Jev and to annotators",
        question="Told only that a tweet contains a given emoji, how positive does Jev think the tweet is, compared "
                 "with how annotators actually labeled the tweets that contain it?",
        why="Emoji carry a lot of the tone of online text, and some are used against their face value (😂 in "
            "complaints, 🙏 in pleas). A model that reads emoji by their picture will misjudge the tone of real posts.",
        sourcing="New questions (sources/emoji_sentiment): 'A tweet contains the emoji X. Knowing only that, is the "
                 "tweet more likely negative, neutral or positive?' for the 300 emojis found in 50+ labeled tweets of "
                 "the Emoji Sentiment Ranking (Kralj Novak et al. 2015, 1.6 million tweets labeled by 83 annotators, "
                 "CC BY-SA 4.0).",
        collection="300 new questions, each asked as written, for 'most people', and with the options in shuffled orders "
                   "(averaged).",
        scoring="Sentiment score = share positive minus share negative, for Jev's distribution and for the tweets' "
                "labels; rank correlation over emojis with a 90% bootstrap interval; how often Jev's most likely label "
                "is the tweets' most common one; the share Jev puts on neutral vs the tweets; the emojis read most "
                "differently.",
        chart="A scatter: the tweets' sentiment score (x) vs Jev's (y), one dot per emoji, the largest gaps labeled.",
        compared_with="Tweets labeled by 83 annotators in 13 European languages (Kralj Novak et al. 2015)",
        limits="The annotators labeled whole tweets, not the emoji; Jev sees only the emoji. Tweets are from 2013-2015 "
               "and in 13 languages.", new_questions=300, sources=["emoji_sentiment"])

    def run():
        rows = []
        for r in with_meta("emoji_sentiment"):
            h = norm(biggest(r["humans"])["dist"])
            j = robust(r)
            rows.append({"id": r["id"], "emoji": r["m"]["emoji"], "name": r["m"]["name"],
                         "jev": j.get("positive", 0) - j.get("negative", 0), "people": h.get("positive", 0) - h.get("negative", 0),
                         "jev_neutral": j.get("neutral", 0), "ppl_neutral": h.get("neutral", 0),
                         "same_top": top(j) == top(h), "sim": 1 - jsd(j, h)})
        t = pl.DataFrame(rows).sort("emoji")
        rho = spearmanr(t["jev"], t["people"]).statistic
        ci = rho_ci(t["jev"].to_numpy(), t["people"].to_numpy())
        t = t.with_columns((pl.col("jev") - pl.col("people")).alias("gap"))
        up, down = t.sort("gap", descending=True).head(4).to_dicts(), t.sort("gap").head(4).to_dicts()
        f = lambda r: f"{r['emoji']} ({r['jev']:+.2f} vs {r['people']:+.2f})"  # noqa: E731
        return Result(
            result=f"Jev ranks the tone of emoji {agree_word(rho)} like the tweets that carry them "
                   f"(rank correlation {rho:.2f}) and names the tweets' most common label for {t['same_top'].mean():.0%} of "
                   f"{t.height} emojis, but it reads {and_list([f(r) for r in down[:3]])} as negative where the tweets using "
                   f"them leaned positive, and {and_list([f(r) for r in up[:3]])} "
                   "far more positive than the tweets were (positive minus negative, Jev vs tweets).",
            evidence=f"{t.height} emojis (the screen hid {300 - t.height}); 90% interval on the rank correlation {ci[0]:.2f} "
                     f"to {ci[1]:.2f}; Jev puts {t['jev_neutral'].mean():.0%} on neutral, the tweets were {t['ppl_neutral'].mean():.0%} neutral",
            numbers={"rho": rho, "ci90": ci, "same_top": float(t["same_top"].mean()), "up": up, "down": down,
                     "neutral_jev": float(t["jev_neutral"].mean()), "neutral_people": float(t["ppl_neutral"].mean())},
            n=t.height,
            chart={"type": "scatter", "points": t.select("people", "jev").to_numpy().round(3).tolist(), "domain": [-1, 1],
                   "labels": [{"label": r["emoji"], "x": r["people"], "y": r["jev"]} for r in up[:4] + down[:4]],
                   "x": "tweets: positive minus negative", "y": "Jev: positive minus negative", "diagonal": True},
            examples=[up[0]["id"], down[0]["id"]])
    return spec, run


# ---- 2. first to mind -------------------------------------------------------------------------------------------------
def first():
    spec = Spec(
        id="lexicon_first_to_mind", family="lexicon", title="Name a bird: what comes to Jev's mind first",
        question="Asked to name a member of a category (a bird, a fruit, an emotion, a crime), does the first one that "
                 "comes to Jev's mind match the one people name first?",
        why="The first member people name is the category's center for them: robin more than penguin. Whether a model "
            "has the same centers says whether its 'typical' matches a person's, which shapes every example it writes.",
        sourcing="New questions (sources/category_norms): 'Asked to name a bird, which one comes to mind first?' for 113 "
                 "concrete and abstract categories from Banks, Wingfield & Connell 2023 (CC BY 4.0), a Choice over the "
                 "members people named first plus 'something else'. 20 Lancaster University students per category.",
        collection="113 new questions, each asked as written, for 'most people', and with the options shuffled (averaged).",
        scoring="How often Jev's top pick is the member people named first most often; Jev's probability on that member; "
                "how much weight it puts on 'something else' vs people; concrete vs abstract categories; the categories "
                "where it disagrees.",
        chart="Bars: agreement with people's most common first answer, concrete vs abstract, with 90% intervals; the "
              "misses listed.",
        compared_with="20 students per category (Banks, Wingfield & Connell 2023)",
        limits="Twenty people per category is few, and they are UK students; ties for the most common first answer "
               "are common. Jev picks from a list of what people named, which is easier than naming freely.",
        new_questions=113, sources=["category_norms"])

    def run():
        rows = []
        for r in with_meta("category_norms"):
            if r["m"].get("set") != "first":
                continue
            h = norm(biggest(r["humans"])["dist"])
            j = robust(r)
            named = {k: v for k, v in h.items() if k != "something_else"}
            best = max(named.values())
            tops = [k for k, v in named.items() if v == best]
            opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
            rows.append({"id": r["id"], "category": r["m"]["category"], "domain": r["m"]["domain"],
                         "agree": top(j) in tops, "p_top": sum(j.get(k, 0) for k in tops), "tie": len(tops) > 1,
                         "jev_else": j.get("something_else", 0), "ppl_else": h.get("something_else", 0),
                         "jev_pick": opts.get(top(j), top(j)), "people_pick": opts.get(sorted(tops)[0], sorted(tops)[0])})
        t = pl.DataFrame(rows).sort("category")
        by = t.group_by("domain").agg(pl.col("agree").mean(), pl.len()).sort("domain").to_dicts()
        miss = t.filter(~pl.col("agree") & ~pl.col("tie")).sort("category").to_dicts()
        ex = seeded([m["id"] for m in miss], "first", 3)
        exr = [m for m in miss if m["id"] in ex]
        return Result(
            result=f"Jev's first pick is the one people named first most often in {t['agree'].mean():.0%} of {t.height} "
                   f"categories ({and_list([f'{b['agree']:.0%} of {b['len']} {b['domain']} ones' for b in by])}). Where it "
                   "differs it names another usual member: " + and_list(
                       [f"{m['jev_pick']} for {m['category']} (people: {m['people_pick']})" for m in exr]) + ".",
            evidence=f"{t.height} categories (the screen hid {113 - t.height}), only 20 people each; ties for the top answer count as a match for either; 90% "
                     f"interval {boot(t['agree'].cast(float).to_numpy())}",
            numbers={"agree": float(t["agree"].mean()), "by_domain": by, "misses": miss,
                     "else_jev": float(t["jev_else"].mean()), "else_people": float(t["ppl_else"].mean())}, n=t.height,
            robustness=f"Jev puts {t['jev_else'].mean():.0%} on 'something else' on average, people "
                       f"{t['ppl_else'].mean():.0%}; {int(t['tie'].sum())} categories have a tie at the top.",
            chart={"type": "bars", "rows": [{"label": f"{b['domain']} categories", "value": b["agree"]} for b in by],
                   "domain": [0, 1]},
            examples=ex)
    return spec, run


# ---- 3. typicality -----------------------------------------------------------------------------------------------------
def typicality():
    spec = Spec(
        id="lexicon_typicality", family="lexicon", title="Is a penguin a good example of a bird?",
        question="How good an example of its category does Jev find each member (a penguin of a bird, a tuba of a wind "
                 "instrument, boredom of an emotion), compared with people's ratings?",
        why="Typicality is how people's categories are shaped: some members are central, some marginal. A model that "
            "treats every member as equally good, or ranks them differently, reasons about categories differently.",
        sourcing="New questions (sources/category_norms): 'How good an example of a bird is a penguin?' on five "
                 "described levels (very poor to very good example, the study's endpoints) for 350 members sampled "
                 "evenly over the range of UK adults' mean ratings (Banks, Wingfield & Connell 2023; at least 12 raters "
                 "per item, means only).",
        collection="350 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Rank correlation between Jev's expected level and people's mean, with a 90% bootstrap interval, overall "
                "and for concrete vs abstract categories; the members it rates much higher or lower than people.",
        chart="A scatter: people's mean rating (x, 1-5) vs Jev's level (y, 0-4), with the largest disagreements labeled.",
        compared_with="UK adults on Prolific (Banks, Wingfield & Connell 2023)",
        limits="Only means are published, so ranks are compared, not distributions. The level descriptions are this "
               "project's, anchored on the study's endpoints.", new_questions=350, sources=["category_norms"])

    def run():
        rows = []
        for r in with_meta("category_norms"):
            if r["m"].get("set") != "typicality":
                continue
            s = score(r)
            if s is not None:
                rows.append({"id": r["id"], "member": r["m"]["member"], "category": r["m"]["category"],
                             "domain": r["m"]["domain"], "jev": s, "people": r["m"]["human_mean"]})
        t = pl.DataFrame(rows).sort("category", "member")
        rho = spearmanr(t["jev"], t["people"]).statistic
        ci = rho_ci(t["jev"].to_numpy(), t["people"].to_numpy())
        by = [{"domain": d, "rho": float(spearmanr(g["jev"], g["people"]).statistic), "n": g.height}
              for (d,), g in t.group_by("domain", maintain_order=True)]
        t = t.with_columns((pl.col("jev").rank() / t.height - pl.col("people").rank() / t.height).alias("d"))
        hi, lo = t.sort("d", descending=True).head(4).to_dicts(), t.sort("d").head(4).to_dicts()
        f = lambda r: f"{r['member']} as {'an' if r['category'][0] in 'aeiou' else 'a'} {r['category']}"  # noqa: E731
        return Result(
            result=f"Jev ranks how good an example each member is {agree_word(rho)} like people (rank correlation "
                   f"{rho:.2f} over {t.height} members; " + ", ".join(f"{b['domain']} categories {b['rho']:.2f}" for b in by)
                   + f"). It rates {and_list([f(r) for r in hi[:3]])} much higher than people do, and "
                   f"{and_list([f(r) for r in lo[:3]])} much lower.",
            evidence=f"{t.height} members against people's published means (no distributions); 90% interval {ci[0]:.2f} to {ci[1]:.2f}",
            numbers={"rho": rho, "ci90": ci, "by_domain": by, "higher": hi, "lower": lo}, n=t.height,
            chart={"type": "scatter", "points": t.select("people", "jev").to_numpy().round(3).tolist(),
                   "labels": [{"label": r["member"], "x": r["people"], "y": r["jev"]} for r in hi[:4] + lo[:4]],
                   "x": "people's mean (1-5)", "y": "Jev's level (0-4)"},
            examples=[hi[0]["id"], lo[0]["id"]])
    return spec, run


# ---- 4. idioms ---------------------------------------------------------------------------------------------------------
def _idioms() -> dict[str, dict]:
    by: dict[str, dict] = {}
    for r in with_meta("idiom_norms"):
        by.setdefault(r["m"]["idiom"], {})[r["m"]["set"]] = r
    return by


def idiom_completion():
    spec = Spec(
        id="lexicon_idiom_completion", family="lexicon", title="Finish the idiom: Jev knows the ending people forget",
        question="Given an idiom without its last word ('Be a bad apple in the ___'), does Jev give the idiom's own "
                 "word, and does it follow people when they mostly give a different one?",
        why="People's completions show which idioms are alive: many people finish 'a bad apple in the...' with 'bunch'. "
            "A model trained on text may know the dictionary form better than people, or follow the drift.",
        sourcing="New questions (sources/idiom_norms): 'Finish this idiom with one word: \"Be a bad apple in the ___\"' "
                 "for 200 idioms from Bulkes & Tanner 2017 (870 American English idioms, about 100 US adults each), a "
                 "Choice over the idiom's word, up to five other completions people gave at least twice, and "
                 "'another word'; people's completions are the human distribution.",
        collection="Up to 200 new questions, each asked as written, for 'most people', and with the options shuffled "
                   "(averaged).",
        scoring="Share where Jev's top pick is the idiom's word, vs the share of people who gave it; on idioms where "
                "people's most common answer was a different word, which of the two Jev picks; agreement with people "
                "by how familiar the idiom is (terciles of the study's familiarity ratings).",
        chart="Bars by familiarity tercile: share of people giving the idiom's word vs Jev picking it.",
        compared_with="US adults (Bulkes & Tanner 2017)",
        limits="Jev picks from the completions people gave rather than writing its own word, which makes the idiom's "
               "word easier to find.", new_questions=200, sources=["idiom_norms"])

    def run():
        rows = []
        for idiom, sets in sorted(_idioms().items()):
            r = sets.get("completion")
            if r is None:
                continue
            h = norm(biggest(r["humans"])["dist"])
            j = robust(r)
            want = r["truth"].strip('"') if isinstance(r["truth"], str) else r["truth"]
            crowd = max((k for k in h if k != "another_word"), key=lambda k: h[k])
            opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
            rows.append({"id": r["id"], "idiom": idiom, "jev_right": top(j) == want, "ppl_share": h.get(want, 0),
                         "crowd_differs": crowd != want, "jev_crowd": top(j) == crowd, "crowd_word": opts.get(crowd, crowd),
                         "fam": r["m"]["familiarity"]})
        t = pl.DataFrame(rows).sort("idiom")
        t = t.with_columns(pl.col("fam").qcut(3, labels=["least familiar", "middle", "most familiar"]).alias("tier"))
        by = t.group_by("tier", maintain_order=False).agg(pl.col("jev_right").mean(), pl.col("ppl_share").mean(), pl.len()) \
              .sort("tier").to_dicts()
        drift = t.filter(pl.col("crowd_differs"))
        ex = drift.sort("ppl_share").head(3).to_dicts()
        return Result(
            result=f"Jev gives the idiom's own last word for {t['jev_right'].mean():.0%} of {t.height} idioms, where "
                   f"{t['ppl_share'].mean():.0%} of people did on average ({by[0]['jev_right']:.0%} vs "
                   f"{by[0]['ppl_share']:.0%} on the least familiar third). On the {drift.height} idioms where most people "
                   f"gave another word, Jev sides with the idiom {drift['jev_right'].mean():.0%} of the time and with the "
                   f"crowd {drift['jev_crowd'].mean():.0%}"
                   + (" (for example \"" + ex[0]["idiom"] + f"\", which most people ended with \"{ex[0]['crowd_word']}\")" if ex else "")
                   + ". Jev leans to the dictionary form more than people do.",
            evidence=f"{t.height} idioms with a completion question shown, about 100 people each; 90% interval on Jev's share {boot(t['jev_right'].cast(float).to_numpy())}",
            numbers={"jev": float(t["jev_right"].mean()), "people": float(t["ppl_share"].mean()), "by_familiarity": by,
                     "drift_n": drift.height, "drift_jev_idiom": float(drift["jev_right"].mean()) if drift.height else None},
            n=t.height,
            chart={"type": "bars2", "labels": [b["tier"] for b in by], "a": [b["ppl_share"] for b in by],
                   "b": [b["jev_right"] for b in by], "a_label": "people giving the idiom's word",
                   "b_label": "Jev picking it"},
            examples=[e["id"] for e in ex[:2]])
    return spec, run


def idiom_ratings():
    spec = Spec(
        id="lexicon_idiom_ratings", family="lexicon", title="Which idioms Jev finds familiar, and which it reads literally",
        question="Does Jev know which idioms are familiar to Americans and which could make sense taken word for word, "
                 "the way people rated them?",
        why="Familiarity and literal plausibility are what people use to read an idiom ('kick the bucket' could "
            "happen; 'rain cats and dogs' couldn't). A model that misjudges them will misread figurative language.",
        sourcing="New questions (sources/idiom_norms): 'How familiar is the idiom \"X\"?' and 'Taken literally, word "
                 "for word, how plausible is \"X\"?' on five described levels for 200 idioms from Bulkes & Tanner 2017 "
                 "(about 100 US adults per idiom and dimension, means on 1-5).",
        collection="About 400 new questions, each asked as written, for 'most people', and with the levels reversed "
                   "(averaged).",
        scoring="Per dimension, rank correlation between Jev's expected level and people's mean with a 90% bootstrap "
                "interval; the idioms whose rank differs most.",
        chart="Two scatters side by side: people's mean (x) vs Jev's level (y), familiarity and literal plausibility.",
        compared_with="US adults (Bulkes & Tanner 2017)",
        limits="Only means are published, so ranks are compared. Jev is asked how familiar the idiom is, not how often it "
               "has met it.", new_questions=392, sources=["idiom_norms"])

    def run():
        out, rows = {}, []
        for set_ in ("familiarity", "literal"):
            pts = []
            for idiom, sets in sorted(_idioms().items()):
                r = sets.get(set_)
                s = score(r) if r is not None else None
                if s is not None:
                    pts.append({"id": r["id"], "idiom": idiom, "jev": s, "people": r["m"]["human_mean"]})
            t = pl.DataFrame(pts)
            rho = spearmanr(t["jev"], t["people"]).statistic
            t = t.with_columns((pl.col("jev").rank() / t.height - pl.col("people").rank() / t.height).alias("d"))
            out[set_] = {"rho": float(rho), "ci90": rho_ci(t["jev"].to_numpy(), t["people"].to_numpy()), "n": t.height,
                         "higher": t.sort("d", descending=True).head(3).to_dicts(), "lower": t.sort("d").head(3).to_dicts(),
                         "points": t.select("people", "jev").to_numpy().round(3).tolist()}
            rows.append({"label": "familiarity" if set_ == "familiarity" else "literal plausibility", "value": float(rho),
                         "ci": out[set_]["ci90"]})
        fa, li = out["familiarity"], out["literal"]
        return Result(
            result=f"Jev knows which idioms Americans find familiar {agree_word(fa['rho'])} (rank correlation "
                   f"{fa['rho']:.2f}) and which make sense taken literally {agree_word(li['rho'])} ({li['rho']:.2f}). It "
                   f"rates \"{fa['higher'][0]['idiom']}\" far more familiar than people do and \"{fa['lower'][0]['idiom']}\" "
                   f"far less; it finds \"{li['higher'][0]['idiom']}\" far more literally plausible than they do.",
            evidence=f"{fa['n']} and {li['n']} idioms against people's published means (no distributions); 90% intervals {fa['ci90'][0]:.2f} to {fa['ci90'][1]:.2f} and "
                     f"{li['ci90'][0]:.2f} to {li['ci90'][1]:.2f}",
            numbers={k: {kk: vv for kk, vv in v.items() if kk != "points"} for k, v in out.items()}, n=fa["n"] + li["n"],
            chart={"type": "dots", "rows": rows, "domain": [0, 1]},
            examples=[fa["higher"][0]["id"], li["higher"][0]["id"]])
    return spec, run


# ---- 5. metaphors ------------------------------------------------------------------------------------------------------
def metaphors():
    spec = Spec(
        id="lexicon_metaphors", family="lexicon", title="Dark thoughts, silky sunsets: how apt Jev finds a metaphor",
        question="Rating two-word expressions for how apt and how familiar they are ('dark thoughts', 'acid test', "
                 "'fan brush'), does Jev agree with people, and does it treat metaphors and literal expressions alike?",
        why="Aptness is what makes a metaphor land. A model that finds every metaphor apt, or rates metaphors below "
            "plain descriptions, will write and read figurative language differently from people.",
        sourcing="New questions (sources/metaphor_norms): 'How apt is the expression \"X\": how well does the "
                 "describing word capture important features of what it describes?' and 'How familiar is the "
                 "expression \"X\"?' on seven described levels, for 300 expressions (207 metaphors, 93 literal) from "
                 "the 2025 metaphor norms (OSF xk3j9); people's full rating distributions (about 25 raters each, "
                 "expression shown alone).",
        collection="600 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Per dimension, rank correlation with people's mean and a 90% bootstrap interval; Jev's mean level minus "
                "people's for metaphors and for literal expressions (on the same 0-6 scale); distribution similarity.",
        chart="Paired dots per group (metaphors, literal) and dimension: people's mean and Jev's, 0-6.",
        compared_with="Crowd raters, expression shown in isolation (OSF xk3j9)",
        limits="The OSF project states no license (the article is CC BY 4.0). Level descriptions are this project's; "
               "the study's scale was 1-7 with defined endpoints.", new_questions=600, sources=["metaphor_norms"])

    def run():
        rows = []
        for r in with_meta("metaphor_norms"):
            s = score(r)
            h = biggest(r["humans"])
            if s is None or not h:
                continue
            rows.append({"id": r["id"], "phrase": r["m"]["phrase"], "set": r["m"]["set"], "literal": r["m"]["literal"],
                         "jev": s, "people": level(h["dist"]), "sim": 1 - jsd(norm(js(r["jev_dist"])), norm(h["dist"]))})
        t = pl.DataFrame(rows).sort("set", "phrase")
        res, dots = {}, []
        for set_ in ("aptness", "familiarity"):
            g = t.filter(pl.col("set") == set_)
            res[set_] = {"rho": float(spearmanr(g["jev"], g["people"]).statistic),
                         "ci90": rho_ci(g["jev"].to_numpy(), g["people"].to_numpy()), "n": g.height}
            for lit, lab in ((False, "metaphors"), (True, "literal")):
                gg = g.filter(pl.col("literal") == lit)
                res[set_][lab] = {"jev": float(gg["jev"].mean()), "people": float(gg["people"].mean()), "n": gg.height,
                                  "gap_ci": boot((gg["jev"] - gg["people"]).to_numpy())}
                dots.append({"label": f"{set_}, {lab}", "value": float(gg["jev"].mean()), "people": float(gg["people"].mean())})
        a = res["aptness"]
        ap = t.filter(pl.col("set") == "aptness").with_columns((pl.col("jev") - pl.col("people")).alias("gap"))
        lo = ap.filter(~pl.col("literal")).sort("gap").head(3).to_dicts()
        return Result(
            result=f"Jev orders the expressions by aptness {agree_word(a['rho'])} like people (rank correlation "
                   f"{a['rho']:.2f}) and by familiarity {agree_word(res['familiarity']['rho'])} "
                   f"({res['familiarity']['rho']:.2f}). On a 0-6 scale it rates metaphors {a['metaphors']['jev']:.1f} for "
                   f"aptness where people give {a['metaphors']['people']:.1f}, and literal expressions "
                   f"{a['literal']['jev']:.1f} where people give {a['literal']['people']:.1f}: it finds nearly everything "
                   f"apt, and, like people, barely separates metaphors from literal phrases. It rates "
                   f"{and_list([f'\"{r['phrase']}\"' for r in lo])} furthest below people.",
            evidence=f"{a['n']} expressions per dimension ({a['metaphors']['n']} metaphors, {a['literal']['n']} literal); "
                     f"90% intervals on the rank correlation {a['ci90'][0]:.2f} to {a['ci90'][1]:.2f} (aptness)",
            numbers=res, n=t.height,
            chart={"type": "dots", "rows": dots, "domain": [0, 6]},
            examples=[r["id"] for r in lo[:2]])
    return spec, run


EXPERIMENTS = [emoji(), first(), typicality(), idiom_completion(), idiom_ratings(), metaphors()]
