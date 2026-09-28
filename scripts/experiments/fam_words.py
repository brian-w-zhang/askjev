"""Word experiments: what Jev knows about how words feel, sound and are sensed, against published word norms.

The Glasgow, Lancaster and Brysbaert norms store the human mean in `meta` (no per-rater distribution); Winter et al.'s
iconicity ratings and the pseudoword shape ratings carry rater distributions in `humans`. Jev's number is its robust
level: the question as asked, averaged with the same question with the levels reversed (fam_taste).
"""

from __future__ import annotations

import json
import re

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, biggest, boot, js, level, norm, seeded, source, top


def robust(r: dict) -> float:
    base = level(js(r["jev_dist"]))
    rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v["kind"] == "reversed_levels"), None)
    return (base + rev) / 2 if rev is not None else base


def word(text: str) -> str:
    return re.search(r'"(.+?)"', text).group(1)


def rho_ci(a, b, reps: int = 300) -> list[float]:
    a, b = np.asarray(a), np.asarray(b)
    return boot(np.arange(len(a)), stat=lambda ii: spearmanr(a[ii.astype(int)], b[ii.astype(int)]).statistic, b=reps)


GLASGOW = {"pleasant": "Pleasantness (valence)", "calming": "Excitement (arousal)", "age": "Age of learning",
           "familiar": "Familiarity", "big": "Size", "mental picture": "Imageability"}


def glasgow() -> pl.DataFrame:
    rows = []
    for r in source("glasgow_norms").iter_rows(named=True):
        dim = next((k for k in GLASGOW if k in r["text"]), None)
        m = js(r["meta"]) or {}
        if dim and "mean" in m:
            rows.append({"id": r["id"], "w": word(r["text"]), "sense": "(in the sense" in r["text"], "dim": dim,
                         "jev": robust(r), "h": m["mean"]})
    return pl.DataFrame(rows)


def word_norms():
    spec = Spec(
        id="words_norms", family="words", title="Jev knows how pleasant a word is, not how exciting",
        question="Rating thousands of English words on the dimensions psycholinguists norm (pleasantness, excitement, "
                 "age of learning, familiarity, size, imageability, concreteness), where does Jev agree with people?",
        why="Word norms are how psychology measures what words mean to people beyond their definitions. A model "
            "learns words only from text, so the dimensions it gets right and wrong show what text does and doesn't "
            "carry.",
        sourcing="Existing rating questions built from the Glasgow Norms (Scott et al. 2019, 5,553 words rated on 1-9 "
                 "or 1-7 scales) and the Brysbaert et al. 2014 concreteness ratings (1-5), with each word's human mean. "
                 "Enough: about 1,000-2,000 words per dimension, 11,857 ratings.",
        scoring="Per dimension, rank correlation between Jev's robust level and the human mean, with a 90% bootstrap "
                "interval over words. Ranks because Jev's five described levels and the norms' numeric scales differ.",
        chart="Dots with intervals, one row per dimension, sorted by agreement.",
        compared_with="Glasgow Norms raters (UK students, about 30 per word per scale); Brysbaert et al. 2014 raters (US, MTurk)",
        limits="Jev's scales use described levels written for this project ('Calming: it feels sleepy or soothing'), "
               "not the norms' numbered anchors, so part of any gap is wording. Human means only; no per-rater spread.",
        sources=["glasgow_norms", "concreteness"])

    def run():
        t = glasgow()
        rows = []
        for dim, label in GLASGOW.items():
            g = t.filter(pl.col("dim") == dim)
            rows.append({"label": label, "value": float(spearmanr(g["jev"], g["h"]).statistic),
                         "ci": rho_ci(g["jev"], g["h"]), "n": g.height})
        c = pl.DataFrame([{"jev": robust(r), "h": js(r["meta"])["mean_1_5"]} for r in source("concreteness").iter_rows(named=True)])
        rows.append({"label": "Concreteness", "value": float(spearmanr(c["jev"], c["h"]).statistic),
                     "ci": rho_ci(c["jev"], c["h"]), "n": c.height})
        rows.sort(key=lambda r: r["value"])
        lo = rows[0]
        best, good = rows[::-1][:3], [r for r in rows[::-1][3:] if r["value"] >= 0.6]
        name = lambda r: r["label"].split(" (")[0].lower()
        best_rhos = ", ".join(f"{r['value']:.2f}" for r in best)
        return Result(
            result=f"Jev orders words by {name(best[0])}, {name(best[1])} and {name(best[2])} almost as people do "
                   f"(rank correlations {best_rhos}), and by " + ", ".join(name(r) for r in good[:-1])
                   + " and " + name(good[-1])
                   + f" fairly well, but it tracks how exciting a word is only loosely ({lo['value']:.2f}); "
                   f"words_arousal_is_mood shows why.",
            evidence="; ".join(f"{r['label']} {r['value']:.2f} ({r['n']:,} words, 90% interval {r['ci'][0]:.2f} to "
                               f"{r['ci'][1]:.2f})" for r in rows[::-1]),
            numbers={"dimensions": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "domain": [0, 1],
                   "rows": [{"label": r["label"], "value": r["value"], "ci": r["ci"]} for r in rows]},
            examples=seeded(t.filter(pl.col("dim") == "calming")["id"].to_list(), "norms"))
    return spec, run


