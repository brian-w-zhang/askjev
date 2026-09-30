"""Experiments for thin branches of the tree (docs/experiments/coverage.md): datasets already in the corpus, with real
people's answers or a right answer, that no experiment about their topic used. Fictional characters as fans see
them, school and exam subjects, the mood of money news, emotions in tweets, and the ETHICS labels."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

import numpy as np

from lib import Result, Spec, biggest, boot, js, norm, seeded, source, top, with_meta


def _key(t) -> str:
    return "true" if t is True else "false" if t is False else str(t)


def _graded(src: str, meta: bool = False) -> list[dict]:
    """One row per question with a right answer: the key, Jev's top pick, its probability of the key and of its pick."""
    out = []
    for r in (with_meta(src) if meta else source(src).iter_rows(named=True)):
        d = norm(js(r["jev_dist"]))
        k = _key(js(r["truth"]))
        out.append({"id": r["id"], "truth": k, "jev": top(d), "p_truth": d.get(k, 0.0), "conf": max(d.values()),
                    "template": r.get("template_id"), "m": r.get("m") or {}})
    return out


# ---- fictional characters ------------------------------------------------------------------------------------------
def characters():
    spec = Spec(
        id="reading_characters", family="reading", title="Jev reads fictional characters as more down to earth than fans do",
        question="Asked which of two opposite words fits a fictional character better (orderly or chaotic, romantic or "
                 "dispassionate), does Jev side with the fans who rated that character, and where does it lean "
                 "differently from them?",
        why="Describing people, real or invented, is everyday work for a language model: summaries, recommendations, "
            "fan wikis. If it reads characters the way the people who know them do, it has absorbed more than plot "
            "facts; if it leans one way across thousands of characters, the lean is a habit of its own.",
        sourcing="Existing questions from the Open Psychometrics 'Which Character' quiz data: people who know a show, "
                 "film or book rated its characters on slider scales between two opposite words, and each question is "
                 "one character on one pair, asked as a pick between the two words. The fans' side is the share of "
                 "raters who put the slider past the middle toward each word. Enough: about 19,000 character-pair "
                 "questions over some 2,000 characters from several hundred works.",
        scoring="Agreement: how often Jev's more likely word is the one most fans leaned to, over all pairs and over "
                "clear ones (fans split at least 80/20). Correlation between Jev's probability and the fans' share. "
                "Lean: for each word, Jev's probability minus the fans' share, averaged over every pair it appears in "
                "(words seen at least 40 times), with 90% bootstrap intervals; positive means Jev picks the word more "
                "than fans do.",
        chart="Dots per word: how much more or less often Jev picks it than fans, the ten words it favors most and the "
              "ten it avoids most.",
        compared_with="Quiz-takers who rated characters from works they know (openpsychometrics.org, 2019-2023)",
        limits="Raters chose characters they know and like enough to rate; sliders were turned into a two-way split at "
               "the middle. Characters are famous, so Jev may recall fan discussion rather than read the character.",
        sources=["character_traits"])

    def run():
        xs = []
        for r in source("character_traits").iter_rows(named=True):
            d, h = norm(js(r["jev_dist"])), biggest(r["humans"])
            if not h:
                continue
            hd = norm(h["dist"])
            a, b = list(d)
            m = re.search(r"describes (.+?) better", r["text"])
            pf = norm(js(r["people_dist"]) or {}) if r["people_dist"] else {}
            xs.append({"id": r["id"], "a": a, "b": b, "p": d[a], "h": hd.get(a, 0.0), "f": pf.get(a),
                       "who": m.group(1) if m else ""})
        p, h = np.array([x["p"] for x in xs]), np.array([x["h"] for x in xs])
        agree = (p > 0.5) == (h > 0.5)
        clear = np.abs(h - 0.5) >= 0.3
        rho = float(np.corrcoef(p, h)[0, 1])
        lean, frame, mid, side = defaultdict(list), defaultdict(list), Counter(), Counter()
        for x in xs:
            lean[x["a"]].append(x["p"] - x["h"])
            lean[x["b"]].append(x["h"] - x["p"])
            if x["f"] is not None:  # the same lean in Jev's guess at what fans of the work would say
                frame[x["a"]].append(x["f"] - x["h"])
                frame[x["b"]].append(x["h"] - x["f"])
            if 0.3 <= x["h"] <= 0.7:  # pairs fans split on: which side Jev takes there
                for w, pw in ((x["a"], x["p"]), (x["b"], 1 - x["p"])):
                    mid[w] += 1
                    side[w] += pw > 0.5
        words = sorted(({"word": w.replace("_", " "), "value": float(np.mean(v)), "ci": boot(v), "n": len(v),
                         "frame": float(np.mean(frame[w])) if frame[w] else None, "split_pairs": mid[w],
                         "jev_side_on_split": side[w]}
                        for w, v in lean.items() if len(v) >= 40), key=lambda w: w["value"])
        most, least = words[::-1][:10], words[:10]
        # the clear cases Jev gets backwards, most confident first
        wrong = sorted((x for x, c, g in zip(xs, clear, agree) if c and not g), key=lambda x: -abs(x["p"] - 0.5))
        ex = [x["id"] for x in wrong[:6]]
        fav = ", ".join(w["word"] for w in most[:4])
        avoid = ", ".join(w["word"] for w in least[:4])
        return Result(
            result=f"On {int(clear.sum()):,} character-and-trait pairs where fans clearly lean one way, Jev picks the same "
                   f"side {agree[clear].mean():.0%} of the time. Where it differs, it leans one way: it calls characters "
                   f"{fav} more often than fans do, and {avoid} less often.",
            evidence=f"{len(xs):,} pairs; agreement on all pairs {agree.mean():.0%}; correlation of Jev's probability with "
                     f"the fans' share {rho:.2f}; lean on '{most[0]['word']}' {most[0]['value']:+.2f} (90% interval "
                     f"{most[0]['ci']}), on '{least[0]['word']}' {least[0]['value']:+.2f} ({least[0]['ci']})",
            numbers={"n": len(xs), "n_clear": int(clear.sum()), "agree_clear": float(agree[clear].mean()),
                     "agree_all": float(agree.mean()), "corr": rho, "favors": most, "avoids": least,
                     "n_words": len(words)},
            n=len(xs),
            chart={"type": "dots", "zero": 0, "x": "Jev picks the word more (+) or less (−) than fans, share",
                   "rows": [{"label": w["word"], "group": "Jev says it more", "value": round(w["value"], 3), "ci": w["ci"]} for w in most]
                   + [{"label": w["word"], "group": "Jev says it less", "value": round(w["value"], 3), "ci": w["ci"]} for w in least]},
            robustness="The lean is averaged over every character a word is paired with, so it isn't one show's quirk; "
                       f"the words at each end appear in {min(w['n'] for w in most[:4] + least[:4])} or more pairs.",
            examples=ex, ids=[x["id"] for x in xs])
    return spec, run


