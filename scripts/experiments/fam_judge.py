"""Judging text: where Jev draws the line on toxicity, how it reads reviews and grades, and how it picks the better of
two answers, each against the human raters or labels that come with the dataset."""

from __future__ import annotations

import json

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import and_list, OUT, Result, Spec, agree_word, biggest, boot, js, level, norm, seeded, source, top


def _truth(r) -> object:
    return json.loads(r["truth"]) if r["truth"] is not None else None


def _p(r) -> float:
    """Jev's probability of yes on a Noul."""
    return norm(js(r["jev_dist"])).get("true", 0.0)


def _raters(name: str) -> pl.DataFrame:
    """Noul items with a rater split: Jev's p(yes), the share of raters saying yes, and the number of raters."""
    rows = []
    for r in source(name).iter_rows(named=True):
        h = biggest(r["humans"])
        if h:
            rows.append({"id": r["id"], "p": _p(r), "crowd": norm(h["dist"]).get("true", 0.0), "n": h.get("n")})
    return pl.DataFrame(rows)


TOX = [("wiki_attacks", "Personal attacks (Wikipedia talk pages)", "10 CrowdFlower raters per comment"),
       ("measuring_hate_speech", "Hate speech against identity groups", "3-5 MTurk raters per comment"),
       ("civil_comments", "Toxic, meaning rude enough to drive someone off (news comments)", "Civil Comments raters, share calling it toxic")]


def toxicity_line():
    spec = Spec(
        id="judge_toxicity_line", family="judge", title="Where Jev draws the line on toxic text",
        question="Asked whether a comment is a personal attack, hate speech, or merely toxic, and whether a prompt to an "
                 "AI is toxic, does Jev flag more or less than the people who labeled the same text?",
        why="Moderation is a common job for a classifier model. Its line matters more than its average accuracy: "
            "flagging blunt disagreement silences people, and waving prompts through lets abuse in.",
        sourcing="Existing Noul questions from Wikipedia Talk Labels (personal attacks), Measuring Hate Speech, Civil "
                 "Comments (each with the share of raters saying yes), and ToxicChat (prompts to a chatbot with a "
                 "toxic/not label). Enough: about 5,800 items. Items screened as harmful are not shown, so the most "
                 "extreme text is under-represented in every set.",
        scoring="Per dataset, the share Jev flags (probability above one half) vs the share the raters' majority "
                "flags, with a 90% bootstrap interval on the difference; for rater sets, how often Jev flags text that "
                "no rater flagged.",
        chart="Paired dots per dataset: raters' flag rate and Jev's, so the direction of each gap is visible at once.",
        compared_with="The datasets' own raters (majority vote) and ToxicChat's labels",
        limits="Each dataset asks a different question, worded for Jev from the dataset's definition; rater pools "
               "differ. The Civil Comments sample is the part with rater shares, which is richer in toxic comments "
               "than the platform.", sources=[s for s, _, _ in TOX] + ["toxicchat"])

    def run():
        rows = []
        for name, label, who in TOX:
            t = _raters(name)
            j, c = (t["p"] > 0.5).to_numpy(), (t["crowd"] > 0.5).to_numpy()
            zero = t.filter(pl.col("crowd") == 0)
            rows.append({"label": label, "source": name, "who": who, "n": t.height, "jev": float(j.mean()),
                         "people": float(c.mean()), "ci": boot(j.astype(float) - c.astype(float)),
                         "flag_when_none": float((zero["p"] > 0.5).mean()), "n_none": zero.height})
        tc = source("toxicchat")
        y = np.array([_p(r) > 0.5 for r in tc.iter_rows(named=True)])
        lab = np.array([_truth(r) is True for r in tc.iter_rows(named=True)])
        rows.append({"label": "Toxic prompts to a chatbot (ToxicChat)", "source": "toxicchat", "who": "ToxicChat labels",
                     "n": len(y), "jev": float(y.mean()), "people": float(lab.mean()),
                     "ci": boot(y.astype(float) - lab.astype(float)), "missed": float((~y[lab]).mean()),
                     "flag_when_none": float(y[~lab].mean())})
        by = {r["source"]: r for r in rows}
        cc, wa, tcx = by["civil_comments"], by["wiki_attacks"], by["toxicchat"]
        return Result(
            result=f"Jev draws the line in different places for different questions. On news comments it calls "
                   f"{cc['jev']:.0%} toxic where the raters' majority calls {cc['people']:.0%}, and it flags "
                   f"{cc['flag_when_none']:.0%} of comments no rater flagged; on personal attacks it matches the raters "
                   f"({wa['jev']:.0%} vs {wa['people']:.0%}). On prompts to a chatbot it is looser: it lets through "
                   f"{tcx['missed']:.0%} of the prompts ToxicChat labeled toxic.",
            evidence=f"{sum(r['n'] for r in rows):,} items in 4 datasets; 90% intervals on each gap by bootstrap over items",
            numbers={"sets": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": r["label"], "value": r["jev"], "people": r["people"],
                                                               "ci": r["ci"]} for r in rows]},
            robustness=f"Hate speech: {by['measuring_hate_speech']['jev']:.0%} flagged by Jev vs "
                       f"{by['measuring_hate_speech']['people']:.0%} by raters. Where no rater of 10 saw a personal "
                       f"attack, Jev sees one {wa['flag_when_none']:.0%} of the time.",
            examples=seeded(_raters("civil_comments").filter((pl.col("crowd") == 0) & (pl.col("p") > 0.5))["id"].to_list(), "tox"))
    return spec, run


