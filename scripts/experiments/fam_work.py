"""Work experiments: Jev doing the Machine hemisphere's tasks (routing, checking, flagging, grading), read as
indicators of where its snap judgments can be trusted and which way they lean, never as a leaderboard.

Every question here has a right answer from the source dataset (or, for TypeSafe-style leaves with no public data,
the label its author decided while writing it; those are kept apart). Documented limits (docs/01-jev.md §6, e.g.
arithmetic) are labeled as known where they show up.
"""

from __future__ import annotations

import glob
import json
from collections import Counter
from functools import lru_cache

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, boot, js, level, seeded, table


@lru_cache(maxsize=1)
def graded() -> pl.DataFrame:
    """Machine questions with a right answer (public data and authored), Noul and Choice."""
    return table().filter((pl.col("hemisphere") == "machine") & pl.col("correct").is_not_null())


def public() -> pl.DataFrame:
    return graded().filter(~pl.col("source").is_in(["typesafe_authored", "typesafe_seeds"]))


L1 = {"support": "customer support", "legal": "legal", "healthcare": "healthcare", "trust_safety": "trust and safety",
      "finance": "finance", "research": "research", "documents": "documents", "commerce": "commerce",
      "ai_systems": "checking AI systems", "search": "search and retrieval", "code": "code", "people": "people and hiring",
      "education": "education", "operations": "operations and logs"}


def where_reliable():
    spec = Spec(
        id="work_task_not_domain", family="work", title="The task decides whether Jev is reliable, not the field",
        question="Across 120 kinds of machine work in 14 fields, does knowing the field (legal, code, healthcare...) "
                 "tell you how often Jev gets it right, or does it depend on the specific task?",
        why="Buyers pick a model per field ('is it good at legal?'). If reliability swings more between tasks inside a "
            "field than between fields, that question is the wrong one, and every new task needs its own check.",
        sourcing="Existing Machine-hemisphere questions from public labeled datasets with a right answer (Noul, "
                 "Choice), grouped by the tree's field (level 1) and by source task. Authored TypeSafe-style "
                 "questions are left out (their labels are the author's), and so are graded-scale tasks "
                 "(work_grading_scales). Enough: ~270,000 questions, 120+ tasks.",
        scoring="Per task, the share Jev gets right (its most likely answer equals the dataset's label). Per field, the "
                "pooled share with a 90% bootstrap interval over tasks, and the lowest and highest task in it. The "
                "share of the variance in task-level results that the field explains (between-field over total).",
        chart="One row per field: a dot at the pooled share, a line from its weakest to its strongest task, weakest "
              "and strongest named.",
        compared_with="each dataset's own labels (a right answer, not a crowd)",
        limits="A dataset's label is not always right, and harder datasets sit in some fields. "
               "Tasks differ in chance level (2 to 77 options). Indicators, not a ranking of fields.",
        sources=[])

    def run():
        q = public().filter(pl.col("primitive").is_in(["noul", "choice"]))
        by_src = q.group_by("l1", "source").agg(pl.len().alias("n"), pl.col("correct").mean().alias("acc")) \
                  .filter(pl.col("n") >= 200)
        rows = []
        for (l1,), g in by_src.group_by("l1"):
            g = g.sort("acc")
            accs = g["acc"].to_numpy()
            pooled = float(q.filter(pl.col("l1") == l1)["correct"].mean())
            rows.append({"label": L1.get(l1, l1), "value": pooled, "ci": boot(accs), "tasks": g.height,
                         "lo": {"task": g["source"][0], "name": TASK.get(g["source"][0], g["source"][0]), "value": float(accs[0])},
                         "hi": {"task": g["source"][-1], "name": TASK.get(g["source"][-1], g["source"][-1]), "value": float(accs[-1])}})
        rows.sort(key=lambda r: r["value"])
        a = by_src["acc"].to_numpy()
        means = by_src.group_by("l1").agg(pl.col("acc").mean().alias("m"))
        m = by_src.join(means, on="l1")["m"].to_numpy()
        between = float(((m - a.mean()) ** 2).sum() / ((a - a.mean()) ** 2).sum())
        widest = max(rows, key=lambda r: r["hi"]["value"] - r["lo"]["value"])
        return Result(
            result=f"The field explains only {between:.0%} of how reliable Jev is on a task; the rest is the task "
                   f"itself. Fields average between {rows[0]['value']:.0%} ({rows[0]['label']}) and "
                   f"{rows[-1]['value']:.0%} ({rows[-1]['label']}) right, but inside {widest['label']} alone the tasks "
                   f"run from {widest['lo']['value']:.0%} ({widest['lo']['name']}) to {widest['hi']['value']:.0%} "
                   f"({widest['hi']['name']}).",
            evidence=f"{q.height:,} questions from {by_src.height} tasks with 200+ questions, in {len(rows)} fields; "
                     "90% intervals over tasks",
            numbers={"fields": rows, "between_share": between, "tasks": by_src.sort("acc").to_dicts()},
            n=q.height,
            chart={"type": "range", "rows": rows, "domain": [0, 1], "x": "share right"},
            examples=seeded(q.filter(pl.col("source") == widest["lo"]["task"])["id"].to_list(), "task"), ids=q["id"].to_list())
    return spec, run


