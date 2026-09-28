"""Humor experiments: rating jokes and captions against the crowds that rated them, guessing which of two got more
upvotes, and telling satire from news.

Ratings use the robust level (the question as asked, averaged with the same question with its levels reversed, stored
in the original order), as in fam_taste.
"""

from __future__ import annotations

import json
import re

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, biggest, boot, js, level, norm, seeded, source, top


def robust(r: dict) -> tuple[float, float | None]:
    """(robust level, reversed-levels level) for one score question."""
    base = level(js(r["jev_dist"]))
    rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v["kind"] == "reversed_levels"), None)
    return ((base + rev) / 2 if rev is not None else base), rev


def rho_ci(a: np.ndarray, b: np.ndarray, reps: int = 300) -> list[float]:
    idx = np.arange(len(a))
    return boot(idx, stat=lambda ii: spearmanr(a[ii.astype(int)], b[ii.astype(int)]).statistic, b=reps)


def crowd_rows(src: str, text_of) -> pl.DataFrame:
    rows = []
    for r in source(src).iter_rows(named=True):
        h = biggest(r["humans"])
        if not h:
            continue
        score, rev = robust(r)
        rows.append({"id": r["id"], "text": text_of(r), "jev": score, "base": level(js(r["jev_dist"])), "rev": rev,
                     "crowd": level(h["dist"]), "n": h.get("n") or 0, "src": h.get("source", ""),
                     "jt": int(top(js(r["jev_dist"]))), "ct": int(top(h["dist"]))})
    return pl.DataFrame(rows)


def captions():
    spec = Spec(
        id="humor_new_yorker_captions", family="humor", title="Jev can't tell which New Yorker captions are funny",
        question="Rating captions entered in the New Yorker Cartoon Caption Contest, does Jev find funny the ones "
                 "the contest's voters found funny?",
        why="The caption contest is the purest test of taste in jokes: same cartoon, a dozen captions, hundreds of "
            "voters each. If a model has a sense of humor, it should at least tell the better captions from the worse.",
        sourcing="Existing questions ('How funny is this caption for the cartoon?', three levels: unfunny, somewhat "
                 "funny, funny), with the cartoon described in words and the caption attached; each has the voters' "
                 "unfunny / somewhat / funny split from the NEXT crowd-rating data (median 165 votes per caption). "
                 "Enough: 2,915 captions from 224 contests.",
        scoring="Rank correlation between Jev's robust level and the voters' mean level, over all captions and within "
                "each contest (captions are only comparable against the same cartoon); how often the voters' favorite "
                "caption in a contest is also Jev's favorite, against the chance rate of 1 in the number of captions.",
        chart="A scatter of voters' mean level (x) against Jev's (y), one dot per caption, with the per-contest "
              "correlations as a strip below.",
        compared_with="New Yorker Caption Contest voters (NEXT crowd ratings, about 165 votes per caption)",
        limits="Jev reads a text description of the cartoon, not the drawing; voters saw the drawing. Most submitted "
               "captions are unfunny to voters, so differences are small; the contest's published winners are not "
               "in this set.", sources=["caption_contest"])

    def run():
        t = crowd_rows("caption_contest", lambda r: js(r["state"])["caption"])
        t = t.with_columns(pl.col("src").map_elements(lambda s: (re.search(r"(\d+)(?:_\w+)?\.csv", s) or [None, s])[1],
                                                      return_dtype=pl.String).alias("contest"))
        rho = spearmanr(t["jev"], t["crowd"]).statistic
        ci = rho_ci(t["jev"].to_numpy(), t["crowd"].to_numpy())
        per, hits, chance = [], [], []
        for _, g in t.group_by("contest"):
            if g.height < 5:
                continue
            per.append(float(spearmanr(g["jev"], g["crowd"]).statistic))
            best = g.sort("crowd", descending=True)["id"][0]
            hits.append(g.sort("jev", descending=True)["id"][0] == best)
            chance.append(1 / g.height)
        somewhat = float((t["jt"] == 1).mean())
        crowd_unfunny = float((t["ct"] == 0).mean())
        return Result(
            result=f"Jev's funniness ratings of {t.height:,} contest captions have essentially no relation to the voters' "
                   f"(rank correlation {rho:.2f}; median {np.nanmedian(per):.2f} within a contest). Its favorite caption "
                   f"is the voters' favorite in {np.mean(hits):.0%} of {len(hits)} contests, near the {np.mean(chance):.0%} "
                   f"a random pick would get. It calls {somewhat:.0%} of captions 'somewhat funny'; voters' most common "
                   f"verdict is 'unfunny' for {crowd_unfunny:.0%}.",
            evidence=f"{t.height:,} captions, {len(hits)} contests with 5+ captions; 90% interval on the overall "
                     f"correlation {ci[0]:.2f} to {ci[1]:.2f}",
            numbers={"rho": rho, "ci90": ci, "per_contest_median": float(np.nanmedian(per)), "top_hit": float(np.mean(hits)),
                     "chance": float(np.mean(chance)), "jev_somewhat": somewhat, "crowd_unfunny": crowd_unfunny,
                     "per_contest": per},
            chart={"type": "scatter", "points": t.select("crowd", "jev").to_numpy().round(3).tolist(),
                   "x": "voters' mean level (0-2)", "y": "Jev's level (0-2)", "strip": per, "strip_label": "per-contest correlation"},
            examples=seeded(t["id"].to_list(), "captions"), n=t.height,
            robustness=f"With the levels reversed the correlation is "
                       f"{spearmanr(t['rev'], t['crowd'], nan_policy='omit').statistic:.2f}.")
    return spec, run