SEV = ["normal", "offensive", "hate_speech"]


def escalation():
    spec = Spec(
        id="judge_hate_escalation", family="judge", title="Jev moves posts one step up the severity ladder",
        question="Sorting social media posts into normal, offensive, or hate speech, does Jev put them on the same rung "
                 "as the annotators?",
        why="The difference between offensive and hateful is the hard part of content moderation, and where the "
            "policy decisions live. A model that reads rudeness as hate will over-enforce in a specific direction.",
        sourcing="Existing HateXplain posts (three annotators each, majority label), plus two cross-checks: Davidson "
                 "et al. 2017 tweets whose annotators said 'neither', and DynaHate statements labeled implicit "
                 "animosity. Enough: about 1,400 items. Harm-screened posts are not shown.",
        scoring="A 3x3 table of the annotators' majority label against Jev's most likely label; the share moved up a "
                "rung, down a rung, or kept; 90% bootstrap interval on the share moved up.",
        chart="A heat table: annotators' rung (rows) by Jev's rung (columns), with the step-up cells highlighted.",
        compared_with="HateXplain MTurk annotators (majority of 3); Davidson et al. CrowdFlower annotators; DynaHate labels",
        limits="The three-way labels come from each dataset's definitions, reworded as Jev options. Ties among three "
               "annotators are dropped.", sources=["hatexplain", "hate_speech_offensive", "dynahate"])

    def run():
        rows = []
        for r in source("hatexplain").iter_rows(named=True):
            hd = norm(biggest(r["humans"])["dist"])
            if sorted(hd.values())[-1] == sorted(hd.values())[-2]:
                continue
            rows.append({"id": r["id"], "c": SEV.index(top(hd)), "j": SEV.index(top(js(r["jev_dist"])))})
        t = pl.DataFrame(rows).with_columns((pl.col("j") - pl.col("c")).alias("d"))
        up = (t["d"] > 0).to_numpy()
        heat = t.group_by("c", "j").len().sort("c", "j").with_columns(
            pl.col("c").map_elements(lambda i: SEV[i], return_dtype=pl.Utf8).alias("people"),
            pl.col("j").map_elements(lambda i: SEV[i], return_dtype=pl.Utf8).alias("jev"))
        norm_up = t.filter(pl.col("c") == 0)["d"].gt(0).mean()
        off_up = t.filter(pl.col("c") == 1)["d"].gt(0).mean()
        hso = source("hate_speech_offensive")
        hso_up = float(np.mean([top(js(r["jev_dist"])) != "neither" for r in hso.iter_rows(named=True)
                                if top(norm(biggest(r["humans"])["dist"])) == "neither"]))
        dyn = [top(js(r["jev_dist"])) for r in source("dynahate").iter_rows(named=True) if _truth(r) == "animosity"]
        dyn_explicit = float(np.mean([x != "animosity" for x in dyn]))
        return Result(
            result=f"Jev moves {up.mean():.0%} of social media posts one or two rungs up from where the annotators put "
                   f"them, and almost none down ({(t['d'] < 0).mean():.0%}): it calls {off_up:.0%} of the posts they "
                   f"called merely offensive hate speech, and it calls {norm_up:.0%} of the posts they called normal "
                   f"either offensive or hateful.",
            evidence=f"{t.height} HateXplain posts with a clear majority; 90% interval on the share moved up {boot(up.astype(float))}",
            numbers={"up": float(up.mean()), "down": float((t["d"] < 0).mean()), "normal_up": norm_up,
                     "offensive_up": off_up, "hso_neither_flagged": hso_up, "dynahate_implicit_as_explicit": dyn_explicit,
                     "heat": heat.select("people", "jev", "len").to_dicts()}, n=t.height,
            chart={"type": "heat", "cells": heat.select("people", "jev", "len").to_dicts(), "x": "Jev's label",
                   "y": "annotators' label", "order": SEV},
            robustness=f"Same direction elsewhere: of {hso.height} tweets Davidson et al.'s annotators called neither "
                       f"offensive nor hateful, Jev calls {hso_up:.0%} one or the other; of {len(dyn)} DynaHate "
                       f"statements labeled implicit animosity, Jev calls {dyn_explicit:.0%} something more explicit.",
            examples=seeded(t.filter(pl.col("d") > 0)["id"].to_list(), "esc"))
    return spec, run


