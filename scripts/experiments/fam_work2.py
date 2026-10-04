"""More work experiments (round 4): the Machine-hemisphere sources fam_work.py doesn't use, each read for one specific
pattern in how Jev does that job. Indicators, never a leaderboard; every question has the dataset's own label.

fam_work.py already covers reliability by task, calibration, which way it leans on quality/matching/logs, routing
misses, borderline cases and graded scales; these don't repeat them. Documented limits (docs/01-jev.md §6) are
labeled as known where they show up.
"""

from __future__ import annotations

from functools import lru_cache

import polars as pl

from lib import Result, Spec, and_list, boot, js, norm, seeded, with_meta


@lru_cache(maxsize=64)
def rows(source: str) -> pl.DataFrame:
    """One row per shown question: template, the label, Jev's top answer, right or wrong, P(yes), and flat meta."""
    out = []
    for r in with_meta(source):
        t = js(r["truth"]) if isinstance(r["truth"], str) else r["truth"]
        d = norm(js(r["jev_dist"]) or {})
        m = {f"m_{k}": str(v) for k, v in (r["m"] or {}).items() if isinstance(v, (str, int, float, bool))}
        out.append({"id": r["id"], "tpl": r["template_id"], "truth": str(t).lower(), "top": r["top"],
                    "ok": bool(r["correct"]), "py": d.get("true"), **m})
    return pl.DataFrame(out, infer_schema_length=None).sort("id")


def rate(d: pl.DataFrame, cond) -> float:
    x = d.filter(cond)
    return float(x["ok"].mean()) if x.height else float("nan")


def miss_fa(d: pl.DataFrame) -> tuple[float, float, int, int]:
    """Share of true cases Jev says no to (miss) and false cases it says yes to (false alarm)."""
    pos, neg = d.filter(pl.col("truth") == "true"), d.filter(pl.col("truth") == "false")
    return 1 - float(pos["ok"].mean()), 1 - float(neg["ok"].mean()), pos.height, neg.height


# ---- 1. legal ---------------------------------------------------------------------------------------------------------
def legal():
    spec = Spec(
        id="work_legal_misses_present", family="work",
        title="In contracts and case law, Jev misses what's there more than it invents what isn't",
        question="Asked whether a contract contains a given provision, whether an opinion overrules a case, or whether a "
                 "policy segment covers a data practice, which way does Jev go wrong?",
        why="In legal review a missed clause and an invented one cost different things: a miss can sink a deal, a false "
            "flag costs a lawyer's minute. Knowing the direction says how to use the model.",
        sourcing="Existing LegalBench yes/no tasks (CUAD contract provisions, overruling, privacy-policy practices, "
                 "legal area, definitions, consumer contracts), balanced about 50/50 by the dataset, plus CaseHOLD "
                 "holdings and ContractNLI. Enough: about 13,000 questions.",
        scoring="Per task, the share of real cases Jev says no to (misses) and of absent cases it says yes to (false "
                "alarms), with 90% bootstrap intervals; the CUAD provision types it misses most.",
        chart="Paired bars per task: misses vs false alarms.",
        compared_with="each dataset's own labels",
        limits="LegalBench labels were written by lawyers and law students; CUAD excerpts are short, so some provisions "
               "depend on context the excerpt leaves out.",
        sources=["legalbench", "casehold_verify", "contract_nli"])

    def run():
        d = rows("legalbench").filter(pl.col("truth").is_in(["true", "false"]))
        names = {"legalbench.cuad_provision": "contract provisions (CUAD)", "legalbench.overruling": "overruling",
                 "legalbench.privacy_practice": "privacy-policy practices", "legalbench.legal_area": "legal area",
                 "legalbench.definition": "definitions", "legalbench.consumer_contracts_qa": "consumer contracts"}
        out = []
        for tpl, lab in names.items():
            g = d.filter(pl.col("tpl") == tpl)
            if g.height < 100:
                continue
            m, f, npos, nneg = miss_fa(g)
            out.append({"label": lab, "miss": m, "fa": f, "n": g.height})
        ch = rows("casehold_verify")
        m, f, _, _ = miss_fa(ch)
        out.append({"label": "case holdings (CaseHOLD)", "miss": m, "fa": f, "n": ch.height})
        cuad = d.filter((pl.col("tpl") == "legalbench.cuad_provision") & (pl.col("truth") == "true"))
        by = cuad.group_by("m_task").agg(pl.col("ok").mean(), pl.len()).filter(pl.col("len") >= 20).sort("ok", "m_task").to_dicts() \
            if "m_task" in cuad.columns else []
        c = next(o for o in out if o["label"].startswith("contract"))
        o = next(o for o in out if o["label"] == "overruling")
        worse = [x for x in out if x["miss"] > x["fa"]]
        miss_all = 1 - float(d.filter(pl.col("truth") == "true")["ok"].mean())
        fa_all = 1 - float(d.filter(pl.col("truth") == "false")["ok"].mean())
        pretty = lambda t: t.replace("cuad_", "").replace("_", " ")  # noqa: E731
        return Result(
            result=f"Jev misses real contract provisions {c['miss']:.0%} of the time but flags absent ones only "
                   f"{c['fa']:.0%}; it misses {o['miss']:.0%} of real overrulings and invents {o['fa']:.0%}. In "
                   f"{len(worse)} of {len(out)} legal tasks misses outnumber false alarms. The provisions it misses most: "
                   + and_list([f"{pretty(b['m_task'])} ({1 - b['ok']:.0%})" for b in by[:3]]) + ".",
            evidence=f"{d.height:,} LegalBench and {ch.height:,} CaseHOLD questions; across LegalBench, misses "
                     f"{miss_all:.0%} vs false alarms {fa_all:.0%}",
            numbers={"tasks": out, "cuad_types": by}, n=d.height + ch.height,
            chart={"type": "bars2", "labels": [x["label"] for x in out], "a": [x["fa"] for x in out],
                   "b": [x["miss"] for x in out], "a_label": "false alarms (flags what isn't there)",
                   "b_label": "misses (says no to what is there)"},
            examples=seeded(cuad.filter(~pl.col("ok"))["id"].to_list(), "legal"))
    return spec, run