def arousal():
    spec = Spec(
        id="words_arousal_is_mood", family="words", title="To Jev, a stirring word is an unpleasant one",
        question="When Jev rates how calming or stirring a word feels, is it rating excitement, as people do, or "
                 "just how pleasant the word is?",
        why="Psychologists separate valence (pleasant or not) from arousal (calm or exciting): 'cuddle' is pleasant "
            "and exciting, 'boredom' is unpleasant and calm. Mixing them up is a specific, checkable gap in how a "
            "model represents feeling.",
        sourcing="Existing Glasgow Norms questions for the words rated on both pleasantness and calming/stirring "
                 "(the same word, both questions, one sense). Enough: 468 words with both, and 1,457 arousal ratings "
                 "overall.",
        scoring="Rank correlations among four numbers per word: Jev's and people's arousal, Jev's and people's "
                "valence. The telling pair: Jev's arousal against people's valence. The words with the largest gap "
                "between Jev's arousal and people's, each way, placed on the same 1-9 scale.",
        chart="A scatter of people's arousal (x) against Jev's (y), colored by people's pleasantness, with the "
              "largest misses labeled.",
        compared_with="Glasgow Norms raters (Scott et al. 2019)",
        limits="Jev's arousal levels are described with examples ('Calming: it feels sleepy or soothing, like a quiet "
               "evening'), which may pull pleasant words toward the calm end. Mapping Jev's five levels onto 1-9 is "
               "linear and approximate.", sources=["glasgow_norms"])

    def run():
        t = glasgow().filter(~pl.col("sense"))
        w = t.filter(pl.col("dim").is_in(["calming", "pleasant"])).pivot(on="dim", index="w", values=["jev", "h"],
                                                                           aggregate_function="first").drop_nulls()
        r = lambda a, b: float(spearmanr(w[a], w[b]).statistic)
        m = {"jev_ar_vs_h_ar": r("jev_calming", "h_calming"), "jev_ar_vs_h_va": r("jev_calming", "h_pleasant"),
             "h_ar_vs_h_va": r("h_calming", "h_pleasant"), "jev_ar_vs_jev_va": r("jev_calming", "jev_pleasant")}
        a = t.filter(pl.col("dim") == "calming").with_columns((pl.col("jev") / 4 * 8 + 1).alias("j9"))
        a = a.with_columns((pl.col("j9") - pl.col("h")).alias("gap"))
        calm = a.sort("gap").head(6).to_dicts()
        stir = a.sort("gap", descending=True).head(6).to_dicts()
        return Result(
            result=f"For Jev, a stirring word is mostly an unpleasant one: its excitement ratings follow people's "
                   f"pleasantness ratings in reverse (rank correlation {m['jev_ar_vs_h_va']:.2f}) about as much as "
                   f"people's own excitement ratings ({m['jev_ar_vs_h_ar']:.2f}), while for people pleasant words "
                   f"lean exciting ({m['h_ar_vs_h_va']:+.2f}). So it calls '{calm[0]['w']}' and '{calm[1]['w']}' calming "
                   f"(people: stirring) and '{stir[0]['w']}' and '{stir[1]['w']}' intensely stirring (people: middling).",
            evidence=f"{w.height} words rated on both scales; {a.height:,} arousal ratings for the gap lists",
            numbers={**m, "calm_misses": calm, "stir_misses": stir, "n_both": w.height},
            chart={"type": "scatter", "points": w.select("h_calming", "jev_calming").to_numpy().round(3).tolist(),
                   "color": w["h_pleasant"].round(2).to_list(), "color_label": "people's pleasantness (1-9)",
                   "x": "people's arousal (1-9)", "y": "Jev's arousal level (0-4)",
                   "labels": [{"label": x["w"], "x": x["h"], "y": x["jev"]} for x in calm[:3] + stir[:3]]},
            examples=[calm[0]["id"], stir[0]["id"]], n=w.height,
            # the questions behind the result: both scales for the words rated on both, and every arousal question
            ids=t.filter(((pl.col("dim") == "pleasant") & pl.col("w").is_in(w["w"].to_list())) | (pl.col("dim") == "calming"))["id"].to_list())
    return spec, run