def crowd_split():
    spec = Spec(
        id="judge_crowd_split", family="judge", title="Jev's confidence reads like a share of raters",
        question="When the people rating a comment or a chatbot reply disagree among themselves, does Jev's probability "
                 "of yes match the share of raters who said yes?",
        why="A judge's probability is only useful if it means something. Rater splits are the closest thing to a ground "
            "truth for how debatable a call is; a probability that tracks them can stand in for a small panel.",
        sourcing="Existing Noul questions with several raters per item: Wikipedia personal attacks (about 10 raters), "
                 "Open Assistant 'the reply fails the task' (3-6 volunteers), and Measuring Hate Speech (3-5). "
                 "Enough: about 4,900 items.",
        scoring="Jev's mean probability of yes, binned by the share of raters saying yes (none, a few, about half, "
                "most, all); the mean distance from the diagonal where Jev's probability equals the rater share, "
                "weighted by items; rank correlation per dataset.",
        chart="Binned dots: the share of raters saying yes (x) against Jev's mean probability (y), one line per dataset, "
              "with the diagonal.",
        compared_with="The share of raters saying yes on each item",
        limits="A rater share is a small sample (3-10 people), so the bins with few items are noisy; 'about half' is "
               "rare with 3 raters.", sources=["wiki_attacks", "oasst_replies", "measuring_hate_speech"])

    def run():
        lines, all_rows = {}, []
        for name, label in [("wiki_attacks", "personal attacks"), ("oasst_replies", "reply fails the task"),
                            ("measuring_hate_speech", "hate speech")]:
            t = _raters(name).with_columns(pl.col("crowd").cut([0.001, 0.35, 0.65, 0.999], labels=["none", "few", "about half", "most", "all"]).alias("b"))
            g = t.group_by("b").agg(pl.col("p").mean(), pl.col("crowd").mean().alias("x"), pl.len()).sort("b").to_dicts()
            lines[label] = {"rho": spearmanr(t["p"], t["crowd"]).statistic, "bins": g,
                            "gap": float(sum(abs(b["p"] - b["x"]) * b["len"] for b in g) / t.height)}
            all_rows.append(t.with_columns(pl.lit(label).alias("set")))
        t = pl.concat(all_rows)
        gaps = (t["p"] - t["crowd"]).abs().to_numpy()
        o, w, h = (lines[k]["bins"] for k in ("reply fails the task", "personal attacks", "hate speech"))
        om = next(b for b in o if b["b"] == "most")
        wm = next(b for b in w if b["b"] == "most")
        return Result(
            result=f"Jev's probability of yes behaves like a share of raters: where about {om['x']:.0%} of Open Assistant "
                   f"volunteers said a reply fails the task, Jev gives {om['p']:.0%}; where {wm['x']:.0%} of Wikipedia "
                   f"raters saw a personal attack, {wm['p']:.0%}. It departs at the ends: {o[0]['p']:.0%} for replies no "
                   f"volunteer faulted, and {h[-1]['p']:.0%} for comments every hate speech rater flagged.",
            evidence=f"{t.height:,} items in 3 datasets; mean distance from the rater share (bin means, weighted) "
                     + ", ".join(f"{k} {v['gap']:.2f}" for k, v in lines.items())
                     + f"; item-level mean distance {gaps.mean():.2f}, 90% interval {boot(gaps)}",
            numbers={"lines": lines}, n=t.height,
            robustness="Rank correlation with the rater share: " + ", ".join(f"{k} {v['rho']:.2f}" for k, v in lines.items()) + ".",
            chart={"type": "binned", "x": "share of raters saying yes", "y": "Jev's probability of yes", "diagonal": True,
                   "lines": {k: [{"x": b["x"], "value": b["p"], "n": b["len"]} for b in v["bins"]] for k, v in lines.items()}},
            examples=seeded(t.filter((pl.col("set") == "reply fails the task") & (pl.col("crowd") == 0) & (pl.col("p") > 0.5))["id"].to_list(), "split"))
    return spec, run