def calibration():
    spec = Spec(
        id="work_calibration", family="work", title="Honest on yes/no, overconfident when picking from a list",
        question="When Jev is 90% sure of an answer to a work task, is it right 90% of the time, and does that depend "
                 "on whether it answers yes/no or picks from options?",
        why="TypeSafe publishes no calibration numbers (docs/01-jev.md §6). A confidence you can take at face value "
            "is what lets a pipeline send only the unsure cases to a person.",
        sourcing="Existing Machine questions with a right answer from public datasets: yes/no (Noul) and "
                 "pick-one (Choice). Enough: ~275,000 questions.",
        scoring="Jev's probability on its chosen answer, binned (50-60%, ..., 99%+); in each bin the share right. "
                "Overconfidence = mean confidence minus share right, per primitive, with 90% bootstrap intervals over "
                "questions. The share right when Jev is 95%+ sure, by primitive and by field.",
        chart="A reliability diagram: confidence (x) vs share right (y), one line for yes/no and one for pick-one, "
              "with the diagonal.",
        compared_with="each dataset's own labels",
        limits="Dataset labels have their own error, which caps the share right in the top bins. Fields differ in "
               "task mix.", sources=[])

    def run():
        q = public().filter(pl.col("primitive").is_in(["noul", "choice"])).with_columns(
            pl.col("p_top").cut([0.6, 0.7, 0.8, 0.9, 0.95, 0.99], labels=["<60%", "60-70%", "70-80%", "80-90%",
                                                                         "90-95%", "95-99%", "99%+"]).alias("b"))
        lines, over = {}, {}
        for prim, g in q.group_by("primitive"):
            prim = prim[0]
            bins = g.group_by("b").agg(pl.len().alias("n"), pl.col("p_top").mean().alias("conf"),
                                       pl.col("correct").mean().alias("acc")).sort("b").to_dicts()
            lines[prim] = [{"label": b["b"], "conf": b["conf"], "acc": b["acc"], "n": b["n"]} for b in bins]
            d = (g["p_top"] - g["correct"].cast(float)).to_numpy()
            over[prim] = {"gap": float(d.mean()), "ci": boot(d, b=300), "n": g.height}
        sure = q.filter(pl.col("p_top") >= 0.95)
        s95 = {p: float(sure.filter(pl.col("primitive") == p)["correct"].mean()) for p in ("noul", "choice")}
        max99 = {p: float((q.filter(pl.col("primitive") == p)["p_top"] >= 0.99).mean()) for p in ("noul", "choice")}
        by_field = sure.group_by("l1").agg(pl.len().alias("n"), pl.col("correct").mean().alias("acc")).sort("acc").to_dicts()
        worst = by_field[0]
        return Result(
            result=f"On yes/no work Jev is close to honest: it overstates its confidence by {over['noul']['gap'] * 100:.0f} "
                   f"points on average. Picking from a list it overstates by {over['choice']['gap'] * 100:.0f}: it puts "
                   f"99%+ on {max99['choice']:.0%} of its picks (against {max99['noul']:.0%} of yes/no answers), and when 95%+ sure "
                   f"it is right {s95['choice']:.0%} of the time on picks vs {s95['noul']:.0%} on yes/no. In "
                   f"{L1.get(worst['l1'], worst['l1'])}, 95%+ sure means right {worst['acc']:.0%} of the time.",
            evidence=f"{q.height:,} questions; overconfidence 90% intervals: yes/no {over['noul']['ci']}, pick-one "
                     f"{over['choice']['ci']}",
            numbers={"lines": lines, "overconfidence": over, "sure_by_field": by_field, "right_at_95": s95,
                     "share_99": max99}, n=q.height,
            chart={"type": "reliability", "lines": lines, "diagonal": True, "x": "Jev's confidence", "y": "share right"},
            robustness=f"95%+ sure and right, by field: from {worst['acc']:.0%} ({L1.get(worst['l1'], worst['l1'])}) to "
                       f"{by_field[-1]['acc']:.0%} ({L1.get(by_field[-1]['l1'], by_field[-1]['l1'])}).",
            examples=seeded(sure.filter(~pl.col("correct") & (pl.col("primitive") == "choice"))["id"].to_list(), "cal"), ids=q["id"].to_list())
    return spec, run