# ---- 2. hallucination detection ------------------------------------------------------------------------------------------
def hallucination():
    spec = Spec(
        id="work_hallucination_checks", family="work",
        title="Checking for invented facts: Jev catches the blatant ones, flags honest chat, misses the subtle",
        question="Asked whether a chatbot reply, an answer or a summary sticks to its source, how often does Jev catch "
                 "the invented ones, how often does it accuse faithful ones, and does it catch errors that are only "
                 "partly wrong?",
        why="Hallucination checking is one of the jobs a small, cheap model is most likely to be given. A checker that "
            "misses subtle errors or rejects honest replies costs trust in both directions.",
        sourcing="Existing questions from HaluEval (dialogue, QA and summarization; half with an injected fabrication), "
                 "FaithDial (knowledge-grounded dialogue) and FRANK (machine-written news summaries annotated sentence by "
                 "sentence). Enough: about 7,000 questions.",
        scoring="Per set, the share of unfaithful items Jev catches and of faithful items it wrongly flags, with 90% "
                "intervals. For FRANK, catches split by how much of the summary is wrong (every sentence unsupported vs "
                "only some).",
        chart="Paired bars per set: caught vs wrongly flagged.",
        compared_with="each dataset's own labels",
        limits="HaluEval's fabrications were generated by a model on purpose; FRANK's errors are real ones from "
               "summarizers. 'Only some sentences wrong' is FRANK's sentence-level factuality above zero, and it is "
               "mostly CNN/DailyMail summaries while the entirely unsupported ones are mostly BBC (XSum), so part of "
               "the gap may be the source.",
        sources=["halueval", "faithdial", "frank_factuality"])

    def run():
        out = []
        h = rows("halueval")
        for tpl, lab in [("halueval.dialogue", "HaluEval dialogue"), ("halueval.qa", "HaluEval QA"),
                         ("halueval.summarization", "HaluEval summaries")]:
            g = h.filter(pl.col("tpl") == tpl)
            m, f, _, _ = miss_fa(g)
            # "true" = faithful: a miss here is accusing a faithful reply; a false alarm is passing a fabrication
            out.append({"label": lab, "caught": 1 - f, "accused": m, "n": g.height})
        fd = rows("faithdial")
        m, f, _, _ = miss_fa(fd)
        out.append({"label": "FaithDial dialogue", "caught": 1 - f, "accused": m, "n": fd.height})
        fr = rows("frank_factuality")
        m, f, _, _ = miss_fa(fr)
        out.append({"label": "FRANK summaries", "caught": 1 - f, "accused": m, "n": fr.height})
        bad = fr.filter(pl.col("truth") == "false").with_columns(pl.col("m_sentence_factuality").cast(pl.Float64, strict=False).alias("sf"))
        blatant = float(bad.filter(pl.col("sf") <= 0)["ok"].mean())
        subtle = float(bad.filter(pl.col("sf") > 0)["ok"].mean())
        nb, ns = bad.filter(pl.col("sf") <= 0).height, bad.filter(pl.col("sf") > 0).height
        dia = out[0]
        return Result(
            result=f"Jev catches {dia['caught']:.0%} of invented facts in chatbot replies but accuses {dia['accused']:.0%} "
                   f"of the faithful ones (FaithDial: {out[3]['caught']:.0%} caught, {out[3]['accused']:.0%} accused). "
                   f"In machine-written news summaries it catches {blatant:.0%} of those where no sentence is supported, "
                   f"but only {subtle:.0%} of those where just some are wrong.",
            evidence=f"{h.height:,} HaluEval, {fd.height:,} FaithDial and {fr.height:,} FRANK questions; FRANK wrong "
                     f"summaries: {nb} entirely unsupported, {ns} partly; 90% interval on the partly-wrong catch rate "
                     f"{boot(bad.filter(pl.col('sf') > 0)['ok'].cast(float).to_numpy())}",
            numbers={"sets": out, "frank_blatant": blatant, "frank_subtle": subtle}, n=h.height + fd.height + fr.height,
            chart={"type": "bars2", "labels": [x["label"] for x in out], "a": [x["accused"] for x in out],
                   "b": [x["caught"] for x in out], "a_label": "faithful replies flagged", "b_label": "fabrications caught"},
            robustness="HaluEval QA shows the opposite balance (it passes more fabrications than it accuses faithful "
                       "answers), so the strictness is specific to dialogue, not a general yes/no lean.",
            examples=seeded(h.filter((pl.col("tpl") == "halueval.dialogue") & ~pl.col("ok") & (pl.col("truth") == "true"))["id"].to_list(), "halu"))
    return spec, run