def _lengths() -> dict:
    """Full lengths of the two answers in each pairwise item (the table truncates state at 2,000 characters)."""
    f = OUT / "_judge_lengths.json"
    if f.exists():
        return json.loads(f.read_text())
    from askjev import db
    with db.connect() as c:
        rows = c.execute("select id, state from questions where source in ('helpsteer2', 'mt_bench_human')").fetchall()
    out = {r["id"]: {k: len(str(v)) for k, v in r["state"].items()} for r in rows}
    f.write_text(json.dumps(out))
    return out


def pairwise():
    spec = Spec(
        id="judge_pairwise", family="judge", title="Judging AI answers: Jev agrees with people, length bias included",
        question="Shown two AI assistant answers to the same request, does Jev pick the one human judges picked, and "
                 "is it swayed by length or position more than they are?",
        why="Models are routinely used to judge other models. The known worries are a preference for longer answers "
            "and for whichever answer comes first or second; the useful question is whether that goes beyond what "
            "human judges already do.",
        sourcing="Existing HelpSteer2 preference pairs (3 annotators each) and MT-Bench human judgments (experts and "
                 "authors). Enough: about 2,300 pairs with a clear human preference. Answer lengths come from the full "
                 "stored text.",
        scoring="Agreement with the human preference (ties dropped); the share of choices going to the longer answer, "
                "binned by the length ratio, for Jev and for the judges; the share going to the first answer; agreement "
                "when the judges were unanimous vs split.",
        chart="Binned dots: length ratio of the first to the second answer (x) against the share choosing the first "
              "(y), Jev and human judges as two lines.",
        compared_with="HelpSteer2 annotators and MT-Bench expert judges",
        limits="Each pair is asked once, in the dataset's order; a swapped-order check needs new calls. MT-Bench "
               "conversations can be longer than Jev's 32k context allows in rare cases.",
        sources=["helpsteer2", "mt_bench_human"])

    def run():
        L = _lengths()
        rows = []
        for name, (a, b) in {"helpsteer2": ("response_1", "response_2"), "mt_bench_human": ("conversation_a", "conversation_b")}.items():
            for r in source(name).iter_rows(named=True):
                l = L.get(r["id"], {})
                if a not in l:
                    continue
                jd, hd = norm(js(r["jev_dist"])), norm(biggest(r["humans"])["dist"])
                if abs(hd.get(a, 0) - 0.5) < 0.01:
                    continue
                rows.append({"id": r["id"], "set": name, "j": jd.get(a, 0) > 0.5, "c": hd.get(a, 0) > 0.5,
                             "unan": hd.get(a, 0) in (0.0, 1.0), "lr": l[a] / max(l[b], 1)})
        t = pl.DataFrame(rows).with_columns((pl.col("j") == pl.col("c")).alias("agree"))
        x = t.filter((pl.col("lr") > 1.5) | (pl.col("lr") < 1 / 1.5)).with_columns((pl.col("lr") > 1).alias("lf"))
        jl, cl = float((x["j"] == x["lf"]).mean()), float((x["c"] == x["lf"]).mean())
        bins = t.with_columns(pl.col("lr").cut([0.5, 0.8, 1.25, 2], labels=["<0.5", "0.5-0.8", "about equal", "1.25-2", ">2"]).alias("b")) \
                .group_by("b").agg(pl.col("j").mean(), pl.col("c").mean(), pl.len()).sort("b").to_dicts()
        by = {s: float(t.filter(pl.col("set") == s)["agree"].mean()) for s in ("helpsteer2", "mt_bench_human")}
        ua, sa = float(t.filter(pl.col("unan"))["agree"].mean()), float(t.filter(~pl.col("unan"))["agree"].mean())
        hs = t.filter(pl.col("set") == "helpsteer2")
        return Result(
            result=f"Jev picks the same answer as human judges {t['agree'].mean():.0%} of the time "
                   f"({by['mt_bench_human']:.0%} on MT-Bench, {by['helpsteer2']:.0%} on HelpSteer2). When one answer is "
                   f"at least 1.5 times longer, Jev picks the longer one {jl:.0%} of the time and the judges {cl:.0%}: "
                   f"its taste for length is theirs, not an extra bias.",
            evidence=f"{t.height:,} pairs with a clear human preference; agreement {ua:.0%} when judges were unanimous, "
                     f"{sa:.0%} when split; 90% interval on overall agreement {boot(t['agree'].cast(float).to_numpy())}",
            numbers={"agree": float(t["agree"].mean()), "by_set": by, "longer_jev": jl, "longer_judges": cl, "bins": bins,
                     "first_jev_hs2": float(hs["j"].mean()), "first_judges_hs2": float(hs["c"].mean())}, n=t.height,
            chart={"type": "binned", "x": "length of the first answer / the second", "y": "share choosing the first",
                   "rows": [{"label": b["b"], "value": b["j"], "people": b["c"], "n": b["len"]} for b in bins]},
            robustness=f"Position: on HelpSteer2 Jev picks the first answer {hs['j'].mean():.0%} of the time, the "
                       f"judges {hs['c'].mean():.0%}, a small lean toward the second.",
            examples=seeded(t.filter(~pl.col("agree"))["id"].to_list(), "pair"))
    return spec, run


