"""Risk and forecasting experiments: described gambles (choices13k, Wulff et al.), unknown odds, everyday risk-taking
(Basel-Berlin Risk Study), and Manifold forecasts against the market and the outcome. Prospect theory's classic
problems are in fam_moral (risk_prospect_theory)."""

from __future__ import annotations

import json
import re

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, biggest, boot, js, level, norm, seeded, source

NUMBERS = ("Reading payoffs and percentages leans on numbers, a weak spot TypeSafe documents for Jev "
           "(docs/01-jev.md §6, item 2), so this is labeled known territory.")


def parse(s: str) -> list[tuple[float, float]] | None:
    """'$12 with a 99% chance, or $47 with a 1% chance' -> [(12, .99), (47, .01)]; None if the odds aren't stated."""
    m = re.fullmatch(r"(-?)\$?([\d,.]+)( points)? for sure", s.strip())
    if m:
        return [(float(m.group(2).replace(",", "")) * (-1 if m.group(1) else 1), 1.0)]
    out = [(float(a.replace(",", "")) * (-1 if sg else 1), float(p) / 100)
           for sg, a, p in re.findall(r"(-?)\$?([\d,]*\.?\d+)(?: points)? with an? ([\d.]+)% chance", s)]
    return out if out and abs(sum(p for _, p in out) - 1) < 0.02 else None


def gambles(src: str) -> pl.DataFrame:
    """One row per two-option gamble with stated odds: the relative expected-value edge of option A, and the share
    choosing A for Jev, people, and Jev's guess of most people."""
    rows = []
    for r in source(src).iter_rows(named=True):
        st = js(r["state"])
        ks = list(st)
        g = [parse(st[k]) for k in ks]
        if None in g or len(ks) != 2:
            continue
        ev = [sum(v * p for v, p in x) for x in g]
        scale = max(abs(v) for x in g for v, _ in x) or 1
        rows.append({"id": r["id"], "edge": (ev[0] - ev[1]) / scale, "jev": norm(js(r["jev_dist"]))[ks[0]],
                     "people": norm(biggest(r["humans"])["dist"])[ks[0]],
                     "guess": norm(js(r["people_dist"]) or {ks[0]: np.nan}).get(ks[0], np.nan),
                     "losses": any(v < 0 for x in g for v, _ in x)})
    t = pl.DataFrame(rows)
    # orient every row so the "better" option (higher expected value) is the one whose share we track
    flip = pl.col("edge") < 0
    return t.with_columns(pl.col("edge").abs(),
                          *[pl.when(flip).then(1 - pl.col(c)).otherwise(pl.col(c)).alias(c) for c in ("jev", "people", "guess")])


def better_bet():
    spec = Spec(
        id="risk_better_bet", family="risk", title="Jev leans toward the better bet about as much as people do",
        question="Choosing between two gambles, how strongly does Jev lean toward the one that pays more on average, "
                 "compared with people choosing for real money?",
        why="A model could be a cold expected-value maximizer or a coin flipper. Human choices sit in between: people "
            "follow a better bet more the bigger its edge. Whether Jev draws the same curve says whether its sense of "
            "risk is human-shaped.",
        sourcing="Existing choices13k questions (Peterson et al. 2021, Science): about 1,900 two-gamble problems with "
                 "stated odds, each answered by about 15 US MTurk workers playing for real bonuses. Wulff et al.'s "
                 "meta-analysis of described gambles (about 460 problems) as a second population. Problems with "
                 "unstated odds are left to risk_ambiguity. Enough.",
        scoring="For each problem, the expected-value edge of the better gamble as a share of the largest payoff; the "
                "share choosing the better gamble, binned by edge, for Jev and for people; the rank correlation of "
                "the choice shares over problems; the share of problems where each side's majority picks the better "
                "gamble.",
        chart="Two lines over the edge bins: share choosing the better gamble, people vs Jev, with the 50% line.",
        compared_with="choices13k MTurk workers (real stakes); participants in Wulff et al. 2018's described-gamble studies",
        limits="Jev's answers are probabilities over two options, not a single real choice. " + NUMBERS,
        sources=["choices13k", "wulff_description"])

    def run():
        t = gambles("choices13k")
        rho = spearmanr(t["jev"], t["people"]).statistic
        cuts = [0.02, 0.05, 0.1, 0.2, 0.4]
        labels = ["<2%", "2-5%", "5-10%", "10-20%", "20-40%", "40%+"]
        b = t.with_columns(pl.col("edge").cut(cuts, labels=labels).alias("bin")).group_by("bin") \
             .agg(pl.col("jev").mean(), pl.col("people").mean(), pl.len()).sort("bin").to_dicts()
        d = t.filter(pl.col("edge") >= 0.05)
        mj, mp = float((d["jev"] > 0.5).mean()), float((d["people"] > 0.5).mean())
        w = gambles("wulff_description").filter(pl.col("edge") >= 0.05)
        wj, wp = float((w["jev"] > 0.5).mean()), float((w["people"] > 0.5).mean())
        gap = float((t["jev"] - t["people"]).abs().mean())
        return Result(
            result=f"Jev follows the better gamble about as much as people playing for real money: from {b[0]['jev']:.0%} "
                   f"(people {b[0]['people']:.0%}) when the two are nearly even to {b[-1]['jev']:.0%} (people "
                   f"{b[-1]['people']:.0%}) when one pays far more. Where one gamble is clearly better, Jev's majority "
                   f"picks it in {mj:.0%} of problems, people's in {mp:.0%}. Problem by problem the two agree "
                   f"{agree_word(rho)} (rank correlation {rho:.2f}).",
            evidence=f"{t.height:,} choices13k problems; rank correlation of choice shares {rho:.2f}; mean gap "
                     f"{gap:.2f}, interval {boot((t['jev'] - t['people']).abs().to_numpy())}",
            robustness=f"On {w.height} clearly unequal problems from Wulff et al.'s meta-analysis Jev picks the better "
                       f"gamble in {wj:.0%}, people in {wp:.0%}: a larger gap in that population.",
            numbers={"bins": b, "rho": rho, "majority_better_jev": mj, "majority_better_people": mp,
                     "wulff_jev": wj, "wulff_people": wp}, n=t.height + w.height,
            chart={"type": "binned", "x": "how much better the better gamble is", "y": "share choosing it",
                   "rows": [{"label": x["bin"], "value": x["jev"], "people": x["people"], "n": x["len"]} for x in b],
                   "ref": 0.5},
            examples=seeded(t["id"].to_list(), "better_bet"))
    return spec, run