# ---- school and exam subjects ----------------------------------------------------------------------------------------
EXAMS = [("arc", "ARC grade-school science"), ("sciq", "SciQ science"), ("openbookqa", "OpenBookQA science"),
         ("commonsense_qa", "CommonsenseQA"), ("hotpot_compare", "HotpotQA comparisons"), ("head_qa", "HEAD-QA (Spanish health exams)")]


def exams():
    spec = Spec(
        id="knowledge_exam_subjects", family="knowledge", title="Across 58 exam subjects, Jev's one deep dip is virology",
        question="Across MMLU's school and university subjects, grade-school science and everyday common sense, where "
                 "is Jev reliably right, where does it dip, and does it know when it's on weak ground?",
        why="A model that is equally good everywhere is easy to trust; one with hidden dips isn't. Laying the same "
            "kind of question out subject by subject shows the shape of what Jev knows, the jaggedness, rather than "
            "one average.",
        sourcing="Existing multiple-choice questions with answer keys: MMLU (57 subjects from high school to "
                 "professional level), ARC (grade-school science, easy and challenge sets), SciQ, OpenBookQA, "
                 "CommonsenseQA, HotpotQA comparison questions and HEAD-QA (Spanish health-profession exams, in "
                 "English). Questions whose answers are numbers or calculations were left out when the corpus was "
                 "built. Enough: about 33,000 questions, 40 or more in each subject shown.",
        scoring="Accuracy per subject (Jev's most likely option equals the key) with 90% bootstrap intervals; Jev's "
                "average confidence in its pick on the questions it gets wrong vs right; the rank correlation between "
                "a subject's accuracy and Jev's average confidence there (does it know where it's weak).",
        chart="Dots per subject with intervals, the lowest subjects and the grade-school sets for contrast.",
        compared_with="The answer keys (and, where a paper reports one, people's accuracy on the same set)",
        limits="Exam keys have errors, and some subjects have more than others (see the caveats); these are famous "
               "public sets that Jev may have seen in training. Indicators of shape, not a score.",
        sources=["mmlu"] + [s for s, _ in EXAMS])

    def run():
        groups = defaultdict(list)
        for r in _graded("mmlu", meta=True):
            groups[("MMLU", r["m"].get("subject", "?").replace("_", " "))].append(r)
        for s, name in EXAMS:
            for r in _graded(s, meta=True):
                sub = r["m"].get("config") or r["m"].get("category") or ""
                groups[(name, {"nursery": "nursing"}.get(sub, sub).replace("ARC-", "").lower())].append(r)
        rows = []
        for (exam, sub), g in groups.items():
            if len(g) < 40:
                continue
            ok = np.array([r["truth"] == r["jev"] for r in g], float)
            conf = np.array([r["conf"] for r in g])
            rows.append({"exam": exam, "subject": sub, "label": f"{sub} ({exam})" if exam == "MMLU" else f"{exam}{': ' + sub if sub else ''}",
                         "n": len(g), "acc": float(ok.mean()), "ci": boot(ok), "conf": float(conf.mean()),
                         "conf_wrong": float(conf[ok == 0].mean()) if (ok == 0).any() else None,
                         "ids": [r["id"] for r in g], "miss": [r["id"] for r in g if r["truth"] != r["jev"]]})
        rows.sort(key=lambda r: r["acc"])
        allr = [r for g in groups.values() for r in g]
        ok = np.array([r["truth"] == r["jev"] for r in allr], float)
        conf = np.array([r["conf"] for r in allr])
        mm = [r for r in rows if r["exam"] == "MMLU"]
        from scipy.stats import spearmanr
        rho = float(spearmanr([r["acc"] for r in rows], [r["conf"] for r in rows]).statistic)
        low = rows[:5]
        above90 = sum(r["acc"] >= 0.9 for r in mm)
        grade = [r for r in rows if r["exam"].startswith("ARC")]
        shown = rows[:14] + [r for r in rows if r["exam"] != "MMLU" and r not in rows[:14]]
        return Result(
            result=f"Jev picks the keyed answer on {ok.mean():.0%} of {len(allr):,} exam questions, and {above90} of "
                   f"{len(mm)} MMLU subjects sit at 90% or above. One dip is deep: {low[0]['subject']} at "
                   f"{low[0]['acc']:.0%}; the next lowest are "
                   + " and ".join(f"{r['subject']} ({r['acc']:.0%})" for r in low[1:3])
                   + f". It is less sure where it's weaker (rank correlation {rho:.2f} between a subject's accuracy and "
                   f"Jev's confidence there), and still {conf[ok == 0].mean():.0%} sure on average when it's wrong.",
            evidence=f"{len(rows)} subjects or sets with 40+ questions; lowest {low[0]['label']} {low[0]['acc']:.0%} "
                     f"(90% interval {low[0]['ci']}, n={low[0]['n']}); average confidence {conf[ok == 1].mean():.0%} when "
                     f"right, {conf[ok == 0].mean():.0%} when wrong",
            numbers={"overall": float(ok.mean()), "n": len(allr), "n_subjects": len(rows), "mmlu_subjects": len(mm),
                     "mmlu_90": above90, "rho_acc_conf": rho, "conf_right": float(conf[ok == 1].mean()),
                     "conf_wrong": float(conf[ok == 0].mean()),
                     "subjects": [{k: v for k, v in r.items() if k not in ("ids", "miss")} for r in rows],
                     "grade_school": [{"label": r["label"], "acc": r["acc"]} for r in grade]},
            n=len(allr),
            chart={"type": "dots", "domain": [0, 1], "x": "share right",
                   "rows": [{"label": r["label"], "group": "lowest subjects" if r in rows[:14] else "other sets",
                             "value": round(r["acc"], 3), "ci": r["ci"], "note": f"n={r['n']}"} for r in shown]},
            robustness="Subjects with fewer than 40 questions are left out; intervals are over questions. The ordering "
                       "below the first is within a few points, so their order is loose.",
            examples=[i for r in low[:3] for i in seeded(r["miss"], r["subject"], 2)],
            ids=[i for r in rows for i in r["ids"]])
    return spec, run