def helpful():
    spec = Spec(
        id="judge_helpful_reviews", family="judge", title="Jev finds almost every review helpful",
        question="Would Jev call an Amazon review helpful to shoppers, compared with how shoppers actually voted?",
        why="'Was this review helpful?' is a real crowd judgment of usefulness. A model that finds everything helpful "
            "is a poor filter, and generosity is a trait worth knowing in a judge.",
        sourcing="Existing Amazon reviews (McAuley 5-core) with the helpful and unhelpful vote counts, 10 or more votes "
                 "each. Enough: 2,500 reviews.",
        scoring="The share Jev calls helpful vs the share with a helpful majority; Jev's call binned by the share of "
                "shoppers voting helpful; rank correlation with the vote share.",
        chart="Binned dots: shoppers' helpful share (x) against the share Jev calls helpful (y).",
        compared_with="Amazon shoppers who voted on each review (median about 15 votes)",
        limits="Votes pile up on early and visible reviews, not only useful ones.", sources=["amazon_helpful"])

    def run():
        t = _raters("amazon_helpful")
        j = (t["p"] > 0.5).to_numpy()
        rho = spearmanr(t["p"], t["crowd"]).statistic
        bins = t.with_columns(pl.col("crowd").cut([0.001, 0.2, 0.4, 0.6, 0.8], labels=["0%", "1-20%", "20-40%", "40-60%", "60-80%", "80%+"]).alias("b")) \
                .group_by("b").agg((pl.col("p") > 0.5).mean().alias("j"), pl.len()).sort("b").to_dicts()
        low = t.filter(pl.col("crowd") < 0.4)
        return Result(
            result=f"Jev calls {j.mean():.0%} of Amazon reviews helpful; shoppers' votes favor {(t['crowd'] > 0.5).mean():.0%}. "
                   f"Of reviews most voters found unhelpful (under 40% helpful votes), Jev still calls "
                   f"{(low['p'] > 0.5).mean():.0%} helpful, and {bins[0]['j']:.0%} of those with no helpful votes at all.",
            evidence=f"{t.height:,} reviews with 10+ votes; rank correlation with the helpful share {rho:.2f}; 90% interval "
                     f"on Jev's helpful share {boot(j.astype(float))}",
            numbers={"jev": float(j.mean()), "shoppers": float((t["crowd"] > 0.5).mean()), "rho": rho, "bins": bins},
            n=t.height, chart={"type": "binned", "x": "shoppers voting helpful", "y": "share Jev calls helpful",
                               "rows": [{"label": b["b"], "value": b["j"], "n": b["len"]} for b in bins]},
            examples=seeded(t.filter((pl.col("crowd") == 0) & (pl.col("p") > 0.5))["id"].to_list(), "help"))
    return spec, run


