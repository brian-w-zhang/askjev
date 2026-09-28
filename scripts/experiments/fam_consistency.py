"""Consistency experiments: does the order of the options matter, how much does the same question move when asked
again, where the middle-of-the-scale habit shows up, and how Jev's answer for itself differs from its answer for
most people."""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import polars as pl

from lib import Result, Spec, biggest, boot, level, norm, seeded, table, top

# Taste ratings have their own self-vs-guess experiment (taste_self_vs_guess).
TASTE = ["taste_ratings", "g5_w13_ratings"]


def _nice(l2: str) -> str:
    return l2.split(".")[-1].replace("_", " ")


@lru_cache(maxsize=1)
def pairs() -> dict:
    """Choice shuffles and Score reversals, read once.

    Two-option questions get three extra probes: reversed, original, reversed again (answer.py). The two reversed
    probes are the same request asked twice, so their gap is the noise of asking again; reversed vs original is the
    order effect on top of that noise."""
    same, flipped, boost, base_same, ids2 = [], [], [], [], []
    first_k, score_shift, score_keep, score_ids = [], [], [], []
    t = table().filter(pl.col("variants").is_not_null())
    for qid, v, jd, prim in t.select("id", "variants", "jev_dist", "primitive").iter_rows():
        vs = json.loads(v)
        if prim == "choice":
            sh = sorted((x for x in vs if x["kind"] == "shuffle"), key=lambda x: x["params"]["i"])
            if len(sh) == 3 and len(sh[0]["params"]["order"]) == 2:
                a, b, c = (norm(x["dist"]) for x in sh)
                o = sh[0]["params"]["order"][0]            # listed first in the reversed probes, second in the original
                same.append((a[o], c[o]))
                flipped.append(abs(a[o] - b[o]))
                boost.append((a[o] + c[o]) / 2 - b[o])
                base_same.append(abs(norm(json.loads(jd)).get(o, 0) - b[o]))
                ids2.append(qid)
            elif len(sh) >= 2 and len(sh[0]["params"]["order"]) >= 3:
                ds = [norm(x["dist"]) for x in sh]
                mean = {k: np.mean([d.get(k, 0) for d in ds]) for k in ds[0]}
                first_k += [d.get(x["params"]["order"][0], 0) - mean[x["params"]["order"][0]] for d, x in zip(ds, sh)]
        elif prim == "score":
            r = next((x for x in vs if x["kind"] == "reversed_levels"), None)
            if r:
                d = json.loads(jd)
                k = len(d) - 1
                if k > 0:
                    score_shift.append((level(r["dist"]) - level(d)) / k)   # + = toward the top level, listed first when reversed
                    score_keep.append(top(r["dist"]) == top(d))
                    score_ids.append(qid)
    return {"same": np.array(same), "flipped": np.array(flipped), "boost": np.array(boost),
            "base_same": np.array(base_same), "ids2": ids2, "first_k": np.array(first_k),
            "score_shift": np.array(score_shift), "score_keep": np.array(score_keep), "score_ids": score_ids}