# ---- the mood of money news ------------------------------------------------------------------------------------------
MONEY = [("financial_phrasebank", "Financial news sentences", "neutral", "positive", "negative"),
         ("fin_tweet_sentiment", "Market tweets", "neutral", "bullish", "bearish"),
         ("gold_headlines", "Gold-price headlines", "neither", "up", "down")]


def money():
    spec = Spec(
        id="work_money_news_mood", family="work", title="Jev hears good news in neutral money news",
        question="Reading financial news, market tweets and gold-price headlines that experts labeled as neutral (no "
                 "good or bad news, no direction), how often does Jev read them as good news or as bad news, and is "
                 "it lopsided?",
        why="Sorting news by sentiment is routine work for trading desks, analysts and news feeds. A reader that "
            "mistakes neutral news for good news more than for bad news tilts every summary it writes, and the "
            "tilt would compound across thousands of items.",
        sourcing="Existing questions from three labeled datasets: the Financial PhraseBank (sentences from company "
                 "news, labeled good, neutral or bad for investors by annotators with finance training; only "
                 "sentences all of them agreed on), a set of finance tweets labeled bullish, bearish or neutral, and "
                 "gold-market headlines (2000-2019) labeled for whether they report the price rising or falling. "
                 "Enough: about 8,500 questions, 2,874 of them labeled neutral.",
        scoring="For the neutral items in each set, the share Jev calls good (positive, bullish, up) and the share it "
                "calls bad; the ratio between the two is the lean, with 90% bootstrap intervals. Also accuracy on the "
                "good and bad items, to show the lean isn't just missing direction altogether.",
        chart="Paired bars per dataset: neutral read as good vs neutral read as bad.",
        compared_with="The datasets' labels (finance-trained annotators for the PhraseBank)",
        limits="Tweet and headline labels come from single datasets' annotators; the neutral class is the hardest to "
               "label, so some 'errors' are borderline items. Descriptions of each label were written for this "
               "project.",
        sources=[s for s, *_ in MONEY])

    def run():
        rows, ex, ids = [], [], []
        for src, name, neu, good, bad in MONEY:
            g = [r for r in _graded(src) if r["truth"] in (neu, good, bad)]
            n_ = [r for r in g if r["truth"] == neu]
            up = np.array([r["jev"] == good for r in n_], float)
            dn = np.array([r["jev"] == bad for r in n_], float)
            pol = [r for r in g if r["truth"] != neu]
            rows.append({"dataset": name, "n": len(g), "n_neutral": len(n_), "neutral_as_good": float(up.mean()),
                         "ci_good": boot(up), "neutral_as_bad": float(dn.mean()), "ci_bad": boot(dn),
                         "polar_right": float(np.mean([r["jev"] == r["truth"] for r in pol])),
                         "good_as_bad": float(np.mean([r["jev"] == bad for r in pol if r["truth"] == good])),
                         "bad_as_good": float(np.mean([r["jev"] == good for r in pol if r["truth"] == bad]))})
            ex += seeded([r["id"] for r in n_ if r["jev"] == good], src, 2)
            ids += [r["id"] for r in g]
        tot_g = sum(r["neutral_as_good"] * r["n_neutral"] for r in rows)
        tot_b = sum(r["neutral_as_bad"] * r["n_neutral"] for r in rows)
        f, t, h = rows
        return Result(
            result=f"On news its labelers called neutral, Jev hears good news {tot_g / tot_b:.1f} times as often as bad: "
                   f"{f['neutral_as_good']:.0%} vs {f['neutral_as_bad']:.0%} of neutral company-news sentences, "
                   f"{t['neutral_as_good']:.0%} vs {t['neutral_as_bad']:.0%} of neutral market tweets. On gold headlines "
                   f"the lean disappears ({h['neutral_as_good']:.0%} up vs {h['neutral_as_bad']:.0%} down). When news "
                   f"is clearly good or bad, it gets the direction backwards on {max(r['good_as_bad'] for r in rows):.0%} "
                   f"or less of items in each set.",
            evidence=f"{sum(r['n_neutral'] for r in rows):,} neutral items; 90% intervals, PhraseBank read as good "
                     f"{f['ci_good']} vs bad {f['ci_bad']}, tweets {t['ci_good']} vs {t['ci_bad']}",
            numbers={"datasets": rows, "ratio": tot_g / tot_b}, n=sum(r["n"] for r in rows),
            chart={"type": "bars2", "labels": [r["dataset"] for r in rows], "a": [r["neutral_as_good"] for r in rows],
                   "b": [r["neutral_as_bad"] for r in rows], "a_label": "neutral read as good news",
                   "b_label": "neutral read as bad news"},
            robustness="Each dataset was labeled by different people with different label descriptions; the lean shows "
                       "in the two about companies and markets, not in the one about a commodity price.",
            examples=ex, ids=ids)
    return spec, run