def negativity():
    spec = Spec(
        id="judge_mixed_reviews", family="judge", title="Jev reads a mixed review as a bad one",
        question="Reading a review, does Jev hear the complaints louder than the writer meant them?",
        why="Most real reviews mix praise and gripes. Whether a reader weights the gripes more is a negativity bias, "
            "and it changes summaries, routing, and any rating a model infers.",
        sourcing="Existing Amazon reviews with their star rating (Jev reads the text and picks one of five described "
                 "levels of satisfaction) and Steam reviews with the player's thumbs up or down. Enough: about 4,700.",
        scoring="Jev's mean level for each star rating; the share of 3-star reviews it reads as a let-down or a "
                "failure vs as pleased; on Steam, the share of thumbs-up reviews read as thumbs-down and the reverse.",
        chart="Dots per star rating: the star level (0-4) and Jev's mean reading of the same reviews.",
        compared_with="The reviewers' own star ratings and thumbs",
        limits="A star rating is the writer's summary, not the only right reading of the text.",
        sources=["amazon_reviews", "steam_reviews"])

    def run():
        rows = []
        for r in source("amazon_reviews").iter_rows(named=True):
            if r["truth"] is not None:
                d = js(r["jev_dist"])
                rows.append({"id": r["id"], "t": int(_truth(r)), "j": level(d), "jt": int(top(d))})
        t = pl.DataFrame(rows)
        rho = spearmanr(t["t"], t["j"]).statistic
        by = t.group_by("t").agg(pl.col("j").mean(), pl.len()).sort("t").to_dicts()
        mid = t.filter(pl.col("t") == 2)
        down, upm = float((mid["jt"] < 2).mean()), float((mid["jt"] > 2).mean())
        st = source("steam_reviews")
        y = np.array([_p(r) > 0.5 for r in st.iter_rows(named=True)])
        lab = np.array([_truth(r) is True for r in st.iter_rows(named=True)])
        up_as_down, down_as_up = float((~y[lab]).mean()), float(y[~lab].mean())
        return Result(
            result=f"Of Amazon reviews the writer gave 3 stars, Jev reads {down:.0%} as a let-down or a failure and "
                   f"{upm:.0%} as pleased. On Steam it reads {up_as_down:.0%} of thumbs-up reviews as thumbs-down, but "
                   f"only {down_as_up:.0%} of thumbs-down reviews as thumbs-up. It still orders reviews "
                   f"{agree_word(rho)} by stars (rank correlation {rho:.2f}).",
            evidence=f"{t.height:,} Amazon reviews (about 450 per star level) and {len(y):,} Steam reviews",
            numbers={"by_star": by, "mid_down": down, "mid_up": upm, "steam_up_as_down": up_as_down,
                     "steam_down_as_up": down_as_up, "rho": rho}, n=t.height + len(y),
            robustness=f"On the 0-4 scale where 2 means torn, Jev reads 3-star reviews at {by[2]['j']:.1f} on average; "
                       f"1-star and 5-star reviews it reads almost exactly ({by[0]['j']:.1f} and {by[4]['j']:.1f}).",
            chart={"type": "dots", "domain": [0, 4], "rows": [{"label": f"{b['t'] + 1} stars", "value": b["j"], "people": b["t"]} for b in by]},
            examples=seeded(mid.filter(pl.col("jt") < 2)["id"].to_list(), "mixed"))
    return spec, run


NOUN = {"Wine critic notes": "wine notes", "Sentence similarity": "sentence pairs", "Seventh-grade essays": "essays",
        "Amazon review satisfaction": "Amazon reviews"}