def option_order():
    spec = Spec(
        id="consistency_option_order", family="consistency", title="The order of the options doesn't matter to Jev",
        question="When the same options are listed in a different order, or a rating scale is turned upside down, does "
                 "Jev's answer move more than it does when the question is simply asked again?",
        why="People and most language models favor whatever is listed first (or last). TypeSafe doesn't document "
            "position bias either way (docs/01-jev.md §6 lists it as open ground); a model that ignores order is "
            "safer to use for ranking and multiple choice.",
        sourcing="Every pick-one question in the corpus was also asked with its options shuffled three times; "
                 "two-option questions were asked reversed, in the original order, and reversed again, so the same "
                 "request was sent twice. Every rating question was also asked with its levels reversed. Enough: "
                 "214,000 two-option questions, 160,000+ questions with three to six options, 168,000 rating questions.",
        scoring="Two-option questions: the mean change in the probability of one option (a) between the two identical "
                "reversed probes (the noise of asking again) and (b) between reversed and original order (noise plus "
                "any order effect); the first-slot boost is how much more probability an option gets when it is listed "
                "first. Larger menus: the same boost for the first slot, against the option's average over three "
                "orders. Rating questions: the shift in Jev's expected level when the scale is reversed, as a share of "
                "the scale's length. 90% intervals by bootstrap over questions.",
        chart="Three bars in probability points: asked again in the same order, asked again against the base probe, "
              "options reversed; with the first-slot boost as a dot at zero.",
        compared_with="Jev itself, asked the same request twice (the noise floor)",
        limits="Only three orderings per question, one of them a repeat. The noise floor comes from two-option "
               "questions only. From outside it can't be told whether the model itself ignores order or the gateway "
               "normalizes the options before the model sees them; for a user the effect is the same.", sources=[])

    def run():
        p = pairs()
        same = np.abs(p["same"][:, 0] - p["same"][:, 1])
        rows = [("Same order, asked again", same), ("Same order, base probe vs shuffle probe", p["base_same"]),
                ("Options reversed", p["flipped"])]
        bars = [{"label": l, "value": float(x.mean() * 100), "ci": [c * 100 for c in boot(x, b=200)]} for l, x in rows]
        b, fk, ss = p["boost"], p["first_k"], p["score_shift"]
        return Result(
            result=f"Reversing two options moves Jev's probability by {bars[2]['value']:.2f} points on average, the same "
                   f"as asking the identical question again ({bars[0]['value']:.2f}). Being listed first is worth "
                   f"{b.mean() * 100:+.2f} points; on longer menus {fk.mean() * 100:+.2f}. Turning a rating scale "
                   f"upside down shifts its answer by {ss.mean() * 100:+.1f}% of the scale.",
            evidence=f"{len(b):,} two-option questions (90% interval on the first-slot boost {[round(x * 100, 2) for x in boot(b, b=200)]} "
                     f"points); {len(fk):,} first-slot placements on 3-6 option menus; {len(ss):,} reversed rating scales",
            numbers={"bars": bars, "boost": float(b.mean()), "boost_k": float(fk.mean()), "score_shift": float(ss.mean()),
                     "score_abs_shift": float(np.abs(ss).mean()), "score_keep": float(p["score_keep"].mean())},
            n=len(b) + len(ss),
            robustness=f"Reversed rating scales keep the same top level {p['score_keep'].mean():.0%} of the time; the "
                       f"average absolute shift is {np.abs(ss).mean() * 100:.1f}% of the scale, with no direction.",
            chart={"type": "bars", "unit": "probability points", "rows": bars,
                   "note": f"first-slot boost {b.mean() * 100:+.2f}"},
            examples=seeded(p["ids2"], "order"), ids=p["ids2"] + p["score_ids"])
    return spec, run