def three_crowds():
    spec = Spec(
        id="humor_three_crowds", family="humor", title="Old jokes yes, new captions no: where Jev's humor matches crowds",
        question="Across three sets of human funniness ratings (classic jokes, edited news headlines, cartoon "
                 "captions), where does Jev's sense of funny line up with people's?",
        why="Humor is one of the places a model's taste could be most different from ours; comparing three crowds "
            "separates 'can't rank jokes at all' from 'can rank some kinds of jokes'.",
        sourcing="Existing rating questions with human rating distributions: Jester (100 classic jokes, thousands of "
                 "ratings each), Humicroedit (4,383 news headlines with one word swapped for a joke, 5 judges each), "
                 "and New Yorker contest captions (2,915, about 165 voters each). Enough.",
        scoring="Per set, rank correlation between Jev's robust level and the crowd's mean level, with a 90% bootstrap "
                "interval over items. Humicroedit's 5 judges make its crowd means noisy, which caps any correlation.",
        chart="Three dots with intervals, one per crowd, on a -1 to 1 scale.",
        compared_with="Jester users, Humicroedit crowd judges (MTurk), New Yorker contest voters",
        limits="The sets differ in format and in how famous the jokes are: Jester's jokes circulate widely online, so "
               "Jev may know how they are received rather than find them funny.",
        sources=["jester", "humicroedit", "caption_contest"])

    def run():
        sets = [("jester", "Classic jokes (Jester)", lambda r: js(r["state"])["joke"]),
                ("humicroedit", "Edited headlines (Humicroedit)", lambda r: js(r["state"])["edited_headline"]),
                ("caption_contest", "Cartoon captions (New Yorker)", lambda r: js(r["state"])["caption"])]
        rows = []
        for src, label, f in sets:
            t = crowd_rows(src, f)
            rho = float(spearmanr(t["jev"], t["crowd"]).statistic)
            rows.append({"label": label, "value": rho, "ci": rho_ci(t["jev"].to_numpy(), t["crowd"].to_numpy()),
                         "n": t.height, "crowd_n": float(t["n"].median())})
        j, h, c = rows
        return Result(
            result=f"Jev ranks {j['n']} classic jokes {agree_word(j['value'])} like Jester's users (rank correlation "
                   f"{j['value']:.2f}), edited news headlines {agree_word(h['value'])} like their judges ({h['value']:.2f}), "
                   f"and New Yorker captions not at all ({c['value']:.2f}).",
            evidence="; ".join(f"{r['label']}: {r['n']:,} items, median {r['crowd_n']:.0f} raters, 90% interval "
                               f"{r['ci'][0]:.2f} to {r['ci'][1]:.2f}" for r in rows),
            numbers={"sets": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "domain": [-1, 1], "zero": 0,
                   "rows": [{"label": r["label"], "value": r["value"], "ci": r["ci"]} for r in rows]})
    return spec, run