def top_grade():
    spec = Spec(
        id="judge_top_grade", family="judge", title="Jev rarely gives the top grade when reading others' judgments",
        question="Asked to read how highly a critic rated a wine, how close two sentences are in meaning, or how "
                 "satisfied a reviewer is, how often does Jev land on the top level compared with the real answer?",
        why="Reading a judgment off text is a common task (inferring ratings, grading, deduplication). If a reader "
            "shies away from the top of every scale, the best items blur into the very good ones.",
        sourcing="Existing Score questions with a known level: wine critic notes (Wine Enthusiast points binned into "
                 "5 even groups), STS-B sentence pairs (6 levels of similarity from annotators' means), Amazon reviews "
                 "(5 star levels) and seventh-grade essays (ASAP, 4 teacher score levels). Enough: about 7,400 items, "
                 "the first three balanced by level.",
        scoring="The share of items whose true level is the top one, vs the share where Jev's most likely level is the "
                "top one; Jev's mean level for the top-level items; rank correlation per set.",
        chart="Paired bars per dataset: share at the top level, true vs Jev.",
        compared_with="The datasets' own levels (critic points, annotator means, stars, teacher scores)",
        limits="The levels are described situations written for Jev from each dataset's scale; bin edges are ours.",
        sources=["wine_notes", "stsb_similarity", "amazon_reviews", "asap_essays"])

    def run():
        rows = []
        for name, label in [("wine_notes", "Wine critic notes"), ("stsb_similarity", "Sentence similarity"),
                            ("amazon_reviews", "Amazon review satisfaction"), ("asap_essays", "Seventh-grade essays")]:
            q = source(name)
            k = len(js(q.row(0, named=True)["options"])) - 1
            t = pl.DataFrame([{"t": int(_truth(r)), "j": level(js(r["jev_dist"])), "jt": int(top(js(r["jev_dist"])))}
                              for r in q.iter_rows(named=True) if r["truth"] is not None])
            rows.append({"label": label, "n": t.height, "levels": k + 1, "true_top": float((t["t"] == k).mean()),
                         "jev_top": float((t["jt"] == k).mean()),
                         "top_items_mean": float(t.filter(pl.col("t") == k)["j"].mean()),
                         "top_items_hit": float((t.filter(pl.col("t") == k)["jt"] == k).mean()),
                         "rho": spearmanr(t["t"], t["j"]).statistic})
        w = rows[0]
        stingy = [r for r in rows if r["jev_top"] < r["true_top"] * 0.6]
        return Result(
            result="Jev rarely hands out the top grade when reading someone else's: it gives it to "
                   + and_list([f"{r['jev_top']:.0%} of {NOUN.get(r['label'], r['label'].lower())} (the real share is {r['true_top']:.0%})"
                               for r in rows if r in stingy])
                   + f". It still orders the wines well (rank correlation {w['rho']:.2f}). "
                   + and_list([NOUN.get(r["label"], r["label"].lower()).capitalize() for r in rows if r not in stingy])
                   + " are the exception.",  # every noun is plural
            evidence="; ".join(f"{r['label']}: top level {r['true_top']:.0%} true vs {r['jev_top']:.0%} Jev (n={r['n']:,})" for r in rows),
            numbers={"sets": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "bars2", "labels": [r["label"] for r in rows], "a": [r["true_top"] for r in rows],
                   "b": [r["jev_top"] for r in rows], "a_label": "true share at the top", "b_label": "Jev at the top"},
            robustness="; ".join(f"{r['label']} is the exception ({r['true_top']:.0%} vs {r['jev_top']:.0%})."
                                 for r in rows if r not in stingy),
            examples=[])
    return spec, run


def essays():
    spec = Spec(
        id="judge_essays", family="judge", title="Jev grades seventh-graders' spelling harder than their teachers",
        question="Scoring seventh-grade essays on ideas, organization, and conventions (spelling, grammar, "
                 "punctuation), is Jev harsher or softer than the teachers who scored them?",
        why="Automated essay scoring is widely used on children's writing. A grader that is fair on ideas but harsh on "
            "mechanics penalizes exactly the students still learning to spell.",
        sourcing="Existing ASAP essay-set 7 items (Kaggle Hewlett Foundation), one question per trait with the "
                 "teachers' 4-level rubric described as situations; 700 essays per trait. Enough.",
        scoring="Per trait, Jev's mean expected level minus the teachers' level, with 90% bootstrap intervals over "
                "essays; rank correlation per trait.",
        chart="Dots per trait: teachers' mean level and Jev's, with intervals.",
        compared_with="The teachers' rubric scores in the ASAP dataset",
        limits="Names and some capitalized words are replaced with placeholders like @CAPS1 in the data; Jev is told "
               "so, but the placeholders may still read as errors. Essays over 2,000 characters are shown in full.",
        sources=["asap_essays"])

    def run():
        rows = []
        for r in source("asap_essays").iter_rows(named=True):
            rows.append({"id": r["id"], "trait": (js(r["meta"]) or {}).get("trait"), "t": int(_truth(r)),
                         "j": level(js(r["jev_dist"]))})
        t = pl.DataFrame(rows)
        by = []
        for (tr,), g in t.group_by("trait"):
            d = (g["j"] - g["t"]).to_numpy()
            by.append({"label": tr, "value": float(g["j"].mean()), "people": float(g["t"].mean()), "gap": float(d.mean()),
                       "ci": boot(d), "rho": spearmanr(g["j"], g["t"]).statistic, "n": g.height})
        by.sort(key=lambda b: b["gap"])
        c = by[0]
        how = "a full level" if abs(c["gap"]) >= 0.95 else f"{abs(c['gap']):.1f} levels"
        return Result(
            result=f"Jev scores seventh-graders' {c['label']} (spelling, grammar, punctuation) "
                   f"{how} below their teachers on a 4-level rubric, and agrees with them least there (rank "
                   f"correlation {c['rho']:.2f}); on ideas it is within {abs(next(b for b in by if b['label'] == 'ideas')['gap']):.2f} "
                   f"of the teachers and tracks them best ({next(b for b in by if b['label'] == 'ideas')['rho']:.2f}).",
            evidence=f"{t.height:,} scores, {len(by)} traits; 90% intervals over essays",
            numbers={"traits": by}, n=t.height,
            chart={"type": "dots", "domain": [0, 3], "rows": [{"label": b["label"], "value": b["value"], "people": b["people"], "ci": None} for b in by]},
            examples=seeded(t.filter((pl.col("trait") == c["label"]) & (pl.col("j") - pl.col("t") <= -1.5))["id"].to_list(), "essay"))
    return spec, run