# ---- 3. evidence verdicts -------------------------------------------------------------------------------------------------
NEUTRAL = {"fever_claims": ("not_enough_info", "FEVER fact checks"), "vitaminc_evidence": ("does_not_decide", "VitaminC edits"),
           "scifact": ("says_nothing", "SciFact science claims"), "anli_grounding": ("left_open", "Adversarial NLI"),
           "mnli_grounding": ("neither", "MultiNLI"), "contract_nli": ("not_mentioned", "ContractNLI"),
           "evidence_inference": ("no_significant_difference", "clinical trial results")}


def evidence():
    spec = Spec(
        id="work_evidence_retreat", family="work", title="When Jev misreads evidence, it says 'can't tell', not the opposite",
        question="On fact-checking and grounding tasks with three answers (supports, contradicts, can't tell), when Jev "
                 "gets a clear case wrong, does it flip to the opposite verdict or retreat to 'can't tell'?",
        why="A checker that errs toward 'not enough information' sends cases to a human; one that errs toward the "
            "opposite verdict certifies falsehoods. The direction of errors matters more than their count.",
        sourcing="Existing three-way questions from FEVER, VitaminC, SciFact, Adversarial NLI, MultiNLI, ContractNLI and "
                 "Evidence Inference (clinical trials), each with the dataset's label. Enough: about 13,000 questions.",
        scoring="Per set, accuracy on clear cases (supports or contradicts), the share of their errors that went to "
                "'can't tell' vs to the opposite verdict, and how often Jev recognizes a genuine 'can't tell'. Adversarial "
                "NLI by round (later rounds were written to fool models).",
        chart="Bars per set: the share of errors on clear cases that retreat to 'can't tell'.",
        compared_with="each dataset's own labels",
        limits="The 'can't tell' class is defined differently per dataset (not enough info, no significant difference, "
               "not mentioned).",
        sources=list(NEUTRAL))

    def run():
        out = []
        for s, (neu, lab) in NEUTRAL.items():
            d = rows(s)
            clear = d.filter(pl.col("truth") != neu)
            err = clear.filter(~pl.col("ok"))
            out.append({"label": lab, "clear_acc": float(clear["ok"].mean()), "retreat": float((err["top"] == neu).mean()),
                        "neutral_recall": rate(d, pl.col("truth") == neu), "errors": err.height, "n": d.height})
        out.sort(key=lambda x: -x["retreat"])
        tot_err = sum(x["errors"] for x in out)
        pooled = sum(x["retreat"] * x["errors"] for x in out) / tot_err
        most = [x for x in out if x["retreat"] > 0.5]
        a = rows("anli_grounding")
        rounds = a.group_by("m_round").agg(pl.col("ok").mean()).sort("m_round").to_dicts()
        return Result(
            result=f"When Jev gets a clear-cut case wrong, {pooled:.0%} of its errors retreat to 'can't tell' rather than "
                   f"the opposite verdict; in {len(most)} of 7 sets most do, up to {out[0]['retreat']:.0%} on "
                   f"{out[0]['label']}. The exceptions are {out[-1]['label']} ({out[-1]['retreat']:.0%}) and "
                   f"{out[-2]['label']} ({out[-2]['retreat']:.0%}), where a wrong answer is usually the opposite one.",
            evidence=f"{sum(x['n'] for x in out):,} questions, {tot_err:,} errors on clear cases",
            numbers={"sets": out, "pooled_retreat": pooled, "anli_rounds": rounds}, n=sum(x["n"] for x in out),
            chart={"type": "bars", "rows": [{"label": x["label"], "value": x["retreat"]} for x in out], "domain": [0, 1],
                   "unit": "share of errors on clear cases that went to 'can't tell'"},
            robustness="Adversarial NLI gets harder by round, as designed to fool models: "
                       + ", ".join(f"round {r['m_round'][-1]} {r['ok']:.0%}" for r in rounds) + " right.")
    return spec, run


# ---- 4. abuse ------------------------------------------------------------------------------------------------------------
ABUSE = [("sms_spam", "sms.spam", "spam texts"), ("phishing_email", None, "spam and phishing email"),
         ("youtube_spam", None, "YouTube comment spam"), ("pii_detect", "pii_detect.contains_pii", "personal data"),
         ("aegis_prompts", "aegis.prompt_unsafe", "unsafe prompts"), ("unsafe_responses", "unsafe_responses.unsafe", "unsafe AI replies"),
         ("jailbreaks", None, "jailbreak prompts"), ("fake_job_posts", None, "fake job ads")]