# ---- emotions in tweets ----------------------------------------------------------------------------------------------
EMO = ["joy", "love", "surprise", "sadness", "anger", "fear"]


def tweets():
    spec = Spec(
        id="social_tweet_emotions", family="social", title="In short posts, Jev reads love as joy and anger as sadness",
        question="Given a short tweet and six emotions (joy, love, surprise, sadness, anger, fear), does Jev name the "
                 "one its writer tagged, and which emotions does it mix up? And does it notice thanks in Reddit "
                 "comments?",
        why="Coding the feeling in short texts is a staple of market research, support triage and social science. The "
            "mix-ups matter more than the average: an emotion Jev reliably folds into another disappears from "
            "whatever it summarizes.",
        sourcing="Existing questions from two datasets: an emotion set of about 2,000 English tweets whose label comes "
                 "from the emotion hashtag its writer used (so the label is the writer's own tag, not a reader's "
                 "judgment), balanced across six emotions; and about 2,000 Reddit comments from GoEmotions, where "
                 "raters marked whether a comment expresses gratitude (half do; the other half include other warm "
                 "comments, so friendliness alone doesn't decide it).",
        scoring="For the tweets, the share of each emotion Jev names correctly and a table of what it names instead, "
                "with 90% bootstrap intervals. For the comments, the share of thankful ones it misses vs the share of "
                "others it calls thankful.",
        chart="A grid: the writer's emotion down the side, Jev's pick across the top, shaded by count.",
        compared_with="The writers' own hashtags (tweets) and raters' labels (Reddit comments)",
        limits="Hashtag labels are noisy: a writer who tags #love may be describing joy. The comparison is to the "
               "writer's tag, not to what other readers would say. Label descriptions were written for this project.",
        sources=["emotion", "goemotions_gratitude"])

    def run():
        t = [r for r in _graded("emotion") if r["truth"] in EMO]
        cells = Counter((r["truth"], r["jev"]) for r in t)
        per = []
        for e in EMO:
            g = np.array([r["jev"] == e for r in t if r["truth"] == e], float)
            wrong = Counter(r["jev"] for r in t if r["truth"] == e and r["jev"] != e).most_common(1)
            per.append({"emotion": e, "right": float(g.mean()), "ci": boot(g), "n": len(g),
                        "instead": wrong[0][0] if wrong else None, "instead_share": wrong[0][1] / len(g) if wrong else 0})
        acc = float(np.mean([r["jev"] == r["truth"] for r in t]))
        grat = _graded("goemotions_gratitude")
        pos = np.array([r["jev"] == "true" for r in grat if r["truth"] == "true"], float)
        neg = np.array([r["jev"] == "true" for r in grat if r["truth"] == "false"], float)
        by = {p["emotion"]: p for p in per}
        worst = sorted(per, key=lambda p: p["right"])
        return Result(
            result=f"Jev names the writer's own emotion tag for {acc:.0%} of tweets across six emotions (chance is 17%). "
                   f"The misses are patterned: love is called {by['love']['instead']} {by['love']['instead_share']:.0%} "
                   f"of the time, anger {by['anger']['instead']} {by['anger']['instead_share']:.0%}, surprise "
                   f"{by['surprise']['instead']} {by['surprise']['instead_share']:.0%}. With thanks it errs the careful way: "
                   f"it misses {1 - pos.mean():.0%} of thankful Reddit comments and calls only {neg.mean():.0%} of others "
                   f"thankful.",
            evidence=f"{len(t):,} tweets, about {len(t) // 6} per emotion; hardest {worst[0]['emotion']} "
                     f"{worst[0]['right']:.0%} right (90% interval {worst[0]['ci']}); {len(grat):,} Reddit comments",
            numbers={"acc": acc, "per_emotion": per, "gratitude_missed": 1 - float(pos.mean()),
                     "gratitude_false": float(neg.mean()), "n_tweets": len(t), "n_comments": len(grat)},
            n=len(t) + len(grat),
            chart={"type": "heat", "cells": [{"writer": a, "jev": b, "len": cells[(a, b)]} for a in EMO for b in EMO],
                   "x": "Jev's pick", "y": "writer's hashtag", "order": EMO},
            robustness="Each emotion has about the same number of tweets, so the mix-ups aren't driven by one emotion "
                       "being rare.",
            examples=seeded([r["id"] for r in t if r["truth"] == "love" and r["jev"] == "joy"], "love", 2)
            + seeded([r["id"] for r in t if r["truth"] == "anger" and r["jev"] == "sadness"], "anger", 2),
            ids=[r["id"] for r in t] + [r["id"] for r in grat])
    return spec, run