def repeat_noise():
    spec = Spec(
        id="consistency_repeat_noise", family="consistency", title="Ask Jev the same thing twice",
        question="If the exact same request is sent twice, how much does Jev's answer change, and when does its top "
                 "answer flip?",
        why="Every comparison on this site rests on a noise floor. Jev returns probabilities, not a sampled answer, "
            "so the question is whether those probabilities are fixed or wobble, and whether a wobble can change "
            "what it would pick.",
        sourcing="Two-option questions whose reversed-order probe was sent twice as separate requests (answer.py "
                 "asks reversed, original, reversed). Enough: 214,000 pairs of identical requests.",
        scoring="The absolute change in the probability of the same option between the two identical requests; the "
                "share of pairs where the favored option changes, by how far the first answer was from 50/50.",
        chart="Flip rate by distance from 50/50 (0-2, 2-5, 5-10, 10-20, 20-50 points), with the mean change above "
              "each bar.",
        compared_with="Jev itself",
        limits="Probabilities come back rounded to whole points, so changes under one point are invisible. Two-option "
               "questions only.", sources=[])

    def run():
        s = pairs()["same"]
        d = np.abs(s[:, 0] - s[:, 1])
        flip = (s[:, 0] > 0.5) != (s[:, 1] > 0.5)
        m = np.abs(s[:, 0] - 0.5)
        cuts = [(0, 0.02, "0-2"), (0.02, 0.05, "2-5"), (0.05, 0.1, "5-10"), (0.1, 0.2, "10-20"), (0.2, 0.51, "20-50")]
        bins = [{"label": lab, "value": float(flip[(m >= a) & (m < b)].mean()), "change": float(d[(m >= a) & (m < b)].mean() * 100),
                 "n": int(((m >= a) & (m < b)).sum())} for a, b, lab in cuts]
        near = m < 0.1
        return Result(
            result=f"Sent the identical request twice, Jev's probability moves by {d.mean() * 100:.1f} points on "
                   f"average ({bins[0]['change']:.1f} near 50/50, under half a point near certainty), and the option it "
                   f"favors changes {flip.mean():.1%} of the time. {flip[near].sum() / max(flip.sum(), 1):.0%} of those "
                   f"flips happen within 10 points of a coin toss; beyond 20 points it essentially never flips "
                   f"({int(flip[m >= 0.2].sum())} of {int((m >= 0.2).sum()):,}).",
            evidence=f"{len(s):,} pairs of identical requests; 95th percentile change {np.percentile(d, 95) * 100:.0f} points, "
                     f"largest {d.max() * 100:.0f}",
            numbers={"mean_change": float(d.mean()), "flip": float(flip.mean()), "bins": bins, "p95": float(np.percentile(d, 95))},
            n=len(s),
            robustness="The same noise shows up between the base probe and the same-order shuffle probe "
                       f"({pairs()['base_same'].mean() * 100:.1f} points), which differ only in when they were sent.",
            chart={"type": "binned", "rows": bins, "x": "distance from 50/50 (points)", "y": "share where the favored option flips"},
            examples=seeded([i for i, f in zip(pairs()["ids2"], flip) if f], "noise"), ids=pairs()["ids2"])
    return spec, run


KINDS = {"taste": "how much it would enjoy something", "personality": "its own personality and habits",
         "evaluative": "judging text and things", "values": "values and ethics", "perception": "perceptions of words and things",
         "social": "how people behave and what they agree on"}