def abuse():
    spec = Spec(
        id="work_new_abuse", family="work", title="Familiar spam is easy for Jev; jailbreaks, unsafe replies and fake jobs slip through",
        question="Across spam, phishing, personal data, unsafe prompts, unsafe AI replies, jailbreaks and fake job ads, "
                 "which kinds of abuse does Jev miss, and does it make up for it with false alarms?",
        why="Trust-and-safety filters are an obvious job for a fast classifier. The question isn't overall accuracy but "
            "which threats get through.",
        sourcing="Existing yes/no questions from the SMS Spam Collection, a phishing email corpus, YouTube Spam, a PII "
                 "corpus, Aegis (unsafe prompts), BeaverTails-style unsafe replies, in-the-wild jailbreak prompts, and "
                 "the EMSCAD fake job postings. Enough: about 14,000 questions.",
        scoring="Per set, the share of real abuse Jev misses and the share of clean items it flags, with 90% intervals; "
                "for jailbreaks, misses by prompt length.",
        chart="Paired bars per set: misses vs false alarms.",
        compared_with="each dataset's own labels",
        limits="The harmful sets are screened: the most extreme items are hidden from the map and left out here. "
               "Jailbreak labels come from where the prompt was collected.",
        sources=[s for s, _, _ in ABUSE])

    def run():
        out = []
        for s, tpl, lab in ABUSE:
            d = rows(s)
            if tpl:
                d = d.filter(pl.col("tpl") == tpl)
            d = d.filter(pl.col("truth").is_in(["true", "false"]))
            m, f, npos, nneg = miss_fa(d)
            out.append({"label": lab, "miss": m, "fa": f, "n": d.height,
                        "ci": boot(1 - d.filter(pl.col("truth") == "true")["ok"].cast(float).to_numpy())})
        out.sort(key=lambda x: x["miss"])
        j = rows("jailbreaks").filter(pl.col("truth") == "true").with_columns(pl.col("m_chars").cast(pl.Int64, strict=False))
        short = 1 - float(j.filter(pl.col("m_chars") <= 476)["ok"].mean())
        long_ = 1 - float(j.filter(pl.col("m_chars") > 950)["ok"].mean())
        old = [x for x in out if x["label"] in ("spam texts", "spam and phishing email", "personal data")]
        new = {x["label"]: x for x in out}
        return Result(
            result=f"Jev misses {and_list([f'{x['miss']:.0%} of {x['label']}' for x in old])}, with few false alarms. "
                   f"Newer abuse gets through: it misses {new['unsafe AI replies']['miss']:.0%} of unsafe AI replies, "
                   f"{new['jailbreak prompts']['miss']:.0%} of jailbreaks ({short:.0%} of the short ones, "
                   f"{long_:.0%} of the long) and {new['fake job ads']['miss']:.0%} of fake job ads.",
            evidence=f"{sum(x['n'] for x in out):,} questions in {len(out)} sets; jailbreak lengths split at 476 and 950 characters",
            numbers={"sets": out, "jailbreak_short_miss": short, "jailbreak_long_miss": long_}, n=sum(x["n"] for x in out),
            chart={"type": "bars2", "labels": [x["label"] for x in out], "a": [x["fa"] for x in out], "b": [x["miss"] for x in out],
                   "a_label": "false alarms", "b_label": "misses"},
            robustness=f"False alarms stay at {max(x['fa'] for x in out):.0%} or below in every set, so the misses "
                       "aren't the price of caution.",
            examples=seeded(rows("fake_job_posts").filter((pl.col("truth") == "true") & ~pl.col("ok"))["id"].to_list(), "abuse"))
    return spec, run


# ---- 5. code ---------------------------------------------------------------------------------------------------------------
def code():
    spec = Spec(
        id="work_code_says_vs_does", family="work", title="Jev reads what code says, not what it does",
        question="Given a function, can Jev tell whether its docstring or commit message describes it, and can it tell "
                 "whether it contains a security bug or needs a reviewer's comment?",
        why="Matching a description to code is a reading task; spotting a buffer overflow is a reasoning task. A model "
            "good at the first and not the second would look helpful in code review while missing what matters.",
        sourcing="Existing yes/no questions: docstring vs function (CodeSearchNet, with docstrings swapped in from other "
                 "functions), commit message vs diff, real vulnerable vs fixed functions from QEMU and FFmpeg "
                 "(Devign), and diff hunks that did or didn't get a review comment. Each set is balanced 50/50.",
        scoring="Per set, the share right, misses and false alarms, with 90% intervals.",
        chart="Bars per set: the share right, with 50% (a coin flip) marked.",
        compared_with="each dataset's own labels",
        limits="Devign functions are shown without the rest of their program, which makes some bugs impossible to see; "
               "review comments reflect one reviewer's choice.",
        sources=["docstring_match", "commit_diff_match", "code_defects", "code_review_need"])

    def run():
        out = []
        for s, lab in [("docstring_match", "docstring fits the function"), ("commit_diff_match", "commit message fits the diff"),
                       ("code_review_need", "change needs a review comment"), ("code_defects", "function has a security bug")]:
            d = rows(s).filter(pl.col("truth").is_in(["true", "false"]))
            m, f, _, _ = miss_fa(d)
            out.append({"label": lab, "acc": float(d["ok"].mean()), "miss": m, "fa": f, "n": d.height,
                        "ci": boot(d["ok"].cast(float).to_numpy())})
        r = {x["label"]: x for x in out}
        bug = r["function has a security bug"]
        return Result(
            result=f"Jev tells whether a docstring describes a function {r['docstring fits the function']['acc']:.0%} "
                   f"of the time and whether a commit message describes a diff {r['commit message fits the diff']['acc']:.0%}. Whether a function has a security bug "
                   f"it gets {bug['acc']:.0%} right, a coin flip: it misses {bug['miss']:.0%} of the vulnerable ones and "
                   f"flags {bug['fa']:.0%} of the fixed ones. Whether a change needs a review comment: "
                   f"{r['change needs a review comment']['acc']:.0%}.",
            evidence=f"{sum(x['n'] for x in out):,} questions, each set balanced; 90% interval on the security-bug share "
                     f"{bug['ci']}",
            numbers={"sets": out}, n=sum(x["n"] for x in out),
            chart={"type": "bars", "rows": [{"label": x["label"], "value": x["acc"], "ci": x["ci"]} for x in out],
                   "domain": [0, 1], "note": "50% = a coin flip"})
    return spec, run