# Yes/no tasks by what the question asks, and which answer is the "pass" (for flags: which answer raises the flag).
LEAN_GROUPS = {
    "Is this work good enough?": {"cola_grammar": True, "amazon_helpful": True, "op_spam_reviews": True,
                                  "gsm8k_verify": True, "semeval_sag": True, "swe_trajectories": True,
                                  "oasst_replies": False, "function_calls": True},
    "Is every claim supported?": {"faithdial": True, "halueval": True, "frank_factuality": True, "casehold_verify": True,
                                  "pubhealth_claims": True, "docstring_match": True, "commit_diff_match": True,
                                  "receipts_extract": True},
    "Are these a match?": {"clone_pairs": True, "poj_clones": True, "medical_question_pairs": True,
                           "paws_paraphrase": True, "sanctions_pairs": True, "people_docs": True,
                           "djinni_recruitment": True, "synergy_screening": True, "hotpot_gating": True,
                           "qnli_gating": True, "msmarco_relevance": True},
    "Is something wrong here?": {"bgl_alerts": True, "hdfs_sessions": True, "unfair_tos": True, "civil_comments": True,
                                 "conda_game_chat": True, "fake_job_posts": True, "fake_reviews": True,
                                 "code_defects": True, "code_review_need": True, "jailbreaks": True, "aegis_prompts": True,
                                 "unsafe_responses": True, "toxicchat": True, "wiki_attacks": True,
                                 "measuring_hate_speech": True, "youtube_spam": True, "sms_spam": True,
                                 "phishing_email": True, "hcv_labs": True},
}
NAMES = {"cola_grammar": "grammatical sentence", "amazon_helpful": "helpful product review",
         "op_spam_reviews": "genuine hotel review", "gsm8k_verify": "correct math answer (known limit)",
         "semeval_sag": "correct student answer", "swe_trajectories": "coding agent finished the task",
         "oasst_replies": "assistant reply does what was asked", "function_calls": "correct tool call",
         "faithdial": "dialogue reply sticks to its source", "halueval": "reply has no invented facts",
         "frank_factuality": "summary supported by the article", "casehold_verify": "right case holding",
         "pubhealth_claims": "health claim is true", "docstring_match": "docstring fits the code",
         "commit_diff_match": "commit message fits the diff", "receipts_extract": "value matches the receipt",
         "clone_pairs": "two methods do the same job", "poj_clones": "two programs solve the same problem",
         "medical_question_pairs": "same medical question", "paws_paraphrase": "same meaning",
         "sanctions_pairs": "same person on a sanctions list", "people_docs": "same product",
         "djinni_recruitment": "candidate fits the job", "synergy_screening": "paper belongs in the review",
         "hotpot_gating": "passage needed to answer", "qnli_gating": "passage answers the question",
         "msmarco_relevance": "passage answers the query", "bgl_alerts": "log line needs an admin",
         "hdfs_sessions": "storage block went wrong", "unfair_tos": "unfair contract clause",
         "civil_comments": "toxic comment", "conda_game_chat": "toxic game chat", "fake_job_posts": "scam job ad",
         "fake_reviews": "machine-written review", "code_defects": "security bug in code",
         "code_review_need": "diff needs a review comment", "jailbreaks": "jailbreak attempt",
         "aegis_prompts": "unsafe request", "unsafe_responses": "unsafe AI reply", "toxicchat": "toxic prompt",
         "wiki_attacks": "personal attack", "measuring_hate_speech": "hate speech", "youtube_spam": "YouTube spam",
         "sms_spam": "SMS spam", "phishing_email": "phishing email", "hcv_labs": "labs show liver disease"}