def middle_lean():
    spec = Spec(
        id="consistency_middle_lean", family="consistency", title="Jev picks the middle when asked what it likes",
        question="Jev's most likely answer on a rating scale is often the middle level. Is that a habit with every "
                 "scale, or does it depend on what is being rated?",
        why="The middle-lean is already known (it's in the old ledger, and people have a milder version); what isn't "
            "known is where it switches on. If it follows the subject rather than the scale, it's a stance, not a tic.",
        sourcing="Every rating question with an odd number of levels (3, 5 or 7), so a middle exists: 117,000 "
                 "questions, grouped by the kind of question the tree assigns (taste, personality, evaluative, values, "
                 "perception, social); for 14 sources, real people's answers to the same items.",
        scoring="Share of questions whose most likely level is the middle one, by kind, with 90% bootstrap intervals; "
                "on the items with human data, Jev's middle share next to the people's.",
        chart="Dots per kind (share at the middle), and paired bars for the sources with people's answers.",
        compared_with="Real respondents on 14 sources (captions, jokes, personality items, taste ratings, norms, "
                      "sound symbolism)",
        limits="Known pattern (old ledger `middle_lean`). Scales differ in wording across sources; five-level scales "
               "dominate. Kinds come from the tree and overlap sources.", sources=[])

    def run():
        rows = []
        for qid, jd, hum, kind, src in table().filter(pl.col("primitive") == "score").select(
                "id", "jev_dist", "humans", "kind", "source").iter_rows():
            d = json.loads(jd)
            k = len(d)
            if k < 3 or k % 2 == 0:
                continue
            mid = str(k // 2)
            h = biggest(hum)
            rows.append({"id": qid, "kind": kind, "k": k, "src": src, "mid": top(d) == mid,
                         "hmid": (top(h["dist"]) == mid) if h else None})
        t = pl.DataFrame(rows)
        by = []
        for kind, label in KINDS.items():
            g = t.filter(pl.col("kind") == kind)
            by.append({"kind": kind, "label": label, "mid": float(g["mid"].mean()), "n": g.height,
                       "ci": boot(g["mid"].cast(float).to_numpy(), b=200)})
        by.sort(key=lambda r: r["mid"])
        five = t.filter(pl.col("k") == 5).group_by("kind").agg(pl.col("mid").mean()).sort("mid").to_dicts()
        hs = t.filter(pl.col("hmid").is_not_null()).group_by("src").agg(pl.len().alias("n"), pl.col("mid").mean().alias("jev"),
                                                                         pl.col("hmid").mean().alias("people")) \
              .filter(pl.col("n") >= 60).sort("n", descending=True).to_dicts()
        g = {r["src"]: r for r in hs}
        k = {r["kind"]: r for r in by}
        cap, sc = g["caption_contest"], g["social_chem"]
        return Result(
            result=f"Jev's favorite rating is the middle one when the question is {KINDS['taste']} "
                   f"({k['taste']['mid']:.0%}) or about {KINDS['personality']} ({k['personality']['mid']:.0%}), and "
                   f"far less often for {KINDS['values']} ({k['values']['mid']:.0%}) or {KINDS['social']} "
                   f"({k['social']['mid']:.0%}). On New Yorker captions it picks the middle {cap['jev']:.0%} of the time "
                   f"where readers do {cap['people']:.0%}; on everyday rules {sc['jev']:.0%} where annotators do "
                   f"{sc['people']:.0%}.",
            evidence=f"{t.height:,} odd-length rating questions; {sum(r['n'] for r in hs):,} with people's answers",
            numbers={"overall": t["mid"].mean(), "kinds": by, "five_levels": five, "vs_people": hs}, n=t.height,
            robustness="Within five-level scales alone the order is the same: " + ", ".join(
                f"{r['kind']} {r['mid']:.0%}" for r in five if r["kind"]) + ".",
            chart={"type": "bars2", "labels": [r["src"] for r in hs], "a": [r["people"] for r in hs],
                   "b": [r["jev"] for r in hs], "a_label": "people", "b_label": "Jev",
                   "dots": [{"label": r["label"], "value": r["mid"], "ci": r["ci"]} for r in by]},
            examples=seeded(t.filter(pl.col("mid") & (pl.col("kind") == "taste"))["id"].to_list(), "middle"),
            ids=t["id"].to_list())
    return spec, run


def self_vs_people():
    spec = Spec(
        id="consistency_self_vs_people", family="consistency",
        title="Jev sees itself as calmer and less dark than most people",
        question="Every question about Jev was also asked as 'what would most people answer?'. Where do the two "
                 "answers part, and in which direction?",
        why="The gap between 'me' and 'most people' is the self-image. A model that says it's calmer, less petty and "
            "less swayed than the humans it learned from is telling you how it was shaped.",
        sourcing="All yes/no and rating questions in the Self hemisphere asked in both frames, except taste ratings "
                 "(their own experiment, taste_self_vs_guess). Enough: 60,000 yes/no and 90,000 rating questions.",
        scoring="Per topic, Jev's yes-rate for itself minus its yes-rate for most people (the share of questions "
                "where P(yes) > 0.5), with 90% bootstrap intervals over questions; for ratings, the mean level gap "
                "as a share of the scale. Topics with 300+ questions.",
        chart="Dots per topic, the gap in yes-rates with intervals, zero line; the largest gaps labeled.",
        compared_with="Jev's own guess of what most people would answer (not real people)",
        limits="Both answers are Jev's. 'Most people' is its guess, and the topics come from the tree.",
        sources=[])

    def run():
        t = table().filter((pl.col("hemisphere") == "self") & pl.col("people_dist").is_not_null() & ~pl.col("source").is_in(TASTE))
        py = lambda s: norm(json.loads(s)).get("true", 0.0)
        n = t.filter(pl.col("primitive") == "noul").with_columns(
            pl.col("jev_dist").map_elements(py, return_dtype=pl.Float64).alias("ys"),
            pl.col("people_dist").map_elements(py, return_dtype=pl.Float64).alias("yp"))
        topics = []
        for (l2,), g in n.group_by("l2"):
            if g.height < 300:
                continue
            d = (g["ys"] > 0.5).cast(float).to_numpy() - (g["yp"] > 0.5).cast(float).to_numpy()
            topics.append({"topic": _nice(l2), "self": float((g["ys"] > 0.5).mean()), "people": float((g["yp"] > 0.5).mean()),
                           "gap": float(d.mean()), "ci": boot(d, b=300), "n": g.height})
        topics.sort(key=lambda r: r["gap"])
        lvl = lambda s: (lambda d: level(d) / (len(d) - 1) if len(d) > 1 else None)(json.loads(s))
        sc = t.filter(pl.col("primitive") == "score").with_columns(
            pl.col("jev_dist").map_elements(lvl, return_dtype=pl.Float64).alias("ls"),
            pl.col("people_dist").map_elements(lvl, return_dtype=pl.Float64).alias("lp"))
        sgap = (sc["ls"] - sc["lp"]).drop_nulls().to_numpy()
        tk = {r["topic"]: r for r in topics}
        ds, em, mf = tk["dark side"], tk["emotions stress"], tk["moral foundations"]
        allgap = (n["ys"] > 0.5).cast(float).to_numpy() - (n["yp"] > 0.5).cast(float).to_numpy()
        return Result(
            result=f"Asked about itself, Jev says yes {(n['ys'] > 0.5).mean():.0%} of the time; asked what most people "
                   f"would say, {(n['yp'] > 0.5).mean():.0%}. The gaps mostly run one way: it admits a dark trait "
                   f"{ds['self']:.0%} of the time but expects people to {ds['people']:.0%}, owns up to stress and strong "
                   f"emotions {em['self']:.0%} vs {em['people']:.0%}, and agrees with moral rules of thumb {mf['self']:.0%} "
                   f"vs {mf['people']:.0%}. Of {len(topics)} topics, {sum(r['ci'][1] < 0 for r in topics)} lean this "
                   f"way and {sum(r['ci'][0] > 0 for r in topics)} the other ("
                   + ", ".join(r["topic"] for r in topics[::-1] if r["ci"][0] > 0) + ").",
            evidence=f"{n.height:,} yes/no questions (90% interval on the overall gap {boot(allgap, b=300)}); "
                     f"{len(sgap):,} rating questions",
            numbers={"topics": topics, "score_gap": float(sgap.mean()), "yes_self": float((n["ys"] > 0.5).mean()),
                     "yes_people": float((n["yp"] > 0.5).mean())}, n=n.height + len(sgap),
            robustness=f"On rating questions it also places itself lower than most people, by {-sgap.mean() * 100:.1f}% "
                       f"of the scale on average (interval {[round(-x * 100, 1) for x in boot(sgap, b=300)][::-1]}).",
            chart={"type": "dots", "rows": [{"label": r["topic"], "value": r["gap"], "ci": r["ci"]} for r in topics], "zero": 0},
            examples=seeded(n.filter((pl.col("ys") < 0.5) & (pl.col("yp") > 0.5) & pl.col("l2").str.contains("dark_side|emotions"))["id"].to_list(), "svp"),
            ids=n["id"].to_list() + sc.filter(pl.col("ls").is_not_null() & pl.col("lp").is_not_null())["id"].to_list())
    return spec, run


EXPERIMENTS = [option_order(), repeat_noise(), middle_lean(), self_vs_people()]
