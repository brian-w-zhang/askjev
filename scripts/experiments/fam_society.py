"""Society experiments on new questions: how honest professions seem (Gallup), how much standing jobs have (the
classic prestige studies), and how much people trust each other and say they're happy, country by country (IVS)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, level, norm, with_meta

PCT = [f"p{v:03d}" for v in range(0, 101, 5)]


def robust(r: dict) -> dict:
    """Jev's choice distribution averaged over the base probe and the shuffled-order probes."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def robust_level(r: dict) -> float | None:
    """Expected level of a Score, averaged with the same question asked with the levels reversed."""
    base = level(js(r["jev_dist"]))
    rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "reversed_levels" and v.get("dist")), None)
    if base is None:
        return None
    return (base + rev) / 2 if rev is not None else base


def top_share(r: dict, levels=("3", "4")) -> float:
    """Jev's probability on the top two of five levels, averaged over the base and reversed-level probes."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "reversed_levels" and v.get("dist")]
    return float(np.mean([sum(d.get(k, 0.0) for k in levels) for d in ds]))


def pct_median(d: dict) -> float:
    d = norm(d)
    c = 0.0
    for k in PCT:
        c += d.get(k, 0.0)
        if c >= 0.5:
            return float(k[1:])
    return 100.0


# ---- Gallup honesty -----------------------------------------------------------------------------------------------------
GALLUP_LIMITS = ("Gallup asks US adults by phone and online; 'no opinion' answers are dropped. Politics and religion "
                 "are left out: members of Congress, journalists, police officers, clergy and labor union leaders. The "
                 "five answers are Gallup's own degree words.")


def honesty():
    spec = Spec(
        id="society_profession_honesty", family="society", title="Which professions Jev trusts, next to Americans",
        question="Rating the honesty and ethical standards of nurses, pharmacists, bankers, car salespeople and a dozen "
                 "other professions, does Jev see the same ladder of trust as Americans, and is it more or less generous?",
        why="Gallup has asked Americans this every year since 1976; it is the standard picture of which jobs people "
            "trust. A model that talks about professions all day carries its own picture, which may be kinder or "
            "harsher than the public's.",
        sourcing="New questions (sources/gallup_honesty): Gallup's wording, 'How would you rate the honesty and "
                 "ethical standards of people in this field: <profession>?', with its five answers, for 16 professions "
                 "in the December 2025 poll; the human distribution is Gallup's published split.",
        collection="16 new questions, each asked as written, for 'most Americans', and with the levels reversed "
                   "(averaged).",
        scoring="Per profession, the share rating it high or very high, Jev (its probability on the top two levels) vs "
                "Americans; rank correlation of the expected levels over professions; the mean gap with a 90% bootstrap "
                "interval; the professions with the largest gaps; Jev's guess for 'most Americans' scored the same way.",
        chart="Dots per profession: Americans' share rating it high or very high (diamond) and Jev's (square), sorted "
              "by Americans'.",
        compared_with="US adults (Gallup Honesty and Ethics poll, December 2025)", limits=GALLUP_LIMITS,
        new_questions=16, sources=["gallup_honesty"])

    def run():
        rows = []
        for r in with_meta("gallup_honesty"):
            if r["m"].get("set") != "current":
                continue
            h = biggest(r["humans"])
            if not h:
                continue
            hd = norm(h["dist"])
            g = norm(js(r["people_dist"]) or {})
            rows.append({"id": r["id"], "prof": r["m"]["profession"], "jev": top_share(r), "people": hd.get("3", 0) + hd.get("4", 0),
                         "jev_level": robust_level(r), "ppl_level": level(hd),
                         "guess": g.get("3", 0) + g.get("4", 0) if g else None})
        t = pl.DataFrame(rows).sort("people", descending=True)
        rho = spearmanr(t["jev_level"], t["ppl_level"]).statistic
        gap = (t["jev"] - t["people"]).to_numpy()
        tt = t.with_columns((pl.col("jev") - pl.col("people")).alias("g"))
        up, down = tt.sort("g", descending=True).head(3).to_dicts(), tt.sort("g").head(3).to_dicts()
        f = lambda r: f"{r['prof'].lower()} ({r['jev']:.0%} vs {r['people']:.0%})"  # noqa: E731
        rho_g = spearmanr(t["guess"].fill_null(0), t["people"]).statistic if t["guess"].is_not_null().all() else None
        return Result(
            result=f"Jev orders the {t.height} professions {agree_word(rho)} like Americans (rank correlation {rho:.2f}), "
                   f"but more starkly: it trusts {and_list([f(r) for r in up if r['g'] > 0])} far more than Americans do, "
                   f"and {and_list([f(r) for r in down if r['g'] < 0])} far less (share rating them high or very high, "
                   f"Jev vs Americans). On average the two come out even ({gap.mean():+.0%}).",
            evidence=f"{t.height} professions; spread of the shares: Jev SD {float(t['jev'].std()):.0%}, Americans "
                     f"{float(t['people'].std()):.0%}; 90% interval on the mean gap {boot(gap)}"
                     + (f"; Jev's guess for 'most Americans' ranks them with correlation {rho_g:.2f}" if rho_g is not None else ""),
            numbers={"rows": rows, "rho": rho, "mean_gap": float(gap.mean()), "rho_guess": rho_g}, n=t.height,
            robustness="" if t.height == 16 else f"The screen hid {16 - t.height} of the 16 profession questions.",
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": r["prof"], "value": r["jev"], "people": r["people"],
                                                                "guess": r["guess"]} for r in t.to_dicts()]},
            examples=[up[0]["id"], down[0]["id"]])
    return spec, run


def honesty_history():
    spec = Spec(
        id="society_honesty_history", family="society", title="Does Jev remember when trust in bankers fell?",
        question="Asked what share of Americans rated each profession's honesty high in Gallup's polls of 2000, 2005, "
                 "2010, 2015 and 2020, how close is Jev, and does it know which professions rose or fell?",
        why="Trust moves: bankers and stockbrokers lost standing after 2008, nurses have led for decades. Knowing the "
            "level is general knowledge; knowing the change means the model has a sense of time for public opinion.",
        sourcing="New questions (sources/gallup_honesty): 'In Gallup's poll of <month year>, what share of Americans "
                 "rated the honesty and ethical standards of <profession> as \"very high\" or \"high\"?', 21 bins "
                 "(0-100% by 5), for each of the 16 professions and each target year with a poll within a year; the "
                 "answer is the published trend figure.",
        collection="65 new questions, each asked as written and with the bins in three shuffled orders (averaged).",
        scoring="Jev's median share vs the published share: mean absolute error in points, and within 5 points, by "
                "year; for professions asked in both 2005 and 2010, and in 2010 and 2020, whether Jev's change has the "
                "same sign as the real change, and the rank correlation of the changes.",
        chart="Slopes per profession: the published share across the years (ink) and Jev's (magenta).",
        compared_with="Gallup's published trend figures (US adults, 2000-2020)", limits=GALLUP_LIMITS,
        new_questions=65, sources=["gallup_honesty"])

    def run():
        rows = []
        for r in with_meta("gallup_honesty"):
            if r["m"].get("set") != "history":
                continue
            rows.append({"id": r["id"], "prof": r["m"]["profession"], "year": r["m"]["year"], "jev": pct_median(robust(r)),
                         "true": r["m"]["high_share"]})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("true")).alias("err"))
        by = t.group_by("year").agg(pl.col("err").abs().mean().alias("mae"), (pl.col("err").abs() <= 5).mean().alias("near"),
                                    pl.col("err").mean().alias("bias"), pl.len()).sort("year").to_dicts()
        changes = []
        for (prof,), g in t.group_by("prof"):
            d = {r["year"]: r for r in g.to_dicts()}
            for a, b in ((2005, 2010), (2010, 2020)):
                if a in d and b in d:
                    changes.append({"prof": prof, "span": f"{a}-{b}", "true": d[b]["true"] - d[a]["true"], "jev": d[b]["jev"] - d[a]["jev"]})
        c = pl.DataFrame(changes)
        moved = c.filter(pl.col("true").abs() >= 5)
        same = float((np.sign(moved["true"]) == np.sign(moved["jev"])).mean()) if moved.height else float("nan")
        flat = float((c["jev"].abs() < 5).mean())
        rho = spearmanr(c["jev"], c["true"]).statistic if c.height > 5 else float("nan")
        mae = float(t["err"].abs().mean())
        big = moved.sort(pl.col("true").abs(), descending=True).head(2).to_dicts()
        return Result(
            result=f"Jev's guesses of past trust are off by {mae:.0f} points on average ({float((t['err'].abs() <= 5).mean()):.0%} "
                   f"within 5), and they barely move over time: its estimate changes by less than 5 points in "
                   f"{flat:.0%} of the five- and ten-year spans. Where Americans' trust really moved by 5 points or more "
                   f"(only {moved.height} spans), Jev's change points the same way in {int(round(same * moved.height))} of them, but smaller"
                   + (f"; for {big[0]['prof'].lower()} {big[0]['span']} the real change was {big[0]['true']:+.0f} points, "
                      f"Jev's {big[0]['jev']:+.0f}." if big else "."),
            evidence=f"{t.height} poll figures for 16 professions; rank correlation of changes {rho:.2f}; by year: "
                     + "; ".join(f"{b['year']} off by {b['mae']:.0f}" for b in by),
            numbers={"rows": rows, "by_year": by, "changes": changes, "same_direction": same, "flat": flat, "rho_changes": rho},
            n=t.height,
            chart={"type": "dumbbell", "a_label": "real change", "b_label": "Jev's change", "zero": 0,
                   "rows": [{"label": f"{x['prof']} {x['span']}", "a": x["true"], "b": x["jev"]} for x in
                            sorted(changes, key=lambda x: x["true"])]},
            examples=[r["id"] for r in t.sort(pl.col("err").abs(), descending=True).head(2).to_dicts()])
    return spec, run


# ---- prestige -----------------------------------------------------------------------------------------------------------
def prestige_duncan():
    spec = Spec(
        id="society_prestige_1947", family="society", title="Job standing: Jev vs Americans in 1947",
        question="For 45 jobs from the classic 1947 NORC prestige survey (physician, banker, carpenter, janitor, shoe "
                 "shiner...), does Jev give each the standing Americans gave it, and is its ladder tied more to pay and "
                 "schooling than theirs was?",
        why="The North-Hatt survey founded the study of occupational prestige; Duncan used it to show that standing "
            "follows education and income. A model's sense of which jobs are respected can be dated (1947 values) or "
            "modern, and it can lean on money more or less than people did.",
        sourcing="New questions (sources/occupation_prestige): 'How would you rate the general standing of <a job> as "
                 "a job?', the survey's five standings (poor to excellent) described, for Duncan's 45 occupations; the "
                 "human side is the published percentage rating each job excellent or good.",
        collection="45 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Jev's probability on 'good' or 'excellent' vs the percentage of 1947 raters; rank correlation; the jobs "
                "with the largest gaps; and the rank correlation of each side with the 1950 census shares of high "
                "income and high education in the job.",
        chart="A scatter: 1947 raters' share good or excellent (x) vs Jev's (y), labeled at the largest gaps, diagonal.",
        compared_with="US adults in the 1947 NORC North-Hatt survey (Duncan 1961)",
        limits="The raters are from 1947 and some job titles are dated (streetcar motorman, soda fountain clerk); a gap "
               "can be Jev being modern rather than wrong. Only the published percentage exists, no distribution.",
        new_questions=45, sources=["occupation_prestige"])

    def run():
        rows = []
        for r in with_meta("occupation_prestige"):
            if r["m"].get("set") != "duncan_1947":
                continue
            rows.append({"id": r["id"], "job": r["m"]["occupation"], "jev": 100 * top_share(r), "people": r["m"]["good_or_excellent"],
                         "income": r["m"]["income_high"], "education": r["m"]["education_high"]})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("people")).alias("g"))
        rho = spearmanr(t["jev"], t["people"]).statistic
        ri_j, ri_p = spearmanr(t["jev"], t["income"]).statistic, spearmanr(t["people"], t["income"]).statistic
        re_j, re_p = spearmanr(t["jev"], t["education"]).statistic, spearmanr(t["people"], t["education"]).statistic
        up, down = t.sort("g", descending=True).head(3).to_dicts(), t.sort("g").head(3).to_dicts()
        f = lambda r: f"{r['job']} ({r['jev']:.0f}% vs {r['people']:.0f}%)"  # noqa: E731
        return Result(
            result=f"Jev ranks the {t.height} jobs {agree_word(rho)} like Americans in 1947 (rank correlation {rho:.2f}). It "
                   f"gives far more standing to {and_list([f(r) for r in up])}, and far less to "
                   f"{and_list([f(r) for r in down])} (share rating it good or excellent, Jev vs 1947). Its ladder follows "
                   f"income {'more' if ri_j > ri_p else 'less'} closely than theirs ({ri_j:.2f} vs {ri_p:.2f}) and "
                   f"education {'more' if re_j > re_p else 'less'} ({re_j:.2f} vs {re_p:.2f}).",
            robustness="" if t.height == 45 else f"The screen hid {45 - t.height} of the 45 jobs as sensitive or political.",
            evidence=f"{t.height} occupations; mean gap {float(t['g'].mean()):+.0f} points, 90% interval {boot(t['g'].to_numpy())}",
            numbers={"rows": rows, "rho": rho, "income": [ri_j, ri_p], "education": [re_j, re_p]}, n=t.height,
            chart={"type": "scatter", "points": [[round(r["people"], 1), round(r["jev"], 1)] for r in rows],
                   "labels": [{"label": r["job"], "x": r["people"], "y": r["jev"]} for r in up + down],
                   "x": "1947 raters: % good or excellent", "y": "Jev: % good or excellent", "diagonal": True, "domain": [0, 100]},
            examples=[up[0]["id"], down[0]["id"]])
    return spec, run


def prestige_canada():
    spec = Spec(
        id="society_prestige_1965", family="society", title="Job standing: Jev vs Canadians in 1965",
        question="For 102 occupations from the Pineo-Porter Canadian prestige survey, does Jev order jobs by standing "
                 "the way Canadians did, and which jobs has it promoted or demoted?",
        why="The second classic prestige study, with a census record of each job's pay, schooling and share of women. "
            "It shows whether a model's picture of respectable work matches a mid-century public, and where it has "
            "moved.",
        sourcing="New questions (sources/occupation_prestige): the same standing question with five described levels "
                 "for the 102 occupations in Fox's carData `Prestige` data (one duplicate title dropped); the human "
                 "side is the published mean prestige score.",
        collection="101 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).",
        scoring="Rank correlation between Jev's expected level (base and reversed averaged) and the mean prestige score, "
                "with a 90% bootstrap interval; the occupations whose rank moves most; each side's rank correlation "
                "with 1971 income, years of education and share of women.",
        chart="A rank scatter: Canadians' rank (x) vs Jev's rank (y), with the ten largest moves labeled.",
        compared_with="Canadian adults in the 1965 national prestige survey (Pineo & Porter 1967)",
        limits="Mean scores only; survey from 1965, census from 1971. Titles are the census's (some dated).",
        new_questions=101, sources=["occupation_prestige"])

    def run():
        rows = []
        for r in with_meta("occupation_prestige"):
            if r["m"].get("set") != "pineo_porter_1965":
                continue
            rows.append({"id": r["id"], "job": r["m"]["occupation"], "jev": robust_level(r), "people": r["m"]["prestige_mean"],
                         "income": r["m"]["income_1971"], "education": r["m"]["education_years"], "women": r["m"]["women_pct"]})
        t = pl.DataFrame(rows).sort("job")
        rho = spearmanr(t["jev"], t["people"]).statistic
        idx = np.arange(t.height)
        ci = boot(idx, stat=lambda ii: spearmanr(t["jev"].to_numpy()[ii.astype(int)], t["people"].to_numpy()[ii.astype(int)]).statistic, b=300)
        t = t.with_columns((pl.col("jev").rank() / t.height).alias("rj"), (pl.col("people").rank() / t.height).alias("rp"))
        t = t.with_columns((pl.col("rj") - pl.col("rp")).alias("d"))
        up, down = t.sort("d", descending=True).head(5).to_dicts(), t.sort("d").head(5).to_dicts()
        cor = {k: (spearmanr(t["jev"], t[k]).statistic, spearmanr(t["people"], t[k]).statistic) for k in ("income", "education", "women")}
        return Result(
            result=f"Jev orders the {t.height} occupations {agree_word(rho)} like Canadians in 1965 (rank correlation {rho:.2f}). "
                   f"It promotes {and_list([r['job'] for r in up[:3]])} and demotes {and_list([r['job'] for r in down[:3]])}. "
                   + (f"Its ladder follows pay more than schooling (income {cor['income'][0]:.2f}, education {cor['education'][0]:.2f}); "
                      f"the 1965 public's followed schooling more (education {cor['education'][1]:.2f}, income {cor['income'][1]:.2f})."
                      if cor["income"][0] > cor["education"][0] and cor["education"][1] > cor["income"][1] else
                      f"Education and income: Jev {cor['education'][0]:.2f} and {cor['income'][0]:.2f}, the 1965 public "
                      f"{cor['education'][1]:.2f} and {cor['income'][1]:.2f}."),
            evidence=f"{t.height} occupations; 90% interval on the rank correlation {ci[0]:.2f} to {ci[1]:.2f}; share of women: "
                     f"Jev {cor['women'][0]:.2f}, Canadians {cor['women'][1]:.2f}",
            numbers={"rho": rho, "ci90": ci, "up": up, "down": down, "correlates": cor}, n=t.height,
            robustness="" if t.height == 101 else f"The screen hid {101 - t.height} of the 101 occupation questions.",
            chart={"type": "rankscatter", "points": t.select("rj", "rp").to_numpy().round(3).tolist(),
                   "labels": [{"label": r["job"], "x": r["rp"], "y": r["rj"]} for r in up[:5] + down[:5]],
                   "x": "Canadians' rank (1965)", "y": "Jev's rank"},
            examples=[up[0]["id"], down[0]["id"]])
    return spec, run


# ---- country trust and happiness ------------------------------------------------------------------------------------------
def country(ind: str):
    what = {"trust": ("say most people can be trusted", "trust", "How much do people trust each other, country by country?"),
            "happy": ("say they are very or quite happy", "happiness", "How many people say they're happy, country by country?")}[ind]
    spec = Spec(
        id=f"society_country_{ind}", family="society",
        title={"trust": "Does Jev know where people trust each other?", "happy": "Does Jev know where people say they're happy?"}[ind],
        question=f"For each of about 100 countries, what share of people {what[0]} in its latest World Values Survey or "
                 f"European Values Study, and does Jev know?",
        why={"trust": "Trust in strangers ranges from under 5% to over 70% of people, and it predicts a great deal about "
                      "a country. A model's picture of it shows whether it knows the world or projects one country onto "
                      "all of them.",
             "happy": "Most people in most countries call themselves happy, but the share still ranges widely; guessing it "
                      "tests whether a model knows the world's moods or assumes misery where it assumes poverty."}[ind],
        sourcing="New questions (sources/country_values): 'In the <year> World Values Survey or European Values Study "
                 "in <country>, what share of people ...?', 21 bins (0-100% by 5), for every country with a survey since "
                 "2010; the answer is the published share (Integrated Values Surveys, via Our World in Data).",
        collection="109 new questions, each asked as written and with the bins in three shuffled orders (averaged).",
        scoring="Jev's median share vs the published share: mean absolute error, bias (mean signed error) with a 90% "
                "bootstrap interval, rank correlation over countries; the largest over- and underestimates.",
        chart="A scatter: published share (x) vs Jev's median (y), one dot per country, diagonal, the largest misses "
              "labeled.",
        compared_with="Integrated Values Surveys respondents (WVS and EVS, nationally representative samples)",
        limits="One survey per country, in different years (2010-2023); the published share has sampling error of a few "
               "points.", new_questions=109, sources=["country_values"])

    def run():
        rows = []
        for r in with_meta("country_values"):
            if r["m"].get("set") != ind:
                continue
            rows.append({"id": r["id"], "country": r["m"]["country"], "jev": pct_median(robust(r)), "true": r["m"]["share"]})
        t = pl.DataFrame(rows).sort("country").with_columns((pl.col("jev") - pl.col("true")).alias("err"))
        rho = spearmanr(t["jev"], t["true"]).statistic
        err = t["err"].to_numpy()
        over, under = t.sort("err", descending=True).head(3).to_dicts(), t.sort("err").head(3).to_dicts()
        f = lambda r: f"{r['country']} ({r['jev']:.0f}% vs {r['true']:.0f}%)"  # noqa: E731
        sd_j, sd_t = float(t["jev"].std()), float(t["true"].std())
        return Result(
            result=(f"Jev guesses the share who {what[0]} {abs(err.mean()):.0f} points too {'high' if err.mean() > 0 else 'low'} "
                    f"on average across {t.height} countries, and ranks the countries only {agree_word(rho)} like the surveys "
                    f"(rank correlation {rho:.2f})" if abs(err.mean()) >= 10 else
                    f"Jev ranks {t.height} countries by {what[1]} {agree_word(rho)} like the surveys (rank correlation "
                    f"{rho:.2f}), off by {float(np.abs(err).mean()):.0f} points on average"
                    + (f" and {'too high' if err.mean() > 0 else 'too low'} by {abs(err.mean()):.0f}" if abs(err.mean()) >= 3 else ""))
                   + (f". Its guesses spread {'less' if sd_j < sd_t else 'more'} than the real shares (SD {sd_j:.0f} vs {sd_t:.0f} points)"
                      if abs(sd_j - sd_t) >= 2 else "")
                   + (f". It overestimates {and_list([f(r) for r in over if r['err'] > 0])}" if any(r["err"] > 0 for r in over) else "")
                   + (f"{'; it' if any(r['err'] > 0 for r in over) else '. It'} underestimates {and_list([f(r) for r in under if r['err'] < 0])}"
                      if any(r["err"] < 0 for r in under) else "")
                   + " (Jev vs survey).",
            evidence=f"{t.height} countries; 90% interval on the mean error {boot(err)} points",
            robustness="" if t.height == 109 else f"The screen hid {109 - t.height} of the 109 country questions.",
            numbers={"rows": rows, "rho": rho, "mae": float(np.abs(err).mean()), "bias": float(err.mean()), "sd": [sd_j, sd_t]},
            n=t.height,
            chart={"type": "scatter", "points": [[round(r["true"], 1), r["jev"]] for r in rows],
                   "labels": [{"label": r["country"], "x": r["true"], "y": r["jev"]} for r in over + under],
                   "x": "survey: share (%)", "y": "Jev's median (%)", "diagonal": True, "domain": [0, 100]},
            examples=[over[0]["id"], under[0]["id"]])
    return spec, run


EXPERIMENTS = [honesty(), honesty_history(), prestige_duncan(), prestige_canada(), country("trust"), country("happy")]