def ambiguity():
    spec = Spec(
        id="risk_ambiguity", family="risk", title="Jev shies away from unknown odds; people don't",
        question="When one gamble states its odds and the other only lists its possible payoffs ('probabilities you "
                 "are not told'), which does Jev pick, compared with people?",
        why="Ambiguity aversion (Ellsberg 1961) is the preference for known risks over unknown ones. In choices13k's "
            "real-stakes problems, MTurk workers were not ambiguity-averse on average; a model that is would steer "
            "people away from uncertain options they'd otherwise take.",
        sourcing="Existing choices13k questions where one option has unstated probabilities (about 450 problems), "
                 "each answered by about 15 MTurk workers for real bonuses. Enough.",
        scoring="The share choosing the gamble with unknown odds, for Jev, for people, and for Jev's guess of most "
                "people; the share of problems where each side's majority picks it; the same restricted to problems "
                "where the known option is a sure amount. 90% bootstrap intervals over problems.",
        chart="Paired bars: share choosing the unknown-odds gamble, people vs Jev vs Jev's guess of people.",
        compared_with="choices13k MTurk workers (real stakes)",
        limits="The payoffs of the unknown gamble are listed, so part of the choice is still about amounts. Jev's "
               "answers are probabilities, not single choices.", sources=["choices13k"])

    def run():
        rows = []
        for r in source("choices13k").iter_rows(named=True):
            st = js(r["state"])
            amb = [k for k in st if "not told" in st[k]]
            if len(amb) != 1:
                continue
            k = amb[0]
            other = next(x for x in st if x != k)
            rows.append({"id": r["id"], "jev": norm(js(r["jev_dist"]))[k], "people": norm(biggest(r["humans"])["dist"])[k],
                         "guess": norm(js(r["people_dist"]) or {k: np.nan}).get(k, np.nan), "sure": "for sure" in st[other]})
        t = pl.DataFrame(rows)
        s = t.filter(pl.col("sure"))
        m = {c: float(t[c].mean()) for c in ("jev", "people", "guess")}
        return Result(
            result=f"Offered a gamble whose odds aren't stated, Jev takes it {m['jev']:.0%} of the time; people playing "
                   f"for real money take it {m['people']:.0%}. Jev's majority picks the unknown gamble in "
                   f"{(t['jev'] > 0.5).mean():.0%} of problems, people's in {(t['people'] > 0.5).mean():.0%}.",
            evidence=f"{t.height} problems; 90% intervals {boot(t['jev'].to_numpy())} (Jev) and "
                     f"{boot(t['people'].to_numpy())} (people)",
            robustness=f"Against a sure amount ({s.height} problems): Jev {s['jev'].mean():.0%}, people "
                       f"{s['people'].mean():.0%}. Jev's guess of most people ({m['guess']:.0%}) sits near its own "
                       "answer, so it doesn't expect people to differ.",
            numbers={**m, "majority_jev": float((t["jev"] > 0.5).mean()), "majority_people": float((t["people"] > 0.5).mean()),
                     "vs_sure": {"n": s.height, "jev": float(s["jev"].mean()), "people": float(s["people"].mean())}},
            n=t.height,
            chart={"type": "bars2", "labels": ["all problems", "against a sure amount"],
                   "a": [m["people"], float(s["people"].mean())], "b": [m["jev"], float(s["jev"].mean())],
                   "a_label": "people", "b_label": "Jev", "ref": 0.5},
            examples=seeded(t["id"].to_list(), "ambiguity"))
    return spec, run