# ---- 6. agent traces ------------------------------------------------------------------------------------------------------
def agents():
    spec = Spec(
        id="work_agent_patches", family="work", title="Jev can tell a crashed coding agent from a finished one, not a good patch from a bad one",
        question="Reading a coding agent's full trace on a real GitHub issue, can Jev tell whether the agent actually "
                 "fixed it?",
        why="Judging agent runs is a growing use for small models (triage before tests run). Telling a crash from a "
            "submission is easy; telling a correct patch from a plausible wrong one is the job.",
        sourcing="Existing questions from SWE-agent trajectories on SWE-bench issues (Llama-based agents), half resolved "
                 "and half not, with the run's exit status in the data.",
        scoring="Share right overall, and split by exit status: runs that ended by running out of room or giving up "
                "vs runs that submitted a patch, where Jev must judge the patch itself.",
        chart="Bars: the share right on each kind of run.",
        compared_with="SWE-bench's own test results (resolved or not)",
        limits="Traces are long; the table keeps the first part of each (large irrelevant state is a documented weak "
               "spot, 01-jev §6 item 5).", sources=["swe_trajectories"])

    def run():
        d = rows("swe_trajectories")
        sub = d.filter(pl.col("m_exit_status") == "submitted")
        crash = d.filter(pl.col("m_exit_status") != "submitted")
        sub_res = rate(sub, pl.col("truth") == "true")
        sub_unres = rate(sub, pl.col("truth") == "false")
        crash_unres = rate(crash, pl.col("truth") == "false")
        crash_res = crash.filter(pl.col("truth") == "true")
        return Result(
            result=f"On runs that crashed, gave up or ran out of room, Jev says 'not fixed' {crash_unres:.0%} of the time, "
                   f"correctly. On runs that submitted a patch it does little better than a coin: it recognizes "
                   f"{sub_res:.0%} of the patches that fixed the issue and {sub_unres:.0%} of those that didn't. "
                   f"Overall {float(d['ok'].mean()):.0%}.",
            evidence=f"{d.height:,} trajectories: {sub.height:,} submitted a patch, {crash.height:,} ended otherwise; "
                     f"90% interval on submitted runs {boot(sub['ok'].cast(float).to_numpy())}",
            numbers={"submitted_resolved": sub_res, "submitted_unresolved": sub_unres, "crashed_unresolved": crash_unres,
                     "crashed_resolved_n": crash_res.height}, n=d.height,
            chart={"type": "bars", "rows": [{"label": "crashed or gave up: says not fixed", "value": crash_unres},
                                            {"label": "submitted, really fixed: says fixed", "value": sub_res},
                                            {"label": "submitted, not fixed: says not fixed", "value": sub_unres}],
                   "domain": [0, 1]},
            robustness=f"{crash_res.height} runs that ran out of room still resolved the issue (the patch submitted "
                       f"automatically passed the tests); Jev calls {1 - float(crash_res['ok'].mean()):.0%} of them unfixed, "
                       "so it judges by how the run ended.",
            examples=seeded(sub.filter(~pl.col("ok"))["id"].to_list(), "swe"))
    return spec, run


# ---- 7. nothing here ------------------------------------------------------------------------------------------------------
NONE = [("squad2_spans", "not_in_passage", None, "questions a passage can't answer"),
        ("relation_extract", "none", None, "chemical-protein relations"),
        ("ddi_interactions", "none", None, "drug-drug interactions"),
        ("unfair_tos", "none", "unfair_tos.clause_type", "unfair clause types"),
        ("pii_detect", "none", "pii_detect.pii_kind", "kinds of personal data")]


def nothing_here():
    spec = Spec(
        id="work_nothing_here", family="work", title="'Nothing here' is the answer Jev gives least",
        question="When a menu of labels includes 'none of these' (the passage has no answer, the sentence states no "
                 "relation), how often does Jev pick it when it's right, and how often when it isn't?",
        why="Extraction pipelines break when a model always finds something: an answer that isn't in the passage, a "
            "drug interaction the sentence never states. The 'nothing here' option is the guard.",
        sourcing="Existing Choice questions whose options include a 'none' answer: SQuAD 2.0 (unanswerable questions), "
                 "ChemProt relations, DDI drug interactions, unfair terms-of-service clause types, PII kinds. Enough: "
                 "about 8,000 questions, about 2,300 whose answer is 'none'.",
        scoring="Per set, the share of 'none' cases where Jev picks 'none', and the share of other cases where it wrongly "
                "picks 'none', with 90% intervals.",
        chart="Paired bars per set: 'none' when right vs 'none' when wrong.",
        compared_with="each dataset's own labels",
        limits="'None' means different things per dataset (no answer, no stated relation, no unfair type).",
        sources=[s for s, _, _, _ in NONE])

    def run():
        out = []
        for s, none, tpl, lab in NONE:
            d = rows(s)
            if tpl:
                d = d.filter(pl.col("tpl") == tpl)
            a, b = d.filter(pl.col("truth") == none), d.filter(pl.col("truth") != none)
            out.append({"label": lab, "says_none": float(a["ok"].mean()), "wrong_none": float((b["top"] == none).mean()),
                        "n_none": a.height, "n": d.height, "ci": boot(a["ok"].cast(float).to_numpy())})
        out.sort(key=lambda x: x["says_none"])
        lo = [x for x in out if x["says_none"] < 0.8]
        return Result(
            result="When the right answer is 'nothing here', Jev picks it only "
                   + and_list([f"{x['says_none']:.0%} of the time on {x['label']}" for x in lo])
                   + f"; otherwise it finds something that isn't there. The reverse error is rare: it picks 'nothing here' "
                   f"wrongly in {min(x['wrong_none'] for x in out):.0%}-{max(x['wrong_none'] for x in out):.0%} of the other cases. "
                   + (f"Personal data is the exception ({out[-1]['says_none']:.0%})." if out[-1]["says_none"] >= 0.8 else ""),
            evidence=f"{sum(x['n'] for x in out):,} questions, {sum(x['n_none'] for x in out):,} whose answer is 'none'",
            numbers={"sets": out}, n=sum(x["n"] for x in out),
            chart={"type": "bars2", "labels": [x["label"] for x in out], "a": [x["wrong_none"] for x in out],
                   "b": [x["says_none"] for x in out], "a_label": "picks 'none' when there is something",
                   "b_label": "picks 'none' when there is nothing"},
            examples=seeded(rows("relation_extract").filter((pl.col("truth") == "none") & ~pl.col("ok"))["id"].to_list(), "none"))
    return spec, run