SENSES = {"seeing": "Sight", "hearing": "Hearing", "feeling through touch": "Touch", "tasting": "Taste",
          "smelling": "Smell"}


def senses():
    spec = Spec(
        id="words_senses", family="words", title="Jev hears and smells words like people but underrates seeing them",
        question="Asked how much it experiences each word through sight, hearing, touch, taste and smell, does Jev "
                 "give the sensory profile people give?",
        why="The Lancaster Sensorimotor Norms record how people experience 40,000 words through each sense. A model "
            "has no senses; which sense it misjudges most says something about what text leaves out.",
        sourcing="Existing Lancaster questions ('How much do you experience \"<word>\" by <sense>?', five described "
                 "levels), about 1,980 words per sense, each with the human mean on the norms' 0-5 scale; plus 1,131 "
                 "'Through which sense do you mostly experience ...' questions and 2,840 'which of two words ... more "
                 "through <sense>' pairs with answers from the norms. Enough.",
        scoring="Per sense: rank correlation with the human mean, and the mean rating on a common 0-5 scale (Jev's "
                "level x 5/4), with 90% bootstrap intervals. For the dominant-sense questions, a confusion table of "
                "Jev's answer against the norms' dominant sense.",
        chart="Paired bars per sense: people's mean vs Jev's mean on 0-5, with the rank correlation printed per row.",
        compared_with="Lancaster Sensorimotor Norms raters (Lynott et al. 2020, US and UK, MTurk and Prolific)",
        limits="The 0-5 mapping is approximate (Jev's levels are described in words, people's are numbered); the gap "
               "for sight is large enough that the conclusion doesn't depend on it, and the rank correlation, which "
               "doesn't use the mapping, points the same way.", sources=["lancaster", "lancaster_modality"])

    def run():
        rows = []
        for r in source("lancaster").iter_rows(named=True):
            m = re.search(r"by ([\w ]+)\?$", r["text"])
            if m and m.group(1) in SENSES:
                rows.append({"id": r["id"], "s": SENSES[m.group(1)], "jev": robust(r) * 5 / 4, "h": js(r["meta"])["mean_0_5"]})
        t = pl.DataFrame(rows)
        out = []
        for s in SENSES.values():
            g = t.filter(pl.col("s") == s)
            out.append({"label": s, "people": float(g["h"].mean()), "jev": float(g["jev"].mean()),
                        "gap_ci": boot((g["jev"] - g["h"]).to_numpy()), "rho": float(spearmanr(g["jev"], g["h"]).statistic),
                        "n": g.height})
        dom = []
        for r in source("lancaster_modality").iter_rows(named=True):
            if r["text"].startswith("Through which"):
                dom.append({"truth": json.loads(r["truth"]), "jev": top(js(r["jev_dist"]))})
        d = pl.DataFrame(dom)
        sight = d.filter(pl.col("truth") == "sight")
        s_touch = float((sight["jev"] == "touch").mean())
        s_ok = float((sight["jev"] == "sight").mean())
        conf = d.group_by("truth", "jev").len().to_dicts()
        o = {x["label"]: x for x in out}
        return Result(
            result=f"Jev's sense of how much we smell and taste words matches people's (means {o['Smell']['jev']:.1f} vs "
                   f"{o['Smell']['people']:.1f} and {o['Taste']['jev']:.1f} vs {o['Taste']['people']:.1f} on 0-5), but it "
                   f"rates how much we see them at {o['Sight']['jev']:.1f} where people say {o['Sight']['people']:.1f}, "
                   f"and sight is the sense it ranks words by least like people (rank correlation {o['Sight']['rho']:.2f}, "
                   f"against {o['Hearing']['rho']:.2f} for hearing). Of words people experience mainly by sight, it names "
                   f"sight for {s_ok:.0%} and touch for {s_touch:.0%}.",
            evidence=f"{t.height:,} sense ratings over about 1,980 words per sense; {d.height:,} dominant-sense questions",
            numbers={"senses": out, "dominant_confusion": conf, "sight_named_sight": s_ok, "sight_named_touch": s_touch},
            chart={"type": "bars2", "labels": [x["label"] for x in out], "a": [x["people"] for x in out],
                   "b": [x["jev"] for x in out], "a_label": "people (0-5)", "b_label": "Jev (0-5)",
                   "notes": [f"rank correlation {x['rho']:.2f}" for x in out]},
            robustness="With the levels reversed, the sight gap stays (the robust level already averages both orders).",
            examples=seeded(t.filter(pl.col("s") == "Sight")["id"].to_list(), "senses"), n=t.height + d.height)
    return spec, run


