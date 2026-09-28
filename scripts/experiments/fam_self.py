"""Self experiments: what Jev does when there is no right answer. Where it is torn and where it is sure about
itself, how it leans on the yes/no questions real people post online, and whether it plays along with whimsy."""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from lib import Result, Spec, boot, norm, seeded, table

CLOSED = ["stackexchange_closed", "quora_closed", "yahoo_closed", "wildchat_closed"]


def _nice(l2: str) -> str:
    return l2.split(".")[-1].replace("_", " ")


def _yes(s: str) -> float:
    return norm(json.loads(s)).get("true", 0.0)


def torn_vs_sure():
    spec = Spec(
        id="self_torn_vs_sure", family="self", title="Jev is surest about how to behave, least sure about what it likes",
        question="Asked about itself with no right answer, on which topics does Jev commit to an answer and on which "
                 "does it hedge?",
        why="A model's confidence where nothing is at stake shows what it has settled views on. People are usually "
            "surest about their tastes and least sure about ethics; a model might be the reverse.",
        sourcing="The questions written for this project about Jev itself (the g5_* banks in the Self hemisphere: "
                 "personality, lifestyle, love, mind, values), yes/no and pick-one only: 102,000 questions in 42 "
                 "topics with 500+ each. Datasets with a right answer are left out.",
        scoring="Confidence = how far Jev's top probability is above an even split, scaled so 0 is a coin toss (1/k) "
                "and 1 is certain; per topic, the mean with a 90% bootstrap interval, and the share of 'torn' answers "
                "(confidence under 0.2). The same measure for Jev's answer on behalf of most people.",
        chart="Dots per topic sorted by confidence, from torn to sure, with Jev's confidence about most people as a "
              "second, hollow dot.",
        compared_with="Jev's confidence when answering for most people (its guess, not real people)",
        limits="Topics are the tree's; question wording varies by bank. Confidence here is Jev's probability, not a "
               "measure of whether it is right.", sources=[])

    def run():
        t = table().filter((pl.col("hemisphere") == "self") & pl.col("primitive").is_in(["noul", "choice"])
                           & pl.col("source").str.starts_with("g5_"))
        t = t.with_columns(pl.col("jev_dist").map_elements(lambda s: len(json.loads(s)), return_dtype=pl.Int64).alias("k"))
        t = t.with_columns(((pl.col("p_top") - 1 / pl.col("k")) / (1 - 1 / pl.col("k"))).alias("conf"),
                           ((pl.col("p_top_h") - 1 / pl.col("k")) / (1 - 1 / pl.col("k"))).alias("confh"))
        rows, used = [], []
        for (l2,), g in t.group_by("l2"):
            if g.height < 500 or l2.count(".") < 2:
                continue
            used += g["id"].to_list()
            c = g["conf"].to_numpy()
            rows.append({"topic": _nice(l2), "conf": float(c.mean()), "ci": boot(c, b=200), "torn": float((c < 0.2).mean()),
                         "people": float(g["confh"].mean()), "n": g.height})
        rows.sort(key=lambda r: r["conf"])
        by_torn = sorted(rows, key=lambda r: r["torn"])
        lo, hi = by_torn[-3:][::-1], by_torn[:3]
        name = lambda rs: ", ".join(f"{r['topic']} {r['torn']:.0%}" for r in rs)
        more_sure_people = [r for r in rows if r["people"] - r["conf"] >= 0.04]
        more_sure_self = [r for r in rows if r["conf"] - r["people"] >= 0.04]
        return Result(
            result=f"Jev is closest to a coin toss on questions about what it likes and what it's like (torn on "
                   f"{name(lo)} of questions) and most decided on questions about conduct ({name(hi)}). On tastes it is "
                   f"surer answering for most people than for itself; only on {' and '.join(r['topic'] for r in more_sure_self)} "
                   f"is it surer about itself.",
            evidence=f"{t.height:,} questions in {len(rows)} topics; overall confidence {t['conf'].mean():.2f}",
            numbers={"topics": rows}, n=t.height,
            robustness=f"Surer for most people than for itself (by 0.04+ on the 0-1 scale) on {len(more_sure_people)} topics, "
                       f"most on {', '.join(r['topic'] for r in sorted(more_sure_people, key=lambda r: r['conf'] - r['people'])[:3])}. "
                       "Torn = confidence under 0.2, where 0 is a coin toss and 1 is certain.",
            chart={"type": "dots", "rows": [{"label": r["topic"], "value": r["conf"], "ci": r["ci"], "people": r["people"]} for r in rows],
                   "domain": [0, 1]},
            examples=seeded(t.filter(pl.col("conf") < 0.05)["id"].to_list(), "torn") + seeded(t.filter(pl.col("conf") > 0.95)["id"].to_list(), "sure", 2),
            ids=used)
    return spec, run