# ---- 8. function calls -------------------------------------------------------------------------------------------------------
def function_calls():
    spec = Spec(
        id="work_function_call_checks", family="work", title="Jev catches a wrong tool call, except when the arguments are swapped",
        question="Checking whether a proposed function call does what the user asked, which kinds of mistakes does Jev "
                 "catch: the wrong function, a missing argument, a wrong value, or two arguments swapped?",
        why="Agents call tools; a cheap verifier in front of the call is an obvious safety net. Its blind spot is where "
            "the net has a hole.",
        sourcing="Existing verify-the-call questions built from xLAM function-calling data: half the calls are the "
                 "dataset's correct ones, half have one perturbation of a known kind.",
        scoring="Share of each perturbation kind Jev rejects, and the share of correct calls it accepts, with 90% "
                "intervals.",
        chart="Bars: the share caught per kind of mistake, and correct calls accepted.",
        compared_with="the dataset's correct calls and the known perturbation",
        limits="Only 45 swapped-argument calls survived the build (swaps need two arguments of the same type), so that "
               "bar is the least certain.", sources=["function_calls"])

    def run():
        d = rows("function_calls").filter(pl.col("tpl") == "fc.verify_call")
        names = {"wrong_function": "wrong function", "dropped_required": "missing required argument",
                 "changed_value": "wrong argument value", "swapped_args": "two arguments swapped"}
        out = []
        for k, lab in names.items():
            g = d.filter(pl.col("m_perturbation") == k)
            out.append({"label": lab, "value": float(g["ok"].mean()), "n": g.height, "ci": boot(g["ok"].cast(float).to_numpy())})
        good = d.filter(pl.col("truth") == "true")
        acc_good = float(good["ok"].mean())
        sw = out[-1]
        return Result(
            result=f"Jev rejects {out[0]['value']:.0%} of calls to the wrong function, {out[1]['value']:.0%} with a missing "
                   f"argument and {out[2]['value']:.0%} with a wrong value, but only {sw['value']:.0%} of calls with two "
                   f"arguments swapped. It accepts {acc_good:.0%} of the correct calls.",
            evidence=f"{d.height:,} calls; swapped arguments n={sw['n']}, 90% interval {sw['ci']}",
            numbers={"kinds": out, "correct_accepted": acc_good}, n=d.height,
            chart={"type": "bars", "rows": [{"label": x["label"], "value": x["value"], "ci": x["ci"]} for x in out]
                   + [{"label": "correct call accepted", "value": acc_good}], "domain": [0, 1]},
            examples=seeded(d.filter((pl.col("m_perturbation") == "swapped_args") & ~pl.col("ok"))["id"].to_list(), "fc"))
    return spec, run


# ---- 9. ICD-10 ---------------------------------------------------------------------------------------------------------------
def icd():
    spec = Spec(
        id="work_icd_coding_rules", family="work", title="Jev knows medicine, not the medical coder's rules",
        question="Asked which ICD-10-CM chapter a diagnosis belongs to, where does Jev go wrong: the medicine, or the "
                 "coding conventions?",
        why="Medical coding follows rules that aren't medical: how an injury happened (a fall, a car crash) is coded in "
            "its own chapter, separate from the injury. A model that reasons from the medicine will be right about "
            "the body and wrong about the book.",
        sourcing="Existing questions: an ICD-10-CM code's description, pick its chapter from the chapters' names; 95 or "
                 "96 codes per chapter.",
        scoring="Share right per chapter, and the most common confusions.",
        chart="Bars per chapter: the share right, lowest first.",
        compared_with="the ICD-10-CM chapter each code belongs to",
        limits="Descriptions only, no clinical notes; the chapter names are what Jev picks from.", sources=["icd10_chapter"])

    def run():
        d = rows("icd10_chapter")
        by = d.group_by("truth").agg(pl.col("ok").mean(), pl.len()).sort("ok", "truth").to_dicts()
        conf = d.filter(~pl.col("ok")).group_by("truth", "top").len().sort("len", "truth", descending=[True, False]).head(5).to_dicts()
        ext = next(b for b in by if b["truth"] == "external_causes")
        ext_inj = d.filter((pl.col("truth") == "external_causes") & (pl.col("top") == "injury_poisoning")).height / max(ext["len"], 1)
        rest = d.filter(pl.col("truth") != "external_causes")
        pretty = lambda s: s.replace("_", " ")  # noqa: E731
        return Result(
            result=f"Jev puts {float(rest['ok'].mean()):.0%} of diagnoses in the right ICD-10 chapter outside one: codes "
                   f"for how an injury happened (falls, crashes, bites) it gets right only {ext['ok']:.0%} of the time, "
                   f"filing {ext_inj:.0%} of them under the injury itself: the medical answer, not the coder's. Next "
                   f"weakest: {and_list([f'{pretty(b['truth'])} ({b['ok']:.0%})' for b in by[1:3]])}.",
            evidence=f"{d.height:,} codes, about 95 per chapter",
            numbers={"chapters": by, "confusions": conf}, n=d.height,
            chart={"type": "bars", "rows": [{"label": pretty(b["truth"]), "value": b["ok"]} for b in by], "domain": [0, 1]},
            examples=seeded(d.filter((pl.col("truth") == "external_causes") & ~pl.col("ok"))["id"].to_list(), "icd"))
    return spec, run