TASK = {**NAMES, "commit_messages": "commit message type", "code_lang": "programming language", "linkedin_jobs":
        "job posting field", "skillspan_jobs": "skill in a job ad", "dbpedia14": "encyclopedia topic",
        "emotion": "emotion in a tweet", "evidence_inference": "trial evidence", "hatexplain": "hate speech kind",
        "helpsteer2": "AI reply quality", "esci_attributes": "product attribute", "cfpb_complaints": "complaint topic",
        "ledgar": "contract clause type", "icd10_chapter": "diagnosis chapter", "drug_reviews": "drug review",
        "airline_complaints": "airline complaint", "multiwoz_domain": "travel dialogue domain",
        "loghub_lines": "log line type", "asap_essays": "essay grade", "dolly_tasks": "task type",
        "arxiv_screen": "paper topic"}


def lean():
    spec = Spec(
        id="work_which_way_it_errs", family="work", title="Which way Jev errs: lenient on quality, strict on matches, "
                                                          "jumpy on logs",
        question="When Jev gets a yes/no work check wrong, does it err in one direction, and does the direction "
                 "depend on what is being checked?",
        why="Knowing that a checker is 85% right is not enough to deploy it; knowing it waves through bad work, or "
            "cries wolf, tells you which side needs a second look.",
        sourcing="Existing yes/no Machine questions from 46 public labeled datasets, sorted by hand into four kinds "
                 "of question: is this work good enough, is every claim supported, are these two things a match, is "
                 "something wrong here. Enough: ~90,000 questions.",
        scoring="Per task, the lean: the share of items Jev passes (or, for 'is something wrong', flags) minus the "
                "share the labels pass (or flag). Positive = too many passes (or too many flags). Per kind, the mean "
                "lean over tasks with a 90% bootstrap interval over tasks.",
        chart="A dot plot, one row per task grouped under its kind, the lean around zero; the bad-case catch rate "
              "as a label on the extreme rows.",
        compared_with="each dataset's own labels",
        limits="The four kinds are a hand grouping. Some datasets are hard for people too (fake hotel reviews were "
               "near chance for human judges in the original study). Math checking is a documented limit "
               "(docs/01-jev.md §6), shown for completeness.", sources=[])

    def run():
        q = public().filter(pl.col("primitive") == "noul")
        rows, kinds = [], []
        for kind, tasks in LEAN_GROUPS.items():
            vals = []
            for src, pass_is_true in tasks.items():
                g = q.filter(pl.col("source") == src)
                if g.height < 200:
                    continue
                t = (g["truth"] == "true").to_numpy()
                j = (g["top"] == "true").to_numpy()
                if not pass_is_true:
                    t, j = ~t, ~j
                lean_ = float(j.mean() - t.mean())
                # catch rate on the cases that matter: fails for pass-questions, real problems for flags
                bad = ~t if kind != "Is something wrong here?" else t
                caught = float((j[bad] == t[bad]).mean()) if bad.any() else None
                rows.append({"kind": kind, "task": src, "label": NAMES[src], "value": lean_, "n": g.height,
                             "says": float(j.mean()), "base": float(t.mean()),
                             "caught": caught, "right": float(g["correct"].mean())})
                vals.append(lean_)
            kinds.append({"kind": kind, "lean": float(np.mean(vals)), "ci": boot(vals), "tasks": len(vals)})
        R = {r["task"]: r for r in rows}
        spam, math_, clone, hdfs = R["op_spam_reviews"], R["gsm8k_verify"], R["clone_pairs"], R["hdfs_sessions"]
        k = {x["kind"]: x for x in kinds}
        return Result(
            result=f"Asked whether work is good enough, Jev leans toward yes ({k['Is this work good enough?']['lean']:+.2f} "
                   f"on average): it calls {spam['says']:.0%} of hotel reviews genuine and catches only "
                   f"{spam['caught']:.0%} of the fakes, and passes {1 - math_['caught']:.0%} of wrong math answers (a "
                   f"known limit). Asked whether two things match, it leans toward no "
                   f"({k['Are these a match?']['lean']:+.2f}): it says two methods do the same job for {clone['says']:.0%} "
                   f"of code pairs when {clone['base']:.0%} do. On server logs it cries wolf, calling {hdfs['says']:.0%} "
                   f"of storage blocks failed when {hdfs['base']:.0%} are.",
            evidence=f"{sum(r['n'] for r in rows):,} yes/no questions from {len(rows)} tasks; per-kind 90% intervals over "
                     "tasks: " + "; ".join(f"{x['kind']} {x['lean']:+.2f} {x['ci']}" for x in kinds),
            numbers={"tasks": rows, "kinds": kinds}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "rows": [{"label": r["label"], "group": r["kind"], "value": r["value"]}
                                            for r in sorted(rows, key=lambda r: (r["kind"], r["value"]))], "zero": 0,
                   "x": "lean (too many passes or flags, +)"},
            examples=seeded(q.filter((pl.col("source") == "op_spam_reviews") & ~pl.col("correct"))["id"].to_list(), "lean"), ids=q.filter(pl.col("source").is_in([r["task"] for r in rows]))["id"].to_list())
    return spec, run