SHOWN = ("blah", "flee")  # hand-picked from the ten largest agreed-on gaps (see limits)


def iconicity():
    spec = Spec(
        id="words_iconicity", family="words", title="Beyond 'moo' and 'beep', Jev hears less sound-meaning link than people",
        question="Asked how much a word sounds like what it means, does Jev hear the same links people do?",
        why="Iconicity (the 'buzz' in buzz) is a live topic in the science of language: people hear some of it in "
            "ordinary words too. A model that only reads text never hears words at all.",
        sourcing="Existing questions ('How much does the word \"<word>\" sound like what it means?', seven described "
                 "levels) on 2,488 words from Winter et al. 2023, each with about 10 raters' individual ratings. Enough.",
        scoring="Rank correlation between Jev's robust level and the raters' mean, with a 90% bootstrap interval; mean "
                "level for each side on the 1-7 scale; the share of words each side puts in the bottom two levels; the "
                "largest gaps each way.",
        chart="A scatter of raters' mean (x) against Jev's (y) with the onomatopoeia labeled and the biggest misses "
              "marked.",
        compared_with="Winter et al. 2023 raters (US English speakers, about 10 per word)",
        limits="Ten raters per word leaves each word's mean noisy, which caps the correlation. Jev can't hear; it "
               "answers from what text says about words. The two words named in the result are hand-picked from the "
               "ten largest gaps among words the raters agreed on.", sources=["iconicity_ratings"])

    def run():
        rows = []
        for r in source("iconicity_ratings").iter_rows(named=True):
            h = biggest(r["humans"])
            if h:
                d, m = h["dist"], level(h["dist"])
                sd = float(np.sqrt(sum(v * (int(k) - m) ** 2 for k, v in d.items())))
                rows.append({"id": r["id"], "w": word(r["text"]), "jev": robust(r) + 1, "h": m + 1, "sd": sd})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("h")).alias("gap"))
        rho = float(spearmanr(t["jev"], t["h"]).statistic)
        low_j, low_h = float((t["jev"] < 2.5).mean()), float((t["h"] < 2.5).mean())
        top_j = t.sort("jev", descending=True).head(8).to_dicts()
        # the biggest misses among words the raters agreed on (rating spread under 1.3 levels)
        under = t.filter(pl.col("sd") < 1.3).sort("gap").head(10).to_dicts()
        shown = [x for x in under if x["w"] in SHOWN] or under[:2]
        return Result(
            result=f"Jev puts {low_j:.0%} of words in the bottom two levels ('nothing in how it sounds connects to what it "
                   f"means'), against {low_h:.0%} for people; its average is {t['jev'].mean():.1f} vs their "
                   f"{t['h'].mean():.1f} on 1-7. It agrees about the obvious ones ({', '.join(x['w'] for x in top_j[:4])}) and "
                   f"orders words {agree_word(rho)} like people overall (rank correlation {rho:.2f}), but hears little in "
                   f"words like '{shown[0]['w']}' and '{shown[1]['w']}' that people rate as strongly iconic.",
            evidence=f"{t.height:,} words, about 10 raters each; 90% interval on the correlation "
                     f"{rho_ci(t['jev'], t['h'])}; mean gap 90% interval {boot(t['gap'].to_numpy())}",
            numbers={"rho": rho, "mean_jev": float(t["jev"].mean()), "mean_people": float(t["h"].mean()),
                     "low_jev": low_j, "low_people": low_h, "top": top_j, "under": under,
                     "over": t.sort("gap", descending=True).head(6).to_dicts()},
            chart={"type": "scatter", "points": t.select("h", "jev").to_numpy().round(3).tolist(),
                   "x": "people's mean (1-7)", "y": "Jev's level (1-7)", "diagonal": True,
                   "labels": [{"label": x["w"], "x": x["h"], "y": x["jev"]} for x in top_j[:4] + under[:4]]},
            examples=[top_j[0]["id"], under[0]["id"]], n=t.height)
    return spec, run