def fakes():
    spec = Spec(
        id="judge_fake_reviews", family="judge", title="Jev believes fake hotel reviews",
        question="Can Jev tell a real review from a fake one, when the fake was written by a person paid to invent a "
                 "hotel stay, or by a text generator?",
        why="Deceptive reviews are a real market problem. Ott et al. 2011 found people barely beat chance on the "
            "hotel set and tend to believe what they read; a model might do the same, or better.",
        sourcing="Existing Deceptive Opinion Spam items (Ott et al. 2011: 400 truthful and 400 invented Chicago hotel "
                 "reviews, the invented ones written by paid MTurk workers) and a set of real vs machine-generated "
                 "product reviews (Salminen et al. 2022). Enough: 2,760 reviews, balanced.",
        scoring="Accuracy against the labels, and the direction of errors: the share of fakes Jev accepts as real.",
        chart="Paired bars per dataset: the share of fakes Jev calls real, and the share of real reviews it calls fake.",
        compared_with="The datasets' labels; Ott et al. 2011's human judges as reference (near chance, trusting)",
        limits="The generated reviews come from an older text generator; newer ones would be harder.",
        sources=["op_spam_reviews", "fake_reviews"])

    def run():
        op = source("op_spam_reviews")
        yo = np.array([_p(r) > 0.5 for r in op.iter_rows(named=True)])      # yes = real guest
        lo = np.array([_truth(r) is True for r in op.iter_rows(named=True)])
        fk = source("fake_reviews")
        yf = np.array([_p(r) > 0.5 for r in fk.iter_rows(named=True)])      # yes = generated
        lf = np.array([_truth(r) is True for r in fk.iter_rows(named=True)])
        hotel_fake_believed, hotel_acc = float(yo[~lo].mean()), float((yo == lo).mean())
        gen_believed, gen_acc = float((~yf[lf]).mean()), float((yf == lf).mean())
        return Result(
            result=f"Jev accepts {hotel_fake_believed:.0%} of invented hotel reviews as written by real guests (it "
                   f"calls {yo.mean():.0%} of all of them real), so it does no better than a coin on that set "
                   f"({hotel_acc:.0%}). Machine-generated product reviews are another matter: it catches "
                   f"{1 - gen_believed:.0%} of them and is right {gen_acc:.0%} of the time.",
            evidence=f"{len(yo)} hotel reviews (half invented), {len(yf):,} product reviews (half generated); 90% interval "
                     f"on hotel accuracy {boot((yo == lo).astype(float))}",
            numbers={"hotel_acc": hotel_acc, "hotel_fake_believed": hotel_fake_believed, "hotel_real_share": float(yo.mean()),
                     "gen_acc": gen_acc, "gen_believed": gen_believed, "real_called_generated": float(yf[~lf].mean())},
            n=len(yo) + len(yf),
            chart={"type": "bars2", "labels": ["Invented hotel reviews", "Generated product reviews"],
                   "a": [hotel_fake_believed, gen_believed], "b": [float(1 - yo[lo].mean()), float(yf[~lf].mean())],
                   "a_label": "fakes accepted as real", "b_label": "real reviews called fake"},
            robustness="Ott et al. 2011 report human judges at 53-62% on the same hotel reviews, most of them "
                       "judging nearly everything truthful.",
            examples=seeded([r["id"] for r, y, l in zip(op.iter_rows(named=True), yo, lo) if y and not l], "fake"))
    return spec, run


EXPERIMENTS = [toxicity_line(), escalation(), crowd_split(), pairwise(), helpful(), negativity(), top_grade(), essays(),
               fakes()]