# ---- the ETHICS labels ------------------------------------------------------------------------------------------------
ETHICS = [("ethics_cs", None, "Is the narrator's action clearly wrong?", "wrong"),
          ("ethics_other", "ethics_other.excuse", "Is the excuse reasonable?", "reasonable"),
          ("ethics_other", "ethics_other.role", "Is the duty reasonable for the role?", "reasonable"),
          ("ethics_util", "ethics_util.justice", "Is the justification reasonable?", "reasonable")]


def ethics():
    spec = Spec(
        id="moral_ethics_labels", family="moral", title="Jev is harder on excuses than the ETHICS labels",
        question="On the ETHICS dataset's everyday moral questions (is this clearly wrong, is this excuse, duty or "
                 "justification reasonable, which trait does this person show, which situation is more pleasant), "
                 "how often does Jev agree with the crowd-validated labels, and when it doesn't, is it harsher or "
                 "more forgiving?",
        why="ETHICS was built so that nearly everyone agrees on each label, which makes it a test of shared moral "
            "sense rather than of contested views. Agreement will be high; the interesting part is the few "
            "disagreements, and whether they lean toward judging people harshly or letting them off.",
        sourcing="Existing questions from ETHICS (Hendrycks et al.; scenarios written and validated by crowd workers, "
                 "kept only when validators agreed) in five kinds: commonsense wrongness, excuses, role duties, "
                 "justice-style justifications, character traits and which of two situations is more pleasant; plus "
                 "Moral Stories (pick the action that follows a social norm). Enough: about 19,000 questions.",
        scoring="Agreement with the label per kind, with 90% bootstrap intervals. For the yes/no kinds, the two ways "
                "to disagree: stricter (calling an acceptable act wrong, or a reasonable excuse, duty or "
                "justification unreasonable) and more lenient (the reverse), as shares of all items of that kind.",
        chart="Paired bars per yes/no kind: stricter than the label vs more lenient than the label.",
        compared_with="The dataset's labels (crowd workers' agreed answers)",
        limits="The scenarios were written by crowd workers to have clear answers, so agreement near the top is "
               "expected; a disagreement can be a label error. Questions the content filter hid are not counted.",
        sources=["ethics_cs", "ethics_other", "ethics_util", "moral_stories"])

    def run():
        rows, yes_no, ex, ids = [], [], [], []
        for src, tpl, label, yes_means in ETHICS:
            g = [r for r in _graded(src) if tpl is None or r["template"] == tpl]
            n = len(g)
            if yes_means == "wrong":   # saying "wrong" to an acceptable act is the strict error
                strict = [r for r in g if r["truth"] == "false" and r["jev"] == "true"]
                lenient = [r for r in g if r["truth"] == "true" and r["jev"] == "false"]
            else:                      # saying "unreasonable" to a reasonable excuse is the strict error
                strict = [r for r in g if r["truth"] == "true" and r["jev"] == "false"]
                lenient = [r for r in g if r["truth"] == "false" and r["jev"] == "true"]
            ok = np.array([r["truth"] == r["jev"] for r in g], float)
            yes_no.append({"kind": label, "n": n, "agree": float(ok.mean()), "ci": boot(ok),
                           "stricter": len(strict) / n, "lenient": len(lenient) / n})
            ex += seeded([r["id"] for r in strict], label, 1)
            ids += [r["id"] for r in g]
        for src, tpl, label in [("ethics_other", "ethics_other.virtue", "Which trait does the person show?"),
                                ("ethics_util", "ethics_util.pleasant", "Which situation is more pleasant?"),
                                ("moral_stories", None, "Which action follows the norm?")]:
            g = [r for r in _graded(src) if tpl is None or r["template"] == tpl]
            ok = np.array([r["truth"] == r["jev"] for r in g], float)
            rows.append({"kind": label, "n": len(g), "agree": float(ok.mean()), "ci": boot(ok)})
            ids += [r["id"] for r in g]
        s = sum(k["stricter"] * k["n"] for k in yes_no)
        l_ = sum(k["lenient"] * k["n"] for k in yes_no)
        allk = yes_no + rows
        cs, exc, duty, just = yes_no
        return Result(
            result=f"Jev agrees with the ETHICS labels on {min(k['agree'] for k in allk):.0%} to "
                   f"{max(k['agree'] for k in allk):.0%} of questions depending on the kind. Its disagreements lean one "
                   f"way only on excuses and justifications: it rejects ones the labels accept ({exc['stricter']:.0%} and "
                   f"{just['stricter']:.0%} of items) about twice as often as it accepts ones they reject "
                   f"({exc['lenient']:.0%} and {just['lenient']:.0%}). On whether an act is clearly wrong it errs "
                   f"evenly ({cs['stricter']:.1%} vs {cs['lenient']:.1%}), and on duties it's the lenient one "
                   f"({duty['stricter']:.1%} vs {duty['lenient']:.1%}).",
            evidence=f"{sum(k['n'] for k in allk):,} questions in {len(allk)} kinds; stricter {int(s):,} vs more lenient "
                     f"{int(l_):,} on the yes/no kinds; "
                     + "; ".join(f"{k['kind']} {k['stricter']:.1%} vs {k['lenient']:.1%}" for k in yes_no),
            numbers={"yes_no": yes_no, "choice": rows, "stricter": int(s), "lenient": int(l_), "ratio": s / l_},
            n=sum(k["n"] for k in allk),
            chart={"type": "bars2", "labels": [k["kind"] for k in yes_no], "a": [k["stricter"] for k in yes_no],
                   "b": [k["lenient"] for k in yes_no], "a_label": "stricter than the label",
                   "b_label": "more lenient than the label"},
            robustness="The lean is counted separately for each kind; the kinds were written by different crowd tasks, "
                       "so a shared direction isn't one task's wording.",
            examples=ex, ids=ids)
    return spec, run