ROUTING = ["banking77", "hwu64_intents", "massive_en", "clinc150", "snips_intents", "multiwoz_domain", "sgd_dialogue",
           "cfpb_complaints", "abcd_flows", "airline_complaints", "skill_select", "math_routing", "dolly_tasks"]


def routing():
    spec = Spec(
        id="work_routing_misses", family="work", title="When Jev misroutes, the right answer is usually next door",
        question="When Jev sends a customer message to the wrong intent, how wrong is it: a neighbor of the right "
                 "intent, or somewhere else entirely, and does a longer list of intents make it worse?",
        why="Routing is TypeSafe's bread-and-butter use case. A miss between 'order a physical card' and 'get a "
            "physical card' costs little; a miss to an unrelated team costs a lot, and a right answer in second "
            "place means a two-choice fallback would recover it.",
        sourcing="Existing intent and topic routing questions from 13 public datasets (banking, assistants, "
                 "complaints, support flows, tools, task types) with 7 to 77 options each. Enough: ~30,000 questions.",
        scoring="Per dataset: share right; among misses, the share where the right intent was Jev's second choice; the "
                "most frequent confusions. Across datasets, rank correlation between the number of options and the "
                "share right.",
        chart="Paired bars per dataset (ordered by number of options): share right, and the share of misses where "
              "the answer was second choice; the top confusions as labels.",
        compared_with="each dataset's own labels",
        limits="Datasets differ in how distinct their intents are; some labels are ambiguous (e.g. 'brainstorming' "
               "vs 'open question' in the Dolly task types).", sources=ROUTING)

    def run():
        q = public().filter(pl.col("source").is_in(ROUTING) & (pl.col("primitive") == "choice"))
        rows = []
        for src in ROUTING:
            g = q.filter(pl.col("source") == src)
            if g.height < 200:
                continue
            second, conf, ks = [], Counter(), []
            for r in g.iter_rows(named=True):
                d = js(r["jev_dist"])
                ks.append(len(d))
                if not r["correct"]:
                    tr = json.loads(r["truth"])
                    order = sorted(d, key=d.get, reverse=True)
                    second.append(len(order) > 1 and order[1] == tr)
                    conf[(tr, order[0])] += 1
            rows.append({"label": src, "options": float(np.mean(ks)), "right": float(g["correct"].mean()),
                         "second": float(np.mean(second)), "misses": len(second), "n": g.height,
                         "confusions": [{"truth": a, "jev": b, "n": c} for (a, b), c in conf.most_common(3)]})
        rows.sort(key=lambda r: r["options"])
        rho = spearmanr([r["options"] for r in rows], [r["right"] for r in rows]).statistic
        misses = sum(r["misses"] for r in rows)
        sec = sum(r["second"] * r["misses"] for r in rows) / misses
        b77 = next(r for r in rows if r["label"] == "banking77")
        c = b77["confusions"][1]
        return Result(
            result=f"When Jev misroutes, the right intent is its second choice {sec:.0%} of the time, and the typical "
                   f"miss is a sibling ('{c['truth'].replace('_', ' ')}' sent to '{c['jev'].replace('_', ' ')}'). A "
                   f"longer menu barely matters: with 77 banking intents it is right {b77['right']:.0%} of the time, "
                   f"and across 13 datasets the number of options and the share right are {agree_word(abs(rho))} "
                   f"related (rank correlation {rho:.2f}).",
            evidence=f"{q.height:,} routing questions, {misses:,} misses, 13 datasets with 7-77 options",
            numbers={"datasets": rows, "second_share": sec, "rho_options": rho}, n=q.height,
            chart={"type": "bars2", "labels": [f"{r['label']} ({r['options']:.0f})" for r in rows],
                   "a": [r["right"] for r in rows], "b": [r["second"] for r in rows],
                   "a_label": "right", "b_label": "misses where the answer was 2nd choice"},
            examples=seeded(q.filter((pl.col("source") == "banking77") & ~pl.col("correct"))["id"].to_list(), "route"))
    return spec, run