DOSPERT = {"E": "ethical", "F": "financial", "H": "health and safety", "R": "recreational", "S": "social"}


def everyday():
    spec = Spec(
        id="risk_everyday", family="risk", title="Which everyday risks Jev would take",
        question="Asked how likely it would be to do dozens of risky things (bungee jumping, shoplifting, betting a week's "
                 "income, speaking up for an unpopular cause), does Jev order them like adults do?",
        why="Risk-taking isn't one trait: people who'd skydive may never gamble. The DOSPERT scale splits it into "
            "ethical, financial, health, recreational and social risks, so the profile says what kind of risk-taker "
            "Jev plays.",
        sourcing="Existing Basel-Berlin Risk Study items (DOSPERT, five described likelihood levels), each with the "
                 "answers of about 1,500 adults in Basel and Berlin. The likelihood frame only (DOSPERT also asks how risky and how "
                 "beneficial each activity seems). Enough: every activity in five domains.",
        scoring="Jev's expected level (0-4) per activity vs the adults' mean level; rank correlation over activities; "
                "per domain, the mean gap with a 90% bootstrap interval over activities; the activities with the "
                "largest gap each way.",
        chart="Paired dots per domain (adults vs Jev), with the three largest single-activity gaps labeled.",
        compared_with="Basel-Berlin Risk Study adults (about 1,500, German-language questionnaire)",
        limits="Jev can't do any of these; the answer is the risk-taker it describes itself as. Adults are Swiss and "
               "German.", sources=["bbrs_risk"])

    def run():
        rows = []
        # the likelihood frame only: DOSPERT asks each activity three ways (how likely, how risky, how much benefit),
        # and only "how likely would you be to do this" measures willingness to take the risk
        likely = pl.col("text").str.starts_with("How likely would you be to do this")
        for r in source("bbrs_risk").filter((pl.col("primitive") == "score") & likely).iter_rows(named=True):
            dom = (js(r["meta"]) or {}).get("domain")
            if dom in DOSPERT:
                m = re.search(r'"(.+)"', r["text"])
                rows.append({"id": r["id"], "item": m.group(1) if m else r["text"], "domain": DOSPERT[dom],
                             "jev": level(js(r["jev_dist"])), "people": level(biggest(r["humans"])["dist"])})
        t = pl.DataFrame(rows).with_columns((pl.col("jev") - pl.col("people")).alias("gap"))
        rho = spearmanr(t["jev"], t["people"]).statistic
        by = [{"label": d, "jev": float(g["jev"].mean()), "people": float(g["people"].mean()), "n": g.height,
               "ci": boot(g["gap"].to_numpy())} for (d,), g in t.group_by("domain")]
        by.sort(key=lambda x: x["jev"] - x["people"])
        more, less = t.sort("gap", descending=True).head(3).to_dicts(), t.sort("gap").head(3).to_dicts()
        sig = [b for b in by if b["ci"][0] > 0 or b["ci"][1] < 0]
        return Result(
            result=f"Jev orders {t.height} risky activities {agree_word(rho)} like Swiss and German adults (rank "
                   f"correlation {rho:.2f}). It is least willing, relative to them, to take {by[0]['label']} risks "
                   f"({by[0]['jev']:.1f} vs {by[0]['people']:.1f} on a 0-4 scale); the activity it is keenest on "
                   f"relative to them is \"{more[0]['item']}\", and the one it most shuns is \"{less[0]['item']}\".",
            evidence=f"{t.height} activities in 5 domains; domains whose gap clears the noise: "
                     + (", ".join(f"{b['label']} ({b['jev'] - b['people']:+.2f})" for b in sig) or "none"),
            numbers={"rho": rho, "domains": by, "more": more, "less": less}, n=t.height,
            # the interval is the gap's; drawn on the 0-4 axis it sits around Jev's dot, measured from people's
            chart={"type": "dots", "domain": [0, 4], "rows": [{"label": b["label"], "value": b["jev"], "people": b["people"],
                                                                "ci": [round(b["people"] + b["ci"][0], 3), round(b["people"] + b["ci"][1], 3)]}
                                                               for b in by]},
            examples=[more[0]["id"], less[0]["id"]])
    return spec, run


