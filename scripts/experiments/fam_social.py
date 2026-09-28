"""Social reading experiments: which emotions Jev names and which it avoids, what it sees in stories, Family Feud
answers, the values it trades off in everyday dilemmas, and which social questions it reads best."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import polars as pl

from lib import Result, Spec, biggest, boot, js, norm, seeded, source, top


def _truth(r) -> str:
    return json.loads(r["truth"])


@lru_cache(maxsize=None)
def labeled(src: str) -> pl.DataFrame:
    """One row per labeled emotion item: the writer's label, Jev's top pick, and its probability."""
    rows = []
    for r in source(src).iter_rows(named=True):
        d = norm(js(r["jev_dist"]))
        rows.append({"id": r["id"], "truth": _truth(r), "jev": top(d), "p": d[top(d)], "d": json.dumps(d)})
    return pl.DataFrame(rows)


def _rate(t: pl.DataFrame, a: str, b: str) -> tuple[float, int]:
    """Share of items labeled `a` that Jev calls `b`, and how many items are labeled `a`."""
    g = t.filter(pl.col("truth") == a)
    return float((g["jev"] == b).mean()), g.height


# ---- emotions ------------------------------------------------------------------------------------------------------
def shame_guilt():
    spec = Spec(
        id="social_shame_as_guilt", family="social", title="Jev hears shame as guilt",
        question="When people describe a time they felt ashamed, does Jev name shame, or does it call it guilt?",
        why="Psychologists separate the two: guilt is about something you did, shame is about who you are. A reader "
            "that folds shame into guilt misses the more painful feeling, and the confusion should run one way only.",
        sourcing="Existing questions from two datasets where the writer named their own feeling: ISEAR (people in 37 "
                 "countries describing a time they felt one of seven emotions, guilt and shame among them) and "
                 "EmpatheticDialogues (short situations written under one of 32 emotion labels, 'ashamed' and "
                 "'guilty' among them). Jev picks one emotion from the dataset's list. Enough: about 400 shame and 400 "
                 "guilt stories in ISEAR, about 90 of each in EmpatheticDialogues.",
        scoring="For each dataset, the share of shame stories Jev calls guilt and the share of guilt stories it calls "
                "shame, with 90% bootstrap intervals over stories; the gap between the two directions is the finding.",
        chart="Paired bars per dataset: shame read as guilt vs guilt read as shame.",
        compared_with="The writers' own labels for their feelings",
        limits="The writer's label is one person's word for a mixed feeling; ISEAR stories were translated and "
               "shortened. Jev sees only the list of emotions the dataset offers.",
        sources=["isear", "empathetic_dialogues"])

    def run():
        rows, ex, used = [], [], []
        for src, shame, guilt, name in [("isear", "shame", "guilt", "ISEAR"),
                                        ("empathetic_dialogues", "ashamed", "guilty", "EmpatheticDialogues")]:
            t = labeled(src)
            s = t.filter(pl.col("truth") == shame)
            g = t.filter(pl.col("truth") == guilt)
            sg, gs = (s["jev"] == guilt).cast(float).to_numpy(), (g["jev"] == shame).cast(float).to_numpy()
            rows.append({"dataset": name, "shame_as_guilt": float(sg.mean()), "ci_sg": boot(sg), "n_shame": s.height,
                         "guilt_as_shame": float(gs.mean()), "ci_gs": boot(gs), "n_guilt": g.height,
                         "shame_right": float((s["jev"] == shame).mean()), "guilt_right": float((g["jev"] == guilt).mean())})
            ex += seeded(s.filter(pl.col("jev") == guilt)["id"].to_list(), "shame", 2)
            used += s["id"].to_list() + g["id"].to_list()
        i, e = rows
        return Result(
            result=f"Asked to name the feeling in someone's own story of shame, Jev says guilt {e['shame_as_guilt']:.0%} "
                   f"of the time in EmpatheticDialogues (it says ashamed {e['shame_right']:.0%}) and "
                   f"{i['shame_as_guilt']:.0%} in ISEAR. The reverse mistake is rare: guilt stories are called shame "
                   f"{e['guilt_as_shame']:.0%} and {i['guilt_as_shame']:.0%} of the time.",
            evidence=f"{e['n_shame']} + {i['n_shame']} shame stories, {e['n_guilt']} + {i['n_guilt']} guilt stories; "
                     f"90% intervals: shame as guilt {e['ci_sg']} and {i['ci_sg']}",
            numbers={"datasets": rows}, n=sum(r["n_shame"] + r["n_guilt"] for r in rows),
            chart={"type": "bars2", "labels": [r["dataset"] for r in rows], "a": [r["shame_as_guilt"] for r in rows],
                   "b": [r["guilt_as_shame"] for r in rows], "a_label": "shame read as guilt",
                   "b_label": "guilt read as shame"},
            robustness="Same direction in both datasets, which differ in language, length and the list of options.",
            examples=ex, ids=used)
    return spec, run


INTENSE = [("furious", "angry"), ("terrified", "afraid"), ("devastated", "sad")]


def mild_words():
    spec = Spec(
        id="social_mild_emotions", family="social", title="Jev almost never calls anyone furious or terrified",
        question="When a feeling comes in a strong and a mild word (furious or angry, terrified or afraid, devastated "
                 "or sad), which one does Jev use?",
        why="Picking the milder word is a quiet form of downplaying. If Jev turns fury into anger and terror into "
            "fear, its summaries of how people feel will read calmer than the people wrote them.",
        sourcing="Existing EmpatheticDialogues questions: a short situation written by someone feeling one of 32 "
                 "named emotions, and Jev picks one of the 32. Three pairs of the same feeling at two strengths are "
                 "in the list. Enough: about 90 stories per label.",
        scoring="For each pair, the share of stories written under the strong word that Jev calls by the mild one, "
                "and the reverse; plus, over all 32 labels, how often Jev uses each word relative to how often "
                "writers did. 90% bootstrap intervals over stories.",
        chart="Paired bars per pair: strong read as mild vs mild read as strong; a ranked strip of the words Jev "
              "uses least relative to writers.",
        compared_with="The writers' own labels (the label they were asked to write about)",
        limits="Writers chose a label before writing, so a story under 'furious' may read as plain anger. The "
               "comparison is Jev's pick vs the prompt label, not vs other readers.",
        sources=["empathetic_dialogues"])

    def run():
        t = labeled("empathetic_dialogues")
        pairs = []
        for strong, mild in INTENSE:
            s2m, ns = _rate(t, strong, mild)
            m2s, nm = _rate(t, mild, strong)
            right, _ = _rate(t, strong, strong)
            sv = (t.filter(pl.col("truth") == strong)["jev"] == mild).cast(float).to_numpy()
            pairs.append({"strong": strong, "mild": mild, "strong_as_mild": s2m, "ci": boot(sv), "mild_as_strong": m2s,
                          "strong_right": right, "n_strong": ns, "n_mild": nm})
        used = Counter(t["jev"].to_list())
        written = Counter(t["truth"].to_list())
        ratio = sorted([{"label": k, "value": used[k] / written[k], "used": used[k], "written": written[k]}
                        for k in written], key=lambda x: x["value"])
        f = pairs[0]
        return Result(
            result=f"Of {f['n_strong']} stories written about feeling furious, Jev calls {f['strong_right']:.0%} furious "
                   f"and {f['strong_as_mild']:.0%} angry; of {pairs[1]['n_strong']} about feeling terrified, it calls "
                   f"{pairs[1]['strong_right']:.0%} terrified and {pairs[1]['strong_as_mild']:.0%} afraid. It rarely goes the "
                   f"other way ({f['mild_as_strong']:.0%} of angry stories called furious, {pairs[1]['mild_as_strong']:.0%} "
                   f"of afraid ones terrified). Devastated and sad are mixed up about equally both ways "
                   f"({pairs[2]['strong_as_mild']:.0%} and {pairs[2]['mild_as_strong']:.0%}).",
            evidence=f"{sum(p['n_strong'] + p['n_mild'] for p in pairs)} stories in the three pairs; 90% interval on "
                     f"furious read as angry {f['ci']}",
            numbers={"pairs": pairs, "use_ratio": ratio}, n=t.height,
            chart={"type": "bars2", "labels": [f"{p['strong']} / {p['mild']}" for p in pairs],
                   "a": [p["strong_as_mild"] for p in pairs], "b": [p["mild_as_strong"] for p in pairs],
                   "a_label": "strong word read as mild", "b_label": "mild word read as strong",
                   "strip": ratio[:8]},
            robustness="Across all 32 labels, the words Jev uses least relative to writers are "
                       + ", ".join(f"{x['label']} ({x['used']} uses for {x['written']} stories)" for x in ratio[:5]) + ".",
            examples=seeded(t.filter((pl.col("truth") == "furious") & (pl.col("jev") == "angry"))["id"].to_list(), "mild"))
    return spec, run


ISEAR = ["joy", "fear", "anger", "sadness", "disgust", "shame", "guilt"]


def isear_disgust():
    spec = Spec(
        id="social_disgust_as_anger", family="social", title="Jev reads disgust as anger",
        question="Across seven basic emotions in people's own stories, which does Jev recognize and which does it "
                 "mistake for another?",
        why="ISEAR is the classic cross-cultural record of what makes people feel each emotion. The emotions a "
            "reader confuses show what it thinks each feeling is about; disgust at someone's behavior and anger at "
            "it sit close together.",
        sourcing="Existing ISEAR questions (about 2,900 first-person stories from students in 37 countries, each "
                 "written about one of seven emotions); Jev picks one of the seven. Enough: about 400 per emotion.",
        scoring="The confusion table: for each emotion the writer named, the share Jev gives each label; the share "
                "right per emotion with 90% bootstrap intervals; how often Jev uses each label compared with writers.",
        chart="A heat table, writer's emotion (rows) by Jev's pick (columns), shares per row.",
        compared_with="The writers' own labels",
        limits="Stories are short and were translated; some were written in answer to a prompt for that emotion, "
               "so the label is what the writer was asked about.",
        sources=["isear"])

    def run():
        t = labeled("isear")
        cells, right = [], []
        for a in ISEAR:
            g = t.filter(pl.col("truth") == a)
            for b in ISEAR:
                cells.append({"p": a, "j": b, "share": float((g["jev"] == b).mean())})
            v = (g["jev"] == a).cast(float).to_numpy()
            right.append({"emotion": a, "right": float(v.mean()), "ci": boot(v), "n": g.height,
                          "used": int((t["jev"] == a).sum())})
        right.sort(key=lambda x: x["right"])
        da, n_d = _rate(t, "disgust", "anger")
        ad, _ = _rate(t, "anger", "disgust")
        lo, hi = right[0], right[-1]
        return Result(
            result=f"Jev names disgust in only {lo['right']:.0%} of stories written about disgust, the lowest of the "
                   f"seven; {da:.0%} of them it calls anger. Anger stories are called disgust {ad:.0%} of the time. "
                   f"Joy is easiest ({hi['right']:.0%}).",
            evidence=f"{t.height:,} stories; 90% interval on disgust named right {lo['ci']}",
            numbers={"right": right, "cells": cells}, n=t.height,
            chart={"type": "heat", "cells": cells, "x": "Jev's pick", "y": "writer's emotion", "order": ISEAR},
            robustness="Shame is the next hardest (" + next(f"{x['right']:.0%}" for x in right if x["emotion"] == "shame")
                       + " right; see social_shame_as_guilt). Jev uses sadness and "
                       f"anger more often than writers did ({next(x['used'] for x in right if x['emotion'] == 'sadness')} "
                       f"and {next(x['used'] for x in right if x['emotion'] == 'anger')} picks for about 410 stories each).",
            examples=seeded(t.filter((pl.col("truth") == "disgust") & (pl.col("jev") == "anger"))["id"].to_list(), "disg"))
    return spec, run


def story_emotion():
    spec = Spec(
        id="social_story_no_emotion", family="social", title="In a story, Jev often sees no feeling at all",
        question="Reading short everyday stories, how often does Jev say a character feels no clear emotion, "
                 "compared with the people who annotated them?",
        why="Reading feelings into plain events is most of what reading a story is. A reader that often answers "
            "'no clear emotion' is being literal where people infer.",
        sourcing="Existing StoryCommonsense questions (Rashkin et al. 2018): five-sentence stories, one character, "
                 "'Which emotion best describes ...' with Plutchik's eight emotions plus 'no clear emotion'; each "
                 "with three MTurk annotators' labels. Enough: about 3,000 story lines.",
        scoring="The average share each label gets from annotators vs Jev's average probability on it; how often "
                "Jev's top pick is 'no clear emotion' when at least two of the three annotators named the same real "
                "emotion. 90% bootstrap intervals over story lines.",
        chart="Paired bars over the nine labels: annotators vs Jev.",
        compared_with="StoryCommonsense MTurk annotators (three per story line)",
        limits="Annotators were asked to find an emotion, which may push them away from 'none'. Literal reading is "
               "on TypeSafe's own list of known weak spots (01-jev §6, item 1); this measures it on stories.",
        sources=["storycommonsense"])

    def run():
        q = source("storycommonsense").filter(pl.col("text").str.starts_with("Which emotion"))
        opts = list(js(q.row(0, named=True)["options"]))
        A, J, maj, ids = defaultdict(list), defaultdict(list), [], []
        for r in q.iter_rows(named=True):
            hd, jd = norm(biggest(r["humans"])["dist"]), norm(js(r["jev_dist"]))
            for k in opts:
                A[k].append(hd.get(k, 0))
                J[k].append(jd.get(k, 0))
            t = top(hd)
            if t != "no_clear_emotion" and hd[t] >= 0.6:
                none = top(jd) == "no_clear_emotion"
                maj.append(none)
                if none:
                    ids.append(r["id"])
        a = {k: float(np.mean(v)) for k, v in A.items()}
        j = {k: float(np.mean(v)) for k, v in J.items()}
        m = np.array(maj, dtype=float)
        order = sorted(opts, key=lambda k: -a[k])
        return Result(
            result=f"Jev puts {j['no_clear_emotion']:.0%} of its answer on 'no clear emotion'; annotators put "
                   f"{a['no_clear_emotion']:.0%} there. Even when two of three annotators agree on a feeling, Jev says "
                   f"there is none {m.mean():.0%} of the time. The feelings it drops most are trust ({j['trust']:.0%} vs "
                   f"{a['trust']:.0%}) and surprise ({j['surprise']:.0%} vs {a['surprise']:.0%}).",
            evidence=f"{q.height:,} story lines; {len(maj):,} with a two-of-three majority emotion, 90% interval {boot(m)}",
            numbers={"annotators": a, "jev": j, "majority_none": float(m.mean()), "n_majority": len(maj)}, n=q.height,
            chart={"type": "bars2", "labels": order, "a": [a[k] for k in order], "b": [j[k] for k in order],
                   "a_label": "annotators", "b_label": "Jev"},
            robustness="Measured against annotators, not the people in the stories. Where the writer's own feeling is known "
                       "(reading_writer_vs_readers), Jev's 'no particular emotion' matches writers who felt nothing much "
                       "more often than readers do, so part of this gap is readers projecting feelings.",
            examples=seeded(ids, "story"))
    return spec, run


# ---- Family Feud ---------------------------------------------------------------------------------------------------
def family_feud():
    spec = Spec(
        id="social_family_feud", family="social", title="Jev plays Family Feud like a quiz",
        question="Given the answers a Family Feud survey got ('Name something a knight needs for a jousting match'), "
                 "does Jev pick the one most people said first?",
        why="Family Feud rewards the most common answer, not the best one. Guessing it takes a model of ordinary "
            "people's first thoughts, which is different from knowing the right answer.",
        sourcing="Existing ProtoQA questions (Boratko et al. 2020, scraped Family Feud surveys of about 100 people): "
                 "'Which of these would most people name first' with the survey's answer clusters as options and "
                 "their counts as the human distribution. Enough for a clear rate, not for subgroups: 146 questions.",
        scoring="How often Jev's top pick is the survey's number one answer, against the chance rate (1 over the "
                "number of options); the rank of Jev's pick in the survey; the biggest misses, where the survey's "
                "favorite was far ahead. 90% bootstrap interval over questions.",
        chart="A bar of where Jev's pick ranked in the survey (1st to 6th), with the chance line; a list of the "
              "biggest misses.",
        compared_with="Family Feud survey respondents (about 100 per question)",
        limits="146 questions; answer clusters were grouped by ProtoQA's authors. The show's surveys are American.",
        sources=["protoqa"])

    def run():
        rows = []
        for r in source("protoqa").iter_rows(named=True):
            hd, jd = norm(biggest(r["humans"])["dist"]), norm(js(r["jev_dist"]))
            rk = sorted(hd, key=hd.get, reverse=True)
            m = re.search(r'"(.*)"', r["text"])
            rows.append({"id": r["id"], "q": (m.group(1) if m else r["text"]).rstrip(".?!"), "survey": rk[0], "survey_share": hd[rk[0]],
                         "jev": top(jd), "jev_share": hd[top(jd)], "rank": rk.index(top(jd)) + 1, "k": len(hd)})
        t = pl.DataFrame(rows)
        hit = (t["rank"] == 1).cast(float).to_numpy()
        chance = float((1 / t["k"]).mean())
        miss = t.with_columns((pl.col("survey_share") - pl.col("jev_share")).alias("gap")).sort("gap", descending=True)
        top3 = miss.head(3).to_dicts()
        ranks = [{"label": ["1st", "2nd", "3rd", "4th", "5th", "6th"][i], "value": float((t["rank"] == i + 1).mean())}
                 for i in range(int(t["rank"].max()))]
        return Result(
            result=f"Jev picks the survey's top answer on {hit.mean():.0%} of {t.height} Family Feud questions, against "
                   f"{chance:.0%} by chance. Its misses are sensible answers few people gave: "
                   + "; ".join(f"'{x['q']}' got {x['jev']} from Jev, {x['survey']} from {x['survey_share']:.0%} of people"
                               for x in top3) + ".",
            evidence=f"{t.height} questions; 90% interval {boot(hit)}; Jev's pick is in the survey's top two "
                     f"{float((t['rank'] <= 2).mean()):.0%} of the time",
            numbers={"hit": float(hit.mean()), "chance": chance, "ranks": ranks, "misses": miss.head(12).to_dicts()},
            n=t.height, chart={"type": "ranked", "items": ranks, "max": 1, "chance": chance},
            examples=[x["id"] for x in top3])
    return spec, run


# ---- values --------------------------------------------------------------------------------------------------------
RAW = Path("data/raw/daily_dilemmas/Dilemmas_with_values_aggregated.parquet")


def dilemma_values():
    spec = Spec(
        id="social_dilemma_values", family="social", title="In everyday dilemmas, loyalty loses",
        question="In 1,300 everyday dilemmas (report a colleague or not, tell a friend the truth or not), which values "
                 "does Jev's choice serve, and which does it give up?",
        why="Models are often said to share a set of values; dilemmas force a trade, which shows the order. A value "
            "that loses most head-to-heads is one the model will talk you out of.",
        sourcing="Existing DailyDilemmas questions (Chiu et al. 2024): two actions per dilemma, each tagged by the "
                 "dataset's authors with the values it serves (honesty, loyalty, self, responsibility...). The tags are "
                 "joined from the released data by the dilemma text. Enough: about 1,275 dilemmas matched.",
        scoring="For each value, its win rate: Jev's average probability on the action that carries it, over every "
                "dilemma where it appears on one side (at least 25 dilemmas); and head-to-heads: for two values on "
                "opposite sides, how often Jev takes the side of each (at least 25 dilemmas per pair).",
        chart="A ranked list of values by win rate, top and bottom; the head-to-heads with loyalty.",
        compared_with="Nothing outside the model: the value tags come from the dataset, the choices from Jev",
        limits="The value tags were written by a language model and checked by the authors; a tag names what an "
               "action serves, not how much. Dilemmas were generated, not collected from people.",
        sources=["daily_dilemmas"])

    def run():
        D = pl.read_parquet(RAW)
        tags = defaultdict(dict)
        for r in D.iter_rows(named=True):
            tags[r["dilemma_situation"].strip()][r["action"].strip().lower()] = set(ast.literal_eval(r["values_aggregated"]))
        win, pair, n = defaultdict(list), defaultdict(list), 0
        for r in source("daily_dilemmas").iter_rows(named=True):
            acts = tags.get(js(r["state"])["dilemma"].strip())
            labs = {k: v.strip().lower() for k, v in js(r["options"]).items()}
            if not acts or len(labs) != 2 or not all(l in acts for l in labs.values()):
                continue
            n += 1
            d = norm(js(r["jev_dist"]))
            (ka, la), (kb, lb) = labs.items()
            A, B = acts[la], acts[lb]
            for v in A:
                win[v].append(d[ka])
            for v in B:
                win[v].append(d[kb])
            for x in A - B:
                for y in B - A:
                    pair[(x, y)].append(d[ka])
                    pair[(y, x)].append(d[kb])
        ranked = sorted([{"label": v, "value": float(np.mean(p)), "n": len(p)} for v, p in win.items() if len(p) >= 25],
                        key=lambda x: -x["value"])
        loyal = sorted([{"vs": y, "loyalty": float(np.mean(p)), "n": len(p)} for (x, y), p in pair.items()
                        if x == "loyalty" and len(p) >= 20], key=lambda x: x["loyalty"])
        hl = {x["vs"]: x for x in loyal}
        ly = next(x for x in ranked if x["label"] == "loyalty")
        pos = [x["label"] for x in ranked].index("loyalty") + 1
        return Result(
            result=f"Loyalty is on the losing side of Jev's choices: the action that serves it gets {ly['value']:.0%} of "
                   f"Jev's weight on average, {pos}th of {len(ranked)} values; only {len(ranked) - pos} do worse, three of "
                   f"them kinds of lying. When loyalty is up against honesty, {hl['honesty']['loyalty']:.0%} of Jev's "
                   f"weight goes to loyalty; against accountability, {hl['accountability']['loyalty']:.0%}.",
            evidence=f"{n:,} dilemmas; loyalty on one side in {ly['n']}; head-to-heads: honesty {hl['honesty']['n']}, "
                     f"accountability {hl['accountability']['n']} dilemmas",
            numbers={"ranked": ranked, "loyalty_vs": loyal, "n": n}, n=n,
            chart={"type": "ranked", "items": ranked[:10], "bottom": ranked[-10:][::-1], "max": 1},
            robustness="Loyalty's head-to-heads (share of Jev's weight on the loyal side): "
                       + ", ".join(f"vs {x['vs']} {x['loyalty']:.0%}" for x in loyal[:6]) + ".",
            examples=[])
    return spec, run


# ---- reading situations ------------------------------------------------------------------------------------------
def siqa_types():
    spec = Spec(
        id="social_why_vs_what_next", family="social", title="Jev reads why people act better than what happens next",
        question="On 30,000 everyday social situations, does Jev read people's motives, their feelings, or what will "
                 "happen next best?",
        why="Explaining an action after the fact and predicting its consequences are different skills; the gap says "
            "which way Jev's social sense points.",
        sourcing="Existing Social IQa questions (Sap et al. 2019): a one-line situation and a question of one of "
                 "about ten types (why did X do this, what does X need to do before, how would X feel, what will "
                 "happen to X...), three answers, one marked right by crowd workers. Enough: 29,500 questions.",
        scoring="The share Jev gets right per question type, with 90% bootstrap intervals; grouped into looking back "
                "(motives, what was needed before), feelings and descriptions, and looking ahead (what happens next, "
                "what they will want next). Also Jev's stated probability against how often it is right.",
        chart="Dots per question type with intervals, ordered, colored by looking back / feelings / looking ahead.",
        compared_with="Social IQa's crowd-validated answers (people agreed with the marked answer about 87% of the "
                      "time in the original study)",
        limits="Answers are crowd-written, and some wrong answers are plausible; differences between types are a few "
               "points, so read them as a direction, not a gap in kind.",
        sources=["social_iqa"])

    GROUP = {"why did X do this?": "back", "what does X need to do before this?": "back",
             "what did X need to do before this?": "back", "what will happen to X?": "ahead",
             "what will happen to others?": "ahead", "what will X want to do next?": "ahead",
             "what will others want to do next?": "ahead"}

    def run():
        rows = []
        for r in source("social_iqa").iter_rows(named=True):
            m = re.search(r"`context`, (.*)$", r["text"])
            if not m:
                continue
            ty = re.sub(r"\b(?!Others\b)[A-Z][a-z]+\b", "X", m.group(1)).replace("Others", "others")
            d = norm(js(r["jev_dist"]))
            rows.append({"id": r["id"], "type": ty, "g": GROUP.get(ty, "feel"), "ok": top(d) == _truth(r),
                         "p": d[top(d)]})
        t = pl.DataFrame(rows)
        types = [{"label": ty, "value": float(g["ok"].mean()), "ci": boot(g["ok"].cast(float).to_numpy(), b=300),
                  "n": g.height, "group": g["g"][0]} for (ty,), g in t.group_by("type") if g.height >= 100]
        types.sort(key=lambda x: x["value"])
        grp = {k: t.filter(pl.col("g") == k)["ok"].cast(float).to_numpy() for k in ("back", "feel", "ahead")}
        rng = np.random.default_rng(3)
        ds = [rng.choice(grp["back"], grp["back"].size).mean() - rng.choice(grp["ahead"], grp["ahead"].size).mean()
              for _ in range(1000)]
        diff = [round(float(np.percentile(ds, 5)), 4), round(float(np.percentile(ds, 95)), 4)]
        cal = t.with_columns(pl.col("p").cut([0.7, 0.9, 0.99], labels=["under 70%", "70-90%", "90-99%", "99%+"]).alias("b")) \
               .group_by("b").agg(pl.col("p").mean().alias("stated"), pl.col("ok").mean().alias("right"), pl.len()).sort("b").to_dicts()
        return Result(
            result=f"Jev picks the crowd's answer {grp['back'].mean():.0%} of the time when asked why someone did "
                   f"something or what they needed first, and {grp['ahead'].mean():.0%} when asked what will happen or "
                   f"what they will want next; the hardest type is 'what will happen to X?' "
                   f"({next(x['value'] for x in types if x['label'] == 'what will happen to X?'):.0%}).",
            evidence=f"{t.height:,} questions; looking back minus looking ahead, 90% interval {diff}",
            numbers={"types": types, "groups": {k: float(v.mean()) for k, v in grp.items()}, "calibration": cal},
            n=t.height,
            chart={"type": "dots", "rows": [{"label": x["label"], "value": x["value"], "ci": x["ci"], "group": x["group"]}
                                            for x in types], "domain": [0.7, 1]},
            robustness="When Jev is 70-90% sure it is right " + next(f"{c['right']:.0%}" for c in cal if c["b"] == "70-90%")
                       + " of the time; when 99%+ sure, " + next(f"{c['right']:.0%}" for c in cal if c["b"] == "99%+") + ".",
            examples=seeded(t.filter((pl.col("type") == "what will happen to X?") & ~pl.col("ok"))["id"].to_list(), "siqa"))
    return spec, run


EXPERIMENTS = [shame_guilt(), mild_words(), isear_disgust(), story_emotion(), family_feud(), dilemma_values(),
               siqa_types()]