@lru_cache(maxsize=1)
def borderline_flags() -> dict:
    out = {}
    for f in glob.glob("authored/machine_inputs/*.jsonl"):
        for line in open(f):
            r = json.loads(line)
            out[json.dumps(r["state"], sort_keys=True)] = bool(r.get("borderline"))
    return out


def borderline():
    spec = Spec(
        id="work_knows_hard_cases", family="work", title="Jev gets less sure on the cases that are genuinely borderline",
        question="On work cases written to be deliberately borderline, does Jev's confidence drop, or is it as sure as "
                 "on the clear ones?",
        why="A model that knows when a case is hard can hand exactly those to a person. Public datasets don't mark "
            "which cases are borderline; the questions written for this project in TypeSafe's style do.",
        sourcing="Existing authored questions for TypeSafe's Machine leaves with no public data (claims triage, "
                 "KYC, ad alignment, listing compliance, moderation enforcement, response verification, prohibited "
                 "claims, methods checks, hiring evidence, purchase intent): 7,450 inputs written by hand, about 30% "
                 "marked borderline at writing time. Plus the examples in TypeSafe's own docs, and public data for "
                 "contrast. Enough.",
        scoring="Share right and share of answers at 95%+ confidence for clear vs borderline cases, per primitive, "
                "with 90% bootstrap intervals; the same for the docs' own examples and for public datasets.",
        chart="Paired bars: share right and share 95%+ sure, for docs examples, clear authored, borderline authored "
              "and public data.",
        compared_with="the author's labels (authored), the docs' answers, and public datasets' labels",
        limits="Authored labels are the author's judgment, not independent ground truth, and the author knew which "
               "cases were borderline. The docs examples are few (a few hundred).",
        sources=["typesafe_authored", "typesafe_seeds"])

    def run():
        flags = borderline_flags()
        a = graded().filter(pl.col("source") == "typesafe_authored")
        a = a.with_columns(pl.Series("bl", [flags.get(json.dumps(json.loads(s), sort_keys=True)) if s else None
                                            for s in a["state"]]))
        a = a.filter(pl.col("bl").is_not_null() & pl.col("primitive").is_in(["noul", "choice"]))
        seeds = graded().filter((pl.col("source") == "typesafe_seeds") & pl.col("primitive").is_in(["noul", "choice"]))
        pub = public().filter(pl.col("primitive").is_in(["noul", "choice"]))

        def stat(g, label):
            c, s = g["correct"].cast(float).to_numpy(), (g["p_top"] >= 0.95).cast(float).to_numpy()
            return {"label": label, "n": g.height, "right": float(c.mean()), "right_ci": boot(c, b=300),
                    "sure": float(s.mean()), "sure_ci": boot(s, b=300)}
        groups = [stat(seeds, "TypeSafe docs examples"), stat(a.filter(~pl.col("bl")), "clear (authored)"),
                  stat(a.filter(pl.col("bl")), "borderline (authored)"), stat(pub, "public datasets")]
        by_prim = {p: {k: stat(a.filter((pl.col("primitive") == p) & (pl.col("bl") == (k == "borderline"))), k)
                       for k in ("clear", "borderline")} for p in ("noul", "choice")}
        cl, bl = groups[1], groups[2]
        return Result(
            result=f"On cases written to be borderline, Jev is 95%+ sure only {bl['sure']:.0%} of the time, against "
                   f"{cl['sure']:.0%} on clear ones, and it is right {bl['right']:.0%} vs {cl['right']:.0%}. The "
                   f"examples in TypeSafe's docs sit at the easy end ({groups[0]['right']:.0%} right); public datasets "
                   f"at {groups[3]['right']:.0%}.",
            evidence=f"{a.height:,} authored questions ({bl['n']:,} borderline); 90% intervals: sure on borderline "
                     f"{bl['sure_ci']}, on clear {cl['sure_ci']}",
            numbers={"groups": groups, "by_primitive": by_prim}, n=a.height + seeds.height,
            chart={"type": "bars2", "labels": [g["label"] for g in groups], "a": [g["right"] for g in groups],
                   "b": [g["sure"] for g in groups], "a_label": "right", "b_label": "95%+ sure"},
            robustness=f"Yes/no: 95%+ sure {by_prim['noul']['borderline']['sure']:.0%} borderline vs "
                       f"{by_prim['noul']['clear']['sure']:.0%} clear; pick-one: {by_prim['choice']['borderline']['sure']:.0%} "
                       f"vs {by_prim['choice']['clear']['sure']:.0%}.",
            examples=seeded(a.filter(pl.col("bl"))["id"].to_list(), "bl"))
    return spec, run


