"""Reading people from their words (round 4): whether Jev reads a writer's own emotion and appraisals or other
readers' guesses (crowd-enVent), and how polite a request sounds (Stanford Politeness Corpus)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, clip, js, level, norm, seeded, top, with_meta


def robust_choice(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-option probes (same keys)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def robust_level(r: dict) -> float:
    """Expected level averaged over the question as asked and with the levels reversed (stored in the original order)."""
    base = level(js(r["jev_dist"]))
    rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "reversed_levels" and v.get("dist")), None)
    return (base + rev) / 2 if rev is not None else base


ENVENT_LIMITS = ("Writers were Prolific workers in the UK and US writing about their own lives in 2021; readers saw the "
                 "text with the emotion words hidden, as Jev does. Five readers per text, so a reader majority can be 3 of 5.")


# ---- 1. writer vs readers: emotions ------------------------------------------------------------------------------------
def writer_vs_readers():
    spec = Spec(
        id="reading_writer_vs_readers", family="reading", title="Does Jev read the writer, or the other readers?",
        question="When someone describes an event from their life, does Jev name the emotion they actually felt, or the one "
                 "other readers guess, and how often do those differ?",
        why="Most emotion datasets label a text by what readers see in it. crowd-enVent also has the writer's own answer, "
            "so it can tell reading the page apart from reading the person; a model trained on text might be a very good "
            "reader and still miss the writer.",
        sourcing="New questions (sources/crowd_envent): 'Someone wrote <story> about an event in their own life. Which "
                 "emotion did the writer feel?' with the study's 13 options (anger ... trust, and no particular emotion), "
                 "for 598 of the 1,200 texts that 5 readers also judged, about 46 per writer emotion; the emotion words "
                 "are hidden as they were for the readers.",
        collection="598 new questions, each asked as written, for 'most people', and with the options in three shuffled "
                   "orders (averaged).",
        scoring="Share where Jev's top emotion is the writer's, and where it is the readers' majority; the same for the "
                "readers' majority and for an average single reader against the writer; on texts where the readers' "
                "majority and the writer differ, whom Jev sides with; hit rate per writer emotion, 90% bootstrap intervals.",
        chart="Paired bars per writer emotion: how often the readers' majority names it, and how often Jev does.",
        compared_with="the writers' own emotion, and 5 readers per text (crowd-enVent, Troiano et al. 2023)",
        limits=ENVENT_LIMITS, new_questions=598, sources=["crowd_envent"])

    def run():
        rows = []
        for r in with_meta("crowd_envent"):
            if r["m"].get("set") != "emotion":
                continue
            h = norm(biggest(r["humans"])["dist"])
            j = robust_choice(r)
            w = r["m"]["writer_emotion"].replace("-", "_")
            maj = top(h)
            rows.append({"id": r["id"], "writer": w, "jev": top(j), "maj": maj, "maj_share": h[maj],
                         "reader_hit": h.get(w, 0.0), "jev_p_writer": j.get(w, 0.0)})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") == pl.col("writer")).alias("jev_w"),
                                            (pl.col("jev") == pl.col("maj")).alias("jev_m"),
                                            (pl.col("maj") == pl.col("writer")).alias("maj_w"))
        jw, jm, mw = float(t["jev_w"].mean()), float(t["jev_m"].mean()), float(t["maj_w"].mean())
        one = float(t["reader_hit"].mean())
        split = t.filter(~pl.col("maj_w"))
        side_w, side_m = float((split["jev"] == split["writer"]).mean()), float((split["jev"] == split["maj"]).mean())
        by = t.group_by("writer").agg(pl.col("jev_w").mean().alias("jev"), pl.col("maj_w").mean().alias("readers"),
                                      pl.len()).sort("writer").to_dicts()
        worst = sorted(by, key=lambda b: b["jev"] - b["readers"])[:3]
        ne = next(b for b in by if b["writer"] == "no_emotion")
        f = lambda b: f"{b['writer'].replace('_', ' ')} ({b['jev']:.0%} vs {b['readers']:.0%})"  # noqa: E731
        return Result(
            result=f"Jev names the emotion the writer actually felt for {jw:.0%} of {t.height} life events, about as often as "
                   f"the majority of five other readers ({mw:.0%}) and more than a single reader ({one:.0%}). The difference is "
                   f"'no particular emotion': when the writer felt nothing much, Jev says so for {ne['jev']:.0%} of the texts "
                   f"and the readers' majority for {ne['readers']:.0%}. It trails the readers most on "
                   f"{and_list([f(b) for b in worst])} (Jev vs readers' majority).",
            evidence=f"{t.height} of 598 texts (the screen hid {598 - t.height}), 5 readers each; 90% interval on Jev naming "
                     f"the writer's emotion {boot(t['jev_w'].cast(float).to_numpy())}. Where readers and writer part ways "
                     f"({split.height} texts), Jev sides with the writer {side_w:.0%} and the readers {side_m:.0%}",
            numbers={"jev_writer": jw, "jev_majority": jm, "majority_writer": mw, "one_reader": one, "split_n": split.height,
                     "split_side_writer": side_w, "split_side_readers": side_m, "by_emotion": by}, n=t.height,
            chart={"type": "bars2", "labels": [b["writer"].replace("_", " ") for b in by], "a": [b["readers"] for b in by],
                   "b": [b["jev"] for b in by], "a_label": "readers' majority names the writer's emotion",
                   "b_label": "Jev names it"},
            robustness="Jev's answer is averaged over the options in the order written and three shuffled orders.",
            examples=seeded(split["id"].to_list(), "envent"))
    return spec, run


# ---- 2. writer vs readers: appraisals ------------------------------------------------------------------------------------
APP_LABEL = {"pleasantness": "how pleasant it was", "suddenness": "how sudden it was",
             "self_responsblt": "how responsible the writer was", "other_responsblt": "how responsible someone else was"}


def appraisals():
    spec = Spec(
        id="reading_event_appraisals", family="reading", title="How an event felt to the person who lived it",
        question="From someone's account of an event in their life, how well does Jev judge how pleasant and sudden it "
                 "was and who was responsible, compared with the writer's own ratings and with other readers'?",
        why="Appraisal theory says emotions come from how we judge events (was it my fault? did it come out of the "
            "blue?). Whether a model infers those judgments like the person who lived them, or like an outside reader, "
            "says what it is modeling when it reads about people.",
        sourcing="New questions (sources/crowd_envent): for 150 of the texts, four of the study's appraisal questions "
                 "(pleasantness, suddenness, the writer's own responsibility, someone else's), each on the study's 1 'not "
                 "at all' to 5 'extremely' scale.",
        collection="600 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Per appraisal, rank correlation with the writer's own rating for Jev (expected level, base and reversed "
                "averaged) and for the readers' mean; the mean gap from the writer's rating (does Jev assume more "
                "responsibility, less pleasantness?), with 90% bootstrap intervals over texts.",
        chart="Dots per appraisal: rank correlation with the writer, Jev vs readers.",
        compared_with="the writers' own appraisal ratings, and 5 readers per text",
        limits=ENVENT_LIMITS + " The level labels paraphrase the study's 1-5 scale.", new_questions=600,
        sources=["crowd_envent"])

    def run():
        rows = []
        for r in with_meta("crowd_envent"):
            if r["m"].get("set") != "appraisal":
                continue
            rows.append({"id": r["id"], "app": r["m"]["appraisal"], "writer": float(r["m"]["writer_level"]),
                         "jev": robust_level(r), "readers": level(biggest(r["humans"])["dist"])})
        t = pl.DataFrame(rows).sort("app", "id")
        out = []
        for a in APP_LABEL:
            g = t.filter(pl.col("app") == a)
            if g.height < 20:
                continue
            gap = (g["jev"] - g["writer"]).to_numpy()
            out.append({"app": a, "label": APP_LABEL[a], "n": g.height,
                        "rho_jev": float(spearmanr(g["jev"], g["writer"]).statistic),
                        "rho_readers": float(spearmanr(g["readers"], g["writer"]).statistic),
                        "gap_jev": float(gap.mean()), "gap_readers": float((g["readers"] - g["writer"]).mean()),
                        "ci": boot(gap)})
        short = {"pleasantness": "pleasant", "suddenness": "sudden", "self_responsblt": "the writer's fault",
                 "other_responsblt": "someone else's fault"}
        for o in out:
            o["short"] = short[o["app"]]
        leans = [o for o in out if not (o["ci"][0] <= 0 <= o["ci"][1])] or [max(out, key=lambda o: abs(o["gap_jev"]))]
        return Result(
            result="Jev reads how an event felt about as well as other readers do (rank correlation with the writer's own "
                   "rating: " + and_list([f"{o['label']} {o['rho_jev']:.2f} vs {o['rho_readers']:.2f}" for o in out])
                   + ", Jev vs readers). But it rates them lower than the writers themselves: "
                   + and_list([f"{abs(o['gap_jev']):.2f} levels {'less' if o['gap_jev'] < 0 else 'more'} {o['short']}"
                               for o in leans])
                   + " than the writers did on a 0-4 scale, where the readers are within "
                   + f"{max(abs(o['gap_readers']) for o in leans):.2f}.",
            evidence=f"{t['id'].n_unique()} of 600 questions (the screen hid {600 - t['id'].n_unique()}); 90% intervals on "
                     "Jev's mean gap from the writer: "
                     + "; ".join(f"{o['app'].replace('_', ' ')} {o['ci']}" for o in out),
            numbers={"appraisals": out}, n=t.height,
            chart={"type": "dots", "domain": [0, 1], "fmt": "num", "rows": [{"label": o["label"], "value": o["rho_jev"], "people": o["rho_readers"],
                                                               "right": f"{o['gap_jev']:+.2f}"} for o in out]},
            examples=seeded(t["id"].to_list(), "appraisal"))
    return spec, run


# ---- 3. politeness -------------------------------------------------------------------------------------------------------
def politeness():
    spec = Spec(
        id="reading_politeness", family="reading", title="How polite does a Wikipedia request sound to Jev?",
        question="Reading requests Wikipedia editors wrote to each other, does Jev hear the same politeness as crowd "
                 "raters, and where does its ear differ?",
        why="Tone is most of what people react to in a message. The Stanford Politeness Corpus is the standard record of "
            "what makes a request sound polite (please, hedges, gratitude) or rude (direct questions, 'you'); a model "
            "that writes and rewrites messages all day should hear it like people do.",
        sourcing="New questions (sources/politeness): 'One Wikipedia editor wrote <request> to another editor on their "
                 "talk page. How polite is it?' on five described levels, for 500 of the 4,353 rated requests, 100 from "
                 "each fifth of the corpus's politeness score; 5 MTurk raters per request on the study's 1-25 scale, "
                 "binned into the same five levels.",
        collection="500 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Rank correlation between Jev's expected level (base and reversed averaged) and the raters' mean score, "
                "with a 90% bootstrap interval, next to how well one rater agrees with the other four (the ceiling); "
                "Jev's spread and mean against the raters'; the requests it hears most differently.",
        chart="A scatter: raters' mean score (x) vs Jev's level (y), with the largest disagreements labeled.",
        compared_with="5 MTurk raters per request (Danescu-Niculescu-Mizil et al. 2013)",
        limits="Raters were US MTurk workers in 2012; requests come from Wikipedia editors' talk pages, a particular "
               "register. Jev's level descriptions were written for this project, anchored on the study's ends.",
        new_questions=500, sources=["politeness"])

    def run():
        rows = []
        for r in with_meta("politeness"):
            st = js(r["state"]) if isinstance(r["state"], str) else r["state"]
            sc = r["m"].get("scores") or []
            rows.append({"id": r["id"], "req": (st or {}).get("request", ""), "jev": robust_level(r),
                         "people": float(r["m"]["mean_score"]), "people_lvl": level(biggest(r["humans"])["dist"]),
                         "one": sc[0] if sc else None, "rest": float(np.mean(sc[1:])) if len(sc) > 1 else None})
        t = pl.DataFrame(rows).sort("id")
        rho = spearmanr(t["jev"], t["people"]).statistic
        idx = np.arange(t.height)
        ci = boot(idx, stat=lambda ii: spearmanr(t["jev"].to_numpy()[ii.astype(int)], t["people"].to_numpy()[ii.astype(int)]).statistic, b=300)
        # the ceiling: the first rater listed against the mean of the other four, across requests
        c = t.drop_nulls(["one", "rest"])
        ceiling = float(spearmanr(c["one"], c["rest"]).statistic) if c.height > 20 else None
        t = t.with_columns((pl.col("jev").rank() / t.height - pl.col("people").rank() / t.height).alias("d"))
        warm, cold = t.sort("d", descending=True).head(3).to_dicts(), t.sort("d").head(3).to_dicts()
        sd_j, sd_p = float(t["jev"].std()), float(t["people_lvl"].std())
        m_j, m_p = float(t["jev"].mean()), float(t["people_lvl"].mean())
        q = lambda r: f"\"{clip(r['req'], 70)}\""  # noqa: E731
        return Result(
            result=f"Jev hears politeness {agree_word(rho)} like the raters (rank correlation {rho:.2f} over {t.height} "
                   f"requests), better than a single rater matches the other four ({ceiling:.2f}). On a 0-4 scale it averages {m_j:.2f} where the raters average {m_p:.2f}, and its readings "
                   f"spread {'more' if sd_j > sd_p else 'less'} ({sd_j:.2f} vs {sd_p:.2f}). It hears {q(warm[0])} as far "
                   f"politer than they did, and {q(cold[0])} as far ruder.",
            evidence=f"{t.height} of 500 requests (the screen hid {500 - t.height}), 5 raters each; 90% interval on the rank "
                     f"correlation {ci[0]:.2f} to {ci[1]:.2f}. Jev is compared with the mean of five raters, the single rater "
                     "with the mean of four, so the two numbers are not strictly like for like",
            numbers={"rho": rho, "ci90": ci, "one_rater_vs_rest": ceiling, "mean_jev": m_j, "mean_people": m_p, "sd_jev": sd_j, "sd_people": sd_p,
                     "warmer": [{k: v for k, v in x.items() if k != 'd'} for x in warm],
                     "colder": [{k: v for k, v in x.items() if k != 'd'} for x in cold]}, n=t.height,
            chart={"type": "scatter", "points": t.select("people", "jev").to_numpy().round(2).tolist(),
                   "labels": [{"label": clip(x["req"], 28), "x": x["people"], "y": x["jev"]} for x in warm[:2] + cold[:2]],
                   "x": "raters' mean score (1-25)", "y": "Jev's level (0-4)"},
            robustness="Jev's level is averaged over the levels as written and reversed.",
            examples=[warm[0]["id"], cold[0]["id"]])
    return spec, run


EXPERIMENTS = [writer_vs_readers(), appraisals(), politeness()]