def upvotes():
    spec = Spec(
        id="humor_upvote_guess", family="humor", title="Asked which joke got more upvotes, Jev picks the second one",
        question="Shown two jokes from r/Jokes, or two captions on the same Imgflip meme, can Jev tell which one got "
                 "more upvotes, and what does it do when it can't?",
        why="Upvotes are the internet's verdict on funny. A model that can't read that verdict falls back on "
            "something, and what it falls back on is itself a finding about how it chooses.",
        sourcing="Existing pair questions ('Which joke, `joke_1` or `joke_2`, got more upvotes...'), each with the "
                 "true answer from the post scores; which item is shown first was randomized when the pairs were "
                 "built. Enough: 2,301 joke pairs and 2,655 caption pairs.",
        scoring="Share of pairs where Jev's pick is the more-upvoted one, with 90% bootstrap intervals; share of pairs "
                "where it picks the item shown second, whichever is right; accuracy by Jev's confidence.",
        chart="Paired bars per set: accuracy when the right answer was shown first vs second, with 50% marked.",
        compared_with="Reddit r/Jokes and Imgflip upvote counts",
        limits="Upvotes depend on timing and luck as well as quality. Reordering the answer options in the question "
               "doesn't change Jev's answer here; the lean is toward the item shown second in the text, which also "
               "carries the label ending in 2.", sources=["rjokes_pairs", "imgflip_captions"])

    def run():
        rows, out = [], []
        for src, label, k in [("rjokes_pairs", "r/Jokes jokes", "joke"), ("imgflip_captions", "Imgflip captions", "caption")]:
            for r in source(src).iter_rows(named=True):
                d = norm(js(r["jev_dist"]))
                truth = json.loads(r["truth"])
                rows.append({"id": r["id"], "set": label, "ok": top(d) == truth, "second": top(d) == f"{k}_2",
                             "truth_second": truth == f"{k}_2"})
        t = pl.DataFrame(rows)
        for (label,), g in t.group_by("set", maintain_order=True):
            out.append({"label": label, "acc": float(g["ok"].mean()), "ci": boot(g["ok"].cast(float).to_numpy()),
                        "second": float(g["second"].mean()),
                        "acc_first": float(g.filter(~pl.col("truth_second"))["ok"].mean()),
                        "acc_second": float(g.filter(pl.col("truth_second"))["ok"].mean()), "n": g.height})
        j, c = out
        return Result(
            result=f"Jev guesses which of two jokes got more upvotes {j['acc']:.0%} of the time and which of two meme "
                   f"captions {c['acc']:.0%}, close to a coin flip. What it does instead is pick the one shown second: "
                   f"{j['second']:.0%} of the time for jokes, {c['second']:.0%} for captions, so it is right "
                   f"{c['acc_second']:.0%} of the time when the better caption comes second and {c['acc_first']:.0%} "
                   f"when it comes first.",
            evidence=f"{j['n']:,} joke pairs (90% interval on accuracy {j['ci'][0]:.2f} to {j['ci'][1]:.2f}); "
                     f"{c['n']:,} caption pairs ({c['ci'][0]:.2f} to {c['ci'][1]:.2f})",
            numbers={"sets": out}, n=t.height,
            chart={"type": "bars2", "labels": [o["label"] for o in out], "a": [o["acc_first"] for o in out],
                   "b": [o["acc_second"] for o in out], "a_label": "right answer shown first",
                   "b_label": "right answer shown second", "ref": 0.5},
            robustness="Shuffling the order of the answer options changes Jev's pick in about 3% of pairs (its "
                       "probability moves 0.01 on average), so the lean follows the order of the texts in the "
                       "question, not the option list.",
            examples=seeded(t.filter(~pl.col("ok"))["id"].to_list(), "upvotes"))
    return spec, run