def sound_shapes():
    spec = Spec(
        id="words_sound_shapes", family="words", title="Bouba and kiki: Jev hears it like people, only more so",
        question="Asked whether made-up words sound round or pointed, does Jev show the bouba/kiki effect people do, "
                 "and how strongly?",
        why="Almost everyone, in almost every language, calls a round blob 'bouba' and a spiky shape 'kiki'. A model "
            "that has only read about it might reproduce the effect, flatten it, or exaggerate it.",
        sourcing="Existing questions on 536 made-up words (McCormick et al. 2015; 'Does it sound more like a round "
                 "shape or a pointed shape?', seven levels) with about 52 raters each, and the two classic bouba/kiki "
                 "questions with the pooled answers from 25 language groups (Ćwiek et al. 2022). Enough.",
        scoring="Rank correlation over the 536 words between Jev's robust level and the raters' mean; the spread "
                "(standard deviation) of each side's ratings; for bouba and kiki, the share choosing the expected shape.",
        chart="A dumbbell per made-up word sorted by people's rating (people vs Jev), and the two classic words as "
              "paired bars.",
        compared_with="McCormick et al. 2015 raters; Ćwiek et al. 2022 participants in 25 language groups",
        limits="Jev reads the spelling and IPA; raters heard or read the words. The bouba/kiki questions are only two, "
               "so they illustrate rather than measure.", sources=["pseudoword_shapes", "bouba_kiki"])

    def run():
        rows = []
        for r in source("pseudoword_shapes").iter_rows(named=True):
            h = biggest(r["humans"])
            if h:
                rows.append({"id": r["id"], "w": word(r["text"]), "jev": robust(r), "h": level(h["dist"])})
        t = pl.DataFrame(rows)
        rho = float(spearmanr(t["jev"], t["h"]).statistic)
        bk = {}
        for r in source("bouba_kiki").iter_rows(named=True):
            k = "kiki" if '"kiki"' in r["text"] else "bouba"
            want = "spiky_shape" if k == "kiki" else "round_shape"
            h = next(x for x in json.loads(r["humans"]) if x.get("n") and "25 language" in x.get("population", ""))
            bk[k] = {"jev": norm(js(r["jev_dist"]))[want], "people": norm(h["dist"])[want]}
        return Result(
            result=f"Jev sorts {t.height} made-up words from round to pointed {agree_word(rho)} like people (rank "
                   f"correlation {rho:.2f}), but more extremely: its ratings spread "
                   f"{t['jev'].std() / t['h'].std():.1f} times as wide, from '{t.sort('jev')['w'][0]}' at "
                   f"{t['jev'].min():.1f} to '{t.sort('jev')['w'][-1]}' at {t['jev'].max():.1f} on 0-6, where people's "
                   f"averages stay between {t['h'].min():.1f} and {t['h'].max():.1f}. It calls kiki spiky "
                   f"{bk['kiki']['jev']:.0%} of the time; people across 25 languages, {bk['kiki']['people']:.0%}.",
            evidence=f"{t.height} made-up words, about 52 raters each; 90% interval on the correlation "
                     f"{rho_ci(t['jev'], t['h'])}; bouba/kiki from 400+ participants",
            numbers={"rho": rho, "sd_jev": float(t["jev"].std()), "sd_people": float(t["h"].std()), "bouba_kiki": bk},
            chart={"type": "scatter", "points": t.select("h", "jev").to_numpy().round(3).tolist(), "diagonal": True,
                   "x": "people's mean (0 round - 6 pointed)", "y": "Jev's level (0-6)",
                   "bars": [{"label": k, "people": v["people"], "jev": v["jev"]} for k, v in bk.items()]},
            examples=[t.sort("jev")["id"][0], t.sort("jev")["id"][-1]], n=t.height + 2)
    return spec, run


EXPERIMENTS = [word_norms(), arousal(), senses(), iconicity(), sound_shapes()]