SCALES = {"stsb_similarity": "sentence similarity", "amazon_reviews": "star rating from a review text",
          "wine_notes": "wine score from tasting notes", "esco_titles": "job title match",
          "wands_relevance": "product search relevance", "wikibio_hallucination": "hallucination in a biography",
          "djinni_recruitment": "candidate-job fit", "trec_covid": "COVID paper relevance",
          "esci_rerank": "shopping search relevance", "helpsteer2": "helpfulness of an AI reply",
          "asap_essays": "student essay grade"}


def scales():
    spec = Spec(
        id="work_grading_scales", family="work", title="Jev ranks on a scale well but rarely hits the exact grade, "
                                                       "and grades student essays low",
        question="When a work task asks for a level on a scale (a relevance grade, a star rating, an essay score), "
                 "does Jev put items in the right order, hit the exact level, and use the scale the way the labels do?",
        why="Graded judgments are how models get used for ranking and review. Order right but levels off means it is "
            "useful for sorting and not for thresholds; a shifted scale means every threshold needs re-tuning.",
        sourcing="Existing Score questions from 11 public labeled datasets with a graded answer (3-6 levels). "
                 "Enough: ~17,000 questions.",
        scoring="Per task: rank correlation between Jev's expected level and the label (90% bootstrap interval); "
                "share at the exact level and within one level (Jev's most likely level); mean level of Jev's most "
                "likely answer vs the labels'.",
        chart="A dot plot per task: rank correlation, with the exact-level share as a label; the essay task marked.",
        compared_with="each dataset's graded labels",
        limits="Level wordings are ours (described situations), the labels' scales were theirs; comparing mean levels "
               "assumes the mapping is fair.", sources=list(SCALES))

    def run():
        q = public().filter((pl.col("primitive") == "score") & pl.col("source").is_in(list(SCALES)))
        rows = []
        for src, name in SCALES.items():
            g = q.filter(pl.col("source") == src)
            pairs = []
            for r in g.iter_rows(named=True):
                t = js(r["truth"])
                d = js(r["jev_dist"])
                if isinstance(t, (int, float)) and d:
                    pairs.append((float(t), level(d), float(max(d, key=d.get)), len(d)))
            if len(pairs) < 200:
                continue
            p = np.array(pairs)
            idx = np.arange(len(p))
            rho = spearmanr(p[:, 0], p[:, 1]).statistic
            ci = boot(idx, stat=lambda ii: spearmanr(p[ii.astype(int), 0], p[ii.astype(int), 1]).statistic, b=200)
            rows.append({"label": name, "task": src, "value": float(rho), "ci": ci, "n": len(p), "levels": int(p[0, 3]),
                         "exact": float((p[:, 0] == p[:, 2]).mean()), "within1": float((abs(p[:, 0] - p[:, 2]) <= 1).mean()),
                         "mean_label": float(p[:, 0].mean()), "mean_jev": float(p[:, 2].mean())})
        rows.sort(key=lambda r: r["value"])
        ess = next(r for r in rows if r["task"] == "asap_essays")
        med_rho = float(np.median([r["value"] for r in rows]))
        med_exact = float(np.median([r["exact"] for r in rows]))
        return Result(
            result=f"On graded work Jev orders items well (median rank correlation {med_rho:.2f} with the labels, "
                   f"{rows[-1]['value']:.2f} on {rows[-1]['label']}) but lands on the exact level only "
                   f"{med_exact:.0%} of the time. The outlier is student essays: it ranks them {agree_word(ess['value'])} "
                   f"({ess['value']:.2f}) and grades them lower than the teachers did ({ess['mean_jev']:.1f} vs "
                   f"{ess['mean_label']:.1f} on a 0-{ess['levels'] - 1} scale).",
            evidence=f"{sum(r['n'] for r in rows):,} graded questions in {len(rows)} tasks; 90% intervals over items",
            numbers={"tasks": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "rows": [{"label": r["label"], "value": r["value"], "ci": r["ci"],
                                             "note": f"exact {r['exact']:.0%}", "hi": r["task"] == "asap_essays"}
                                            for r in rows], "domain": [0, 1], "x": "rank correlation with the labels"},
            examples=seeded(q.filter(pl.col("source") == "asap_essays")["id"].to_list(), "ess"))
    return spec, run


EXPERIMENTS = [where_reliable(), calibration(), lean(), routing(), borderline(), scales()]