def satire():
    spec = Spec(
        id="humor_satire", family="humor", title="One Onion headline in five reads as real news to Jev",
        question="Shown a headline from The Onion or a real news site, how often does Jev mistake satire for news, "
                 "or news for satire?",
        why="Satire works by reporting the absurd with a straight face; a model that reads literally (a weakness "
            "TypeSafe documents, 01-jev §6.1) should miss some of it. The misses show which jokes are too deadpan.",
        sourcing="Existing questions ('Is `headline` sarcastic?') on the News Headlines Dataset for Sarcasm Detection "
                 "(Misra 2019): Onion headlines are satire, HuffPost headlines are not. Enough: 1,206 headlines.",
        scoring="Share of Onion headlines Jev calls straight news, share of real headlines it calls satire, each with a "
                "90% bootstrap interval; accuracy by Jev's confidence.",
        chart="A 2x2 table (real source vs Jev's call) with the share in each cell, and the misses listed.",
        compared_with="the headline's real source (The Onion or HuffPost)",
        limits="Literal reading is a documented Jev weakness (01-jev §6.1); this puts a number on it for satire. "
               "Some HuffPost headlines are themselves wry, and the dataset is from 2014-2018.",
        sources=["sarcasm_headlines"])

    def run():
        rows = []
        for r in source("sarcasm_headlines").iter_rows(named=True):
            d = norm(js(r["jev_dist"]))
            rows.append({"id": r["id"], "h": js(r["state"])["headline"], "onion": bool(json.loads(str(r["truth"]).lower())),
                         "says": top(d) == "true", "conf": max(d.values())})
        t = pl.DataFrame(rows)
        on, real = t.filter(pl.col("onion")), t.filter(~pl.col("onion"))
        missed, flagged = on.filter(~pl.col("says")), real.filter(pl.col("says"))
        sure = t.filter(pl.col("conf") > 0.9)
        acc_sure = float((sure["says"] == sure["onion"]).mean())
        return Result(
            result=f"Jev takes {len(missed) / on.height:.0%} of Onion headlines for real news, like \"{missed.sort('conf', descending=True)['h'][0]}\", "
                   f"and calls {len(flagged) / real.height:.0%} of real headlines satire. When it is more than 90% sure "
                   f"it is right {acc_sure:.0%} of the time.",
            evidence=f"{on.height} Onion and {real.height} HuffPost headlines; 90% intervals "
                     f"{boot((~on['says']).cast(float).to_numpy())} and {boot(real['says'].cast(float).to_numpy())}",
            numbers={"onion_missed": len(missed) / on.height, "real_flagged": len(flagged) / real.height,
                     "acc_when_sure": acc_sure, "missed": missed.sort("conf", descending=True).head(10)["h"].to_list(),
                     "flagged": flagged.sort("conf", descending=True).head(10)["h"].to_list()},
            chart={"type": "heat", "cells": [{"p": "Onion", "j": "satire", "len": len(on) - len(missed)},
                                             {"p": "Onion", "j": "news", "len": len(missed)},
                                             {"p": "HuffPost", "j": "satire", "len": len(flagged)},
                                             {"p": "HuffPost", "j": "news", "len": len(real) - len(flagged)}],
                   "x": "Jev's call", "y": "real source"},
            examples=missed.sort("conf", descending=True)["id"].head(2).to_list() + flagged.sort("conf", descending=True)["id"].head(1).to_list(),
            n=t.height)
    return spec, run


EXPERIMENTS = [captions(), three_crowds(), upvotes(), satire()]