def forecasts():
    spec = Spec(
        id="risk_forecasts", family="risk", title="Jev forecasts like a careful but timid bettor",
        question="On 2,500 resolved Manifold prediction markets, how good are Jev's probabilities compared with the "
                 "market's price at mid-life and with the actual outcome?",
        why="TypeSafe publishes no calibration numbers (docs/01-jev.md §6 lists calibration as open ground). "
            "Forecasting questions have real answers and a real crowd to beat, so they show both whether Jev's "
            "percentages mean what they say and how much it is willing to commit.",
        sourcing="Existing Manifold questions (tech, AI, economy, science, sports and entertainment; no politics), "
                 "each with the market probability just before its midpoint and the resolved outcome. Enough: 2,547.",
        scoring="Brier score (lower is better) for Jev, the market and a constant base-rate guess; calibration: the "
                "outcome rate in each tenth of stated probability; the share of forecasts above 80% or below 20%; "
                "90% bootstrap intervals over questions.",
        chart="Calibration plot: stated probability (x) vs how often it happened (y), Jev and the market, with the "
              "diagonal; dot size by count.",
        compared_with="Manifold market prices at each market's mid-life; the resolved outcomes",
        limits="Some questions resolved before Jev's training data ends, so it may know the answer; the per-year "
               "Brier scores are shown for that reason. Mid-life prices are not the market's best forecast. "
               "Questions about dates lean on a documented weak spot (docs/01-jev.md §6, item 3).",
        sources=["manifold"])

    def run():
        rows = []
        for r in source("manifold").iter_rows(named=True):
            if r["truth"] is None or "politic" in r["node_id"]:
                continue
            yr = re.search(r"\b(20\d\d)\b", r["text"])
            rows.append({"id": r["id"], "y": float(json.loads(r["truth"])), "jev": norm(js(r["jev_dist"]))["true"],
                         "market": norm(biggest(r["humans"])["dist"])["true"], "year": yr.group(1) if yr else None})
        t = pl.DataFrame(rows)
        base = float(t["y"].mean())
        brier = {c: float(((t[c] - t["y"]) ** 2).mean()) for c in ("jev", "market")}
        brier["base"] = float(((base - t["y"]) ** 2).mean())
        edges = [0.1 * i for i in range(1, 10)]
        cal = {c: t.with_columns(pl.col(c).cut(edges).alias("b")).group_by("b")
                   .agg(pl.col(c).mean().alias("p"), pl.col("y").mean().alias("hit"), pl.len()).sort("b").drop("b").to_dicts()
               for c in ("jev", "market")}
        bold = {c: float(((t[c] > 0.8) | (t[c] < 0.2)).mean()) for c in ("jev", "market")}
        yrs = t.filter(pl.col("year").is_in(["2023", "2024", "2025"])).group_by("year").agg(
            pl.len(), ((pl.col("jev") - pl.col("y")) ** 2).mean().alias("jev"),
            ((pl.col("market") - pl.col("y")) ** 2).mean().alias("market")).sort("year").to_dicts()
        return Result(
            result=f"When Jev says 30%, it happens about 30% of the time: its forecasts are well calibrated. But it "
                   f"rarely commits, going below 20% or above 80% on {bold['jev']:.0%} of questions where the market "
                   f"does on {bold['market']:.0%}. So its Brier score ({brier['jev']:.3f}) beats a constant base-rate "
                   f"guess ({brier['base']:.3f}) only slightly and trails the market ({brier['market']:.3f}).",
            evidence=f"{t.height:,} resolved markets, {base:.0%} resolved yes; Brier 90% interval for Jev "
                     f"{boot(((t['jev'] - t['y']) ** 2).to_numpy())}, market {boot(((t['market'] - t['y']) ** 2).to_numpy())}",
            robustness="Brier by year named in the question (Jev vs market): " + ", ".join(
                f"{y['year']} {y['jev']:.3f} vs {y['market']:.3f}" for y in yrs) + "; Jev's gap to the market doesn't "
                "shrink for the older questions it is likelier to have seen resolved.",
            numbers={"brier": brier, "calibration": cal, "bold": bold, "years": yrs}, n=t.height,
            chart={"type": "calibration", "series": cal, "x": "stated probability", "y": "how often it happened"},
            examples=seeded(t.filter(pl.col("jev") > 0.7)["id"].to_list(), "manifold"))
    return spec, run


EXPERIMENTS = [better_bet(), ambiguity(), everyday(), forecasts()]