def closed_questions():
    spec = Spec(
        id="self_closed_questions", family="self", title="Can? Yes. Will? No. How Jev leans on real people's questions",
        question="On 80,000 yes/no questions people actually posted online (Stack Exchange, Quora, Yahoo Answers, "
                 "chatbot logs), does Jev lean yes or no, and does the way a question starts decide it?",
        why="These questions have no answer key, so Jev's lean is a default, not knowledge. If the first word of a "
            "question predicts its answer, that's a habit worth knowing before trusting its yes or no.",
        sourcing="Existing closed questions from four public Q&A sources, asked as yes/no. Enough: 79,700 questions; "
                 "first words with 300+ questions.",
        scoring="Share where P(yes) > 0.5, overall, by source and by the question's first word, with 90% bootstrap "
                "intervals; the share within 10 points of 50/50.",
        chart="Dots per first word (Can, Have, Has, ... Will, Was), yes-share with intervals, line at 50%.",
        compared_with="Nothing outside the model: no answer key exists for these questions",
        limits="A question's first word travels with its subject (Will... is about the future, Can... often about "
               "what's possible), so this shows a pattern, not its cause.", sources=CLOSED)

    def run():
        c = table().filter(pl.col("source").is_in(CLOSED) & (pl.col("primitive") == "noul")).with_columns(
            pl.col("jev_dist").map_elements(_yes, return_dtype=pl.Float64).alias("y"),
            pl.col("text").str.extract(r"^(\w+)", 1).str.to_titlecase().alias("stem"))
        rows = []
        for (stem,), g in c.group_by("stem"):
            if g.height < 300:
                continue
            y = (g["y"] > 0.5).cast(float).to_numpy()
            rows.append({"stem": stem, "yes": float(y.mean()), "ci": boot(y, b=200), "n": g.height})
        rows.sort(key=lambda r: r["yes"])
        s = {r["stem"]: r for r in rows}
        src = c.group_by("source").agg(pl.len().alias("n"), (pl.col("y") > 0.5).mean().alias("yes")).sort("yes").to_dicts()
        return Result(
            result=f"On {c.height:,} yes/no questions people posted online, Jev says yes to {(c['y'] > 0.5).mean():.0%}, "
                   f"but the first word tilts it: {s['Can']['yes']:.0%} yes for 'Can...?', {s['Have']['yes']:.0%} for "
                   f"'Have...?', and {s['Will']['yes']:.0%} for 'Will...?', {s['Was']['yes']:.0%} for 'Was...?'. It stays "
                   f"within 10 points of a coin toss on {((c['y'] - 0.5).abs() < 0.1).mean():.0%} of them.",
            evidence=f"{c.height:,} questions from {len(CLOSED)} sources; {len(rows)} first words with 300+ questions",
            numbers={"stems": rows, "sources": src, "yes": float((c["y"] > 0.5).mean())}, n=c.height,
            robustness="By source the yes-share runs from " + ", ".join(f"{r['source'].split('_')[0]} {r['yes']:.0%}" for r in src) + ".",
            chart={"type": "dots", "rows": [{"label": r["stem"], "value": r["yes"], "ci": r["ci"]} for r in rows], "zero": 0.5,
                   "domain": [0, 1]},
            examples=seeded(c.filter(pl.col("stem") == "Will")["id"].to_list(), "will", 2) + seeded(c.filter(pl.col("stem") == "Can")["id"].to_list(), "can", 2),
            ids=c["id"].to_list())
    return spec, run


def shower_thoughts():
    spec = Spec(
        id="self_shower_thoughts", family="self", title="Does a guitar get jealous? Jev mostly doesn't play along",
        question="Asked whimsical yes/no questions ('Does 9 feel left out because it's always almost 10?'), does Jev "
                 "answer the joke or the literal question?",
        why="Literal reading is a limit TypeSafe documents (docs/01-jev.md §6, item 1). This measures it on questions "
            "whose only sensible answer is playful, and shows where the line falls.",
        sourcing="The shower-thoughts bank written for this project (World > Society): 576 yes/no questions that "
                 "personify objects or pose silly hypotheticals. Enough for a rate; small for subtopics.",
        scoring="Share where P(yes) > 0.5; share torn (within 10 points of 50/50); the most and least playful answers.",
        chart="A histogram of P(yes) across the 576 questions, with a few questions labeled at each end.",
        compared_with="Nothing outside the model",
        limits="Known limit (literal reading, §6). The questions were written for this project; 'playing along' "
               "and 'yes' are the same thing only for questions phrased so a playful answer is yes.",
        sources=["g5_w12_shower_thoughts"])

    def run():
        n = table().filter((pl.col("source") == "g5_w12_shower_thoughts") & (pl.col("primitive") == "noul")).with_columns(
            pl.col("jev_dist").map_elements(_yes, return_dtype=pl.Float64).alias("y")).sort("y")
        y = n["y"].to_numpy()
        hist = [{"label": f"{a / 10:.1f}", "value": float(((y >= a / 10) & (y < (a + 1) / 10 + (a == 9))).mean())} for a in range(10)]
        low, high = n.head(3).to_dicts(), n.tail(3).reverse().to_dicts()
        # hand-picked from the two ends of the list; the question ids are in `examples`
        pick = lambda text: n.filter(pl.col("text") == text).row(0, named=True)
        sundial, eraser = pick("Would a sundial feel useless on a cloudy day?"), pick("Does an eraser feel guilty about the mistakes it erases?")
        return Result(
            result=f"Jev answers yes to {(y > 0.5).mean():.0%} of whimsical questions and is torn on "
                   f"{(np.abs(y - 0.5) < 0.1).mean():.0%}. Its yeses tend to go to lines that also work as plain "
                   f"description (a sundial would 'feel useless' on a cloudy day, {sundial['y']:.2f}); it denies objects "
                   f"moral feelings (an eraser feeling guilty, {eraser['y']:.2f}). Examples hand-picked.",
            evidence=f"{len(y)} questions; 90% interval on the yes-share {boot((y > 0.5).astype(float), b=300)}",
            numbers={"yes": float((y > 0.5).mean()), "hist": hist, "low": low, "high": high}, n=len(y),
            chart={"type": "binned", "rows": hist, "x": "P(yes)", "y": "share of questions",
                   "labels": [{"label": r["text"], "x": r["y"]} for r in low[:2] + high[:2]]},
            examples=[sundial["id"], eraser["id"], low[0]["id"], high[0]["id"]],
            ids=n["id"].to_list())
    return spec, run


EXPERIMENTS = [torn_vs_sure(), closed_questions(), shower_thoughts()]