# ---- 10. job ads -------------------------------------------------------------------------------------------------------------
RUNGS = ["internship", "entry_level", "associate", "mid_senior", "director", "executive"]


def jobs():
    spec = Spec(
        id="work_job_ad_rungs", family="work", title="Jev reads entry-level job ads as a rung more senior",
        question="Reading a LinkedIn job posting, does Jev place its seniority and type (full-time, contract, part-time) "
                 "where the employer did?",
        why="Job matching and search depend on these fields. A systematic lean (every entry-level ad read as "
            "associate) quietly moves candidates to the wrong jobs.",
        sourcing="Existing questions from LinkedIn job postings (2023-24), balanced across seniority levels and work "
                 "types, with the employer's own label.",
        scoring="Seniority: share right, and among misses the share placed above vs below the employer's level on the "
                "ladder internship < entry < associate < mid-senior < director < executive. Work type: the most "
                "common confusions.",
        chart="A heat table: the employer's level (rows) vs Jev's (columns).",
        compared_with="the employer's own labels",
        limits="Employers' labels are themselves inconsistent (one company's associate is another's entry level). "
               "Postings are truncated in the table.", sources=["linkedin_jobs"])

    def run():
        d = rows("linkedin_jobs")
        s = d.filter(pl.col("tpl") == "linkedin_jobs.seniority").filter(pl.col("truth").is_in(RUNGS) & pl.col("top").is_in(RUNGS))
        s = s.with_columns(pl.col("truth").replace_strict({k: i for i, k in enumerate(RUNGS)}).alias("ti"),
                           pl.col("top").replace_strict({k: i for i, k in enumerate(RUNGS)}).alias("ji"))
        miss = s.filter(~pl.col("ok"))
        up = float((miss["ji"] > miss["ti"]).mean())
        one = float(((miss["ji"] - miss["ti"]).abs() == 1).mean())
        e2a = s.filter(pl.col("truth") == "entry_level")
        e2a_share = float((e2a["top"] == "associate").mean())
        w = d.filter(pl.col("tpl") == "linkedin_jobs.work_type")
        c2f = float((w.filter(pl.col("truth") == "contract")["top"] == "full_time").mean())
        p2f = float((w.filter(pl.col("truth") == "part_time")["top"] == "full_time").mean())
        return Result(
            result=f"Jev places {float(s['ok'].mean()):.0%} of job ads at the employer's seniority. Its misses go up the "
                   f"ladder {up:.0%} of the time, {one:.0%} of them by one rung: it reads {e2a_share:.0%} of entry-level "
                   f"ads as associate. It also reads {c2f:.0%} of contract jobs and {p2f:.0%} of part-time jobs as "
                   f"full-time.",
            evidence=f"{s.height:,} seniority and {w.height:,} work-type questions",
            numbers={"acc": float(s["ok"].mean()), "up": up, "one_rung": one, "entry_as_associate": e2a_share,
                     "contract_as_full": c2f, "part_as_full": p2f}, n=s.height + w.height,
            chart={"type": "heat", "cells": [{"y": r["truth"], "x": r["top"], "len": r["len"]}
                                              for r in s.group_by("truth", "top").len().sort("truth", "top").to_dicts()],
                   "x": "Jev's level", "y": "employer's level", "order": RUNGS},
            examples=seeded(e2a.filter(~pl.col("ok"))["id"].to_list(), "jobs"))
    return spec, run