# ---- common knowledge -------------------------------------------------------------------------------------------------
def _pageviews() -> dict[str, int]:
    """qid -> English Wikipedia views in the 60 days to 2026-09-30 (prop=pageviews, 50 titles a request; the per-article
    API rate-limits a full run), from the vital-articles cache."""
    import json
    from pathlib import Path
    cache = Path("data/raw/vital/cache/pageviews_60d_api.json")
    if not cache.exists():
        return {}
    pv = json.loads(cache.read_text())
    out = {}
    for line in Path("data/raw/vital/level4.jsonl").open():
        a = json.loads(line)
        if a.get("qid") and pv.get(a["title"]) is not None:
            out[a["qid"]] = pv[a["title"]]
    return out


def heard_of():
    spec = Spec(
        id="knowledge_heard_of", family="knowledge", title="What Jev thinks everyone has heard of",
        question="Asked whether most adults have heard of a person, place, idea or thing from Wikipedia's list of "
                 "about 10,000 vital articles, does Jev say yes to the ones people actually look up, and in which "
                 "fields does it overestimate what everyone knows?",
        why="Pitching an explanation at the right level depends on knowing what people already know. A model that "
            "thinks everyone has heard of eigenvalues, or that nobody has heard of a famous athlete, will explain "
            "too little or too much.",
        sourcing="Existing yes/no questions on every Level 4 vital article ('Would most adults have heard of "
                 "\"Toshiro Mifune\"?'), about 9,300. The comparison is how often each article was opened on "
                 "English Wikipedia in the 60 days to 30 September 2026, from Wikipedia's public page-view counts, "
                 "and the number of language editions that have an article on it.",
        scoring="Rank correlation between Jev's probability of yes and the article's views. Then, for each field on "
                "the vital list, Jev's average yes against what its views would predict (a rank-based fit over all "
                "articles), with 90% bootstrap intervals: positive means Jev assumes more people know that field's "
                "things than its readership suggests.",
        chart="Dots per field: how much more (or less) Jev assumes is common knowledge than views predict.",
        compared_with="English Wikipedia readers' page views (a measure of attention, not of recognition)",
        limits="Views measure how often people look something up, not whether they've heard of it: everyone knows "
               "'water', few read its article. Sixty days; English Wikipedia only.",
        sources=["vital4"])

    def run():
        from scipy.stats import spearmanr, rankdata
        pv = _pageviews()
        xs = []
        for r in with_meta("vital4"):
            if r.get("template_id") != "g6.recognize":
                continue
            q = r["m"].get("qid")
            if q not in pv:
                continue
            d = norm(js(r["jev_dist"]))
            xs.append({"id": r["id"], "p": d.get("true", 0.0), "pv": pv[q], "links": r["m"].get("sitelinks") or 0,
                       "field": (r["m"].get("vital_section") or "?").split(" > ")[0], "text": r["text"]})
        n_all = sum(1 for r in with_meta("vital4") if r.get("template_id") == "g6.recognize")
        if len(xs) < 0.9 * n_all:  # a partial fetch is ordered by section, so it would skew the fields
            return None
        p = np.array([x["p"] for x in xs])
        v = np.log10(np.array([x["pv"] for x in xs]) + 1)
        rho = float(spearmanr(p, v).statistic)
        rho_links = float(spearmanr(p, [x["links"] for x in xs]).statistic)
        # what views predict: Jev's average yes among articles at the same views rank (a running mean over ranks)
        order = np.argsort(v)
        w = 301
        pred = np.empty(len(p))
        ps = p[order]
        cs = np.concatenate([[0], np.cumsum(ps)])
        for k in range(len(ps)):
            lo, hi = max(0, k - w // 2), min(len(ps), k + w // 2 + 1)
            pred[order[k]] = (cs[hi] - cs[lo]) / (hi - lo)
        res = p - pred
        fields = defaultdict(list)
        for x, e in zip(xs, res):
            fields[x["field"]].append(e)
        rows = sorted(({"field": f, "value": float(np.mean(e)), "ci": boot(e), "n": len(e)}
                       for f, e in fields.items() if len(e) >= 100), key=lambda r: -r["value"])
        yes = float((p > 0.5).mean())
        top_dec = p[v >= np.percentile(v, 90)].mean()
        bot_dec = p[v <= np.percentile(v, 10)].mean()
        over = sorted(range(len(xs)), key=lambda i: -res[i])
        under = sorted(range(len(xs)), key=lambda i: res[i])
        hi, lo = rows[0], rows[-1]
        return Result(
            result=f"Jev says most adults have heard of {yes:.0%} of Wikipedia's 'vital' topics. Its yes follows how much "
                   f"people read them (rank correlation {rho:.2f}): {top_dec:.0%} likely for the most-read tenth, "
                   f"{bot_dec:.0%} for the least-read. By field, it overestimates common knowledge most in "
                   f"{hi['field'].lower()} and underestimates it most in {lo['field'].lower()}.",
            evidence=f"{len(xs):,} articles with 60-day views; {hi['field']} {hi['value']:+.2f} (90% interval "
                     f"{hi['ci']}), {lo['field']} {lo['value']:+.2f} ({lo['ci']}); correlation with the number of "
                     f"language editions {rho_links:.2f}",
            numbers={"n": len(xs), "yes": yes, "rho_views": rho, "rho_languages": rho_links, "top_tenth": float(top_dec),
                     "bottom_tenth": float(bot_dec), "fields": rows,
                     "over": [{"text": xs[i]["text"], "p": xs[i]["p"], "views": xs[i]["pv"]} for i in over[:10]],
                     "under": [{"text": xs[i]["text"], "p": xs[i]["p"], "views": xs[i]["pv"]} for i in under[:10]]},
            n=len(xs),
            chart={"type": "dots", "zero": 0, "x": "Jev's yes minus what views predict",
                   "rows": [{"label": r["field"], "value": round(r["value"], 3), "ci": r["ci"], "note": f"n={r['n']}"} for r in rows]},
            robustness="The views-based prediction is Jev's own average at the same views rank, so a field only stands "
                       "out if Jev treats its topics differently from equally read topics elsewhere.",
            examples=[xs[i]["id"] for i in over[:3]] + [xs[i]["id"] for i in under[:3]],
            ids=[x["id"] for x in xs])
    return spec, run


EXPERIMENTS = [characters(), exams(), money(), tweets(), ethics(), heard_of()]