# ---- 11. retrieval gates -------------------------------------------------------------------------------------------------
def retrieval():
    spec = Spec(
        id="work_retrieval_gates", family="work", title="Deciding what goes into the context: too generous on web search, too strict on multi-step questions",
        question="Asked whether a retrieved passage answers a query or belongs in the context, which way does Jev err: "
                 "letting in passages that don't help, or throwing out ones that do?",
        why="Retrieval pipelines use a cheap model as a gate before the expensive one. A generous gate wastes context; "
            "a strict one drops the evidence a multi-step question needs.",
        sourcing="Existing yes/no questions from MS MARCO (web search passages vs real queries), HotpotQA (paragraphs "
                 "needed for two-step questions vs distractors on the same topic) and QNLI (does a Wikipedia sentence "
                 "answer the question).",
        scoring="Per set, the share of useful passages Jev rejects and of useless passages it lets in, with 90% intervals.",
        chart="Paired bars per set: useful passages rejected vs useless ones let in.",
        compared_with="each dataset's own labels",
        limits="MS MARCO's labels mark the passage a human annotator used, so some unmarked passages do answer the "
               "query; that inflates its 'let in' rate.", sources=["msmarco_relevance", "hotpot_gating", "qnli_gating"])

    def run():
        out = []
        for s, tpl, lab in [("msmarco_relevance", "msmarco.answers_query", "web search (MS MARCO)"),
                            ("hotpot_gating", None, "two-step questions (HotpotQA)"), ("qnli_gating", None, "single sentences (QNLI)")]:
            d = rows(s)
            if tpl:
                d = d.filter(pl.col("tpl") == tpl)
            d = d.filter(pl.col("truth").is_in(["true", "false"]))
            m, f, _, _ = miss_fa(d)
            out.append({"label": lab, "rejects_useful": m, "lets_in": f, "n": d.height})
        ms, hp, qn = out
        return Result(
            result=f"On web search passages Jev lets in {ms['lets_in']:.0%} of those that don't answer the query "
                   f"(rejecting {ms['rejects_useful']:.0%} of useful ones); on two-step questions it throws out "
                   f"{hp['rejects_useful']:.0%} of the paragraphs the answer needs (letting in {hp['lets_in']:.0%} of "
                   f"distractors). With a single sentence that states the answer or not, both errors stay under "
                   f"{max(qn['rejects_useful'], qn['lets_in']):.0%}.",
            evidence=f"{sum(x['n'] for x in out):,} questions",
            numbers={"sets": out}, n=sum(x["n"] for x in out),
            chart={"type": "bars2", "labels": [x["label"] for x in out], "a": [x["lets_in"] for x in out],
                   "b": [x["rejects_useful"] for x in out], "a_label": "useless passages let in",
                   "b_label": "useful passages rejected"},
            robustness="A likely reason, not measured here: HotpotQA's needed paragraphs are often the 'bridge' that "
                       "names an entity without stating the answer, and Jev seems to read 'needed' as 'contains the answer'.",
            examples=seeded(rows("hotpot_gating").filter((pl.col("truth") == "true") & ~pl.col("ok"))["id"].to_list(), "hotpot"))
    return spec, run


# ---- 12. names in tweets -------------------------------------------------------------------------------------------------
def entities():
    spec = Spec(
        id="work_names_in_tweets", family="work", title="People are easy; brands and products in tweets are not",
        question="Given a name in a sentence, can Jev say what kind of thing it names, in edited news text and in tweets?",
        why="Entity typing feeds search, moderation and analytics. News names follow conventions; tweets name brands, "
            "products and groups in ways that break them.",
        sourcing="Existing questions from CoNLL-2003 (news: person, organization, location, other) and WNUT-17 (tweets: "
                 "person, location, group, corporation, product, creative work), balanced by type.",
        scoring="Share right per type in each corpus, and the most common confusion for the weakest types.",
        chart="Bars per type, news and tweets.",
        compared_with="each dataset's own labels",
        limits="WNUT-17 was built from rare and emerging names on purpose.", sources=["entity_typing"])

    def run():
        d = rows("entity_typing")
        out = []
        for tpl, corp in [("entity_typing.conll_type", "news"), ("entity_typing.wnut_type", "tweets")]:
            for b in d.filter(pl.col("tpl") == tpl).group_by("truth").agg(pl.col("ok").mean(), pl.len()).sort("ok", "truth").to_dicts():
                out.append({"label": f"{b['truth'].replace('_', ' ')} ({corp})", "value": b["ok"], "n": b["len"], "corpus": corp, "type": b["truth"]})
        tw = d.filter(pl.col("tpl") == "entity_typing.wnut_type")
        conf = {t: tw.filter((pl.col("truth") == t) & ~pl.col("ok")).group_by("top").len().sort("len", "top", descending=[True, False]).head(1).to_dicts()
                for t in ("corporation", "product", "group")}
        p = {(x["corpus"], x["type"]): x["value"] for x in out}
        c = conf["corporation"][0]["top"] if conf["corporation"] else "?"
        pr = conf["product"][0]["top"] if conf["product"] else "?"
        return Result(
            result=f"Jev types people's names right {p[('news', 'person')]:.0%} of the time in news and "
                   f"{p[('tweets', 'person')]:.0%} in tweets, but in tweets it gets corporations {p[('tweets', 'corporation')]:.0%}, "
                   f"products {p[('tweets', 'product')]:.0%} and groups {p[('tweets', 'group')]:.0%} right: a company "
                   f"is most often taken for a {c.replace('_', ' ')}, a product for a {pr.replace('_', ' ')}.",
            evidence=f"{d.height:,} names ({d.filter(pl.col('tpl') == 'entity_typing.conll_type').height:,} news, {tw.height:,} tweets)",
            numbers={"types": out, "confusions": conf}, n=d.height,
            chart={"type": "bars", "rows": [{"label": x["label"], "value": x["value"]} for x in out], "domain": [0, 1]},
            examples=seeded(tw.filter((pl.col("truth") == "corporation") & ~pl.col("ok"))["id"].to_list(), "ent"))
    return spec, run


EXPERIMENTS = [legal(), hallucination(), evidence(), abuse(), code(), agents(), nothing_here(), function_calls(), icd(),
               jobs(), retrieval(), entities()]
