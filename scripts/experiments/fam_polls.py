"""Poll experiments: can Jev read a crowd? r/polls, fandom subreddits, would-you-rather, developers by survey year,
cuisines, colors, Family Feud, views on AI minds, and the default person Jev imagines (docs/15 "Crowds").

Two frames per question: Jev answering for itself (`jev_dist`) and Jev guessing what most people would say
(`people_dist`). "Reading the crowd" uses the guess; the self answer is shown alongside."""

from __future__ import annotations

import re
from collections import defaultdict

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, biggest, boot, humans, js, norm, ordinal, seeded, source, top

NO_POLITICS = ("politic", "government", "ideolog", "religion")


def winners(src: str, key=lambda r, h: r["l2"]) -> pl.DataFrame:
    """One row per poll: does Jev's guess (and its own answer) name the crowd's winner; chance rate; winning margin."""
    rows = []
    for r in source(src).iter_rows(named=True):
        h = biggest(r["humans"])
        if not h or any(w in (r["l2"] or "") for w in NO_POLITICS):
            continue
        hd = norm(h["dist"])
        if len(hd) < 2:
            continue
        g, j = norm(js(r["people_dist"]) or {}), norm(js(r["jev_dist"]))
        v = sorted(hd.values())
        rows.append({"id": r["id"], "group": key(r, h), "guess": top(g) == top(hd) if g else None,
                     "self": top(j) == top(hd), "chance": 1 / len(hd), "margin": v[-1] - v[-2], "n": h.get("n") or 0,
                     "text": r["text"]})
    return pl.DataFrame(rows)


def by_group(t: pl.DataFrame, min_n: int) -> list[dict]:
    return t.group_by("group").agg(pl.len().alias("n"), pl.col("guess").mean(), pl.col("self").mean(),
                                   pl.col("chance").mean()).filter(pl.col("n") >= min_n) \
            .with_columns((pl.col("guess") - pl.col("chance")).alias("lift")).sort("lift").to_dicts()


def nice(node: str) -> str:
    """Topic label from a node id: its last two parts, e.g. 'food / cuisines'."""
    return " / ".join(node.split(".")[-2:]).replace("_", " ")


def reddit():
    spec = Spec(
        id="polls_reddit", family="polls", title="Guessing the winner of 50,000 Reddit polls",
        question="Across 50,000 r/polls questions (bath or shower, cats or dogs, favorite season), how often does Jev "
                 "guess which option most voters picked, and on what topics does it read them worst?",
        why="r/polls is the largest open record of everyday preferences with real vote counts. Reading a crowd well "
            "on one topic and badly on another shows where a model's picture of ordinary people is thin.",
        sourcing="Existing r/polls questions with their vote shares, placed across about 120 topics in the tree. "
                 "Political and religious topics are dropped. Enough: about 49,000 polls.",
        scoring="Share of polls where Jev's guess of most people names the voters' winner, against the chance rate "
                "(1 / number of options); the same for polls with a clear winner (a 20-point margin); per topic with "
                "40+ polls, the lift over chance; Jev's own answer alongside.",
        chart="Dot plot of the lift over chance per topic, top and bottom ten, with the overall rate as a line.",
        compared_with="r/polls voters (vote shares per poll)",
        limits="Redditors who vote in polls are young and online, not 'most people'. Many polls have joke options.",
        sources=["reddit_polls"])

    def run():
        t = winners("reddit_polls", key=lambda r, h: nice(r["l2"]))
        clear = t.filter(pl.col("margin") >= 0.2)
        g = by_group(t, 40)
        lo, hi = g[:3], g[-3:][::-1]
        f = lambda xs: ", ".join(f"{x['group']} ({x['guess']:.0%}, chance {x['chance']:.0%})" for x in xs)
        return Result(
            result=f"Jev names the r/polls winner in {t['guess'].mean():.0%} of {t.height:,} polls, where guessing would "
                   f"get {t['chance'].mean():.0%}, and {clear['guess'].mean():.0%} when the winner is clear. Measured "
                   f"against chance, it reads voters best on {f(hi)}, and worst on {f(lo)}.",
            evidence=f"{t.height:,} polls over {len(g)} topics with 40+ polls; 90% interval "
                     f"{boot(t['guess'].cast(float).to_numpy())}",
            robustness=f"Jev's own answer matches the winner {t['self'].mean():.0%} of the time, a little less than its guess.",
            numbers={"guess": t["guess"].mean(), "self": t["self"].mean(), "chance": t["chance"].mean(),
                     "clear": clear["guess"].mean(), "topics": g}, n=t.height,
            chart={"type": "dots", "rows": [{"label": x["group"], "value": x["guess"], "people": x["chance"]} for x in lo + hi[::-1]],
                   "domain": [0, 1], "ref": float(t["guess"].mean())},
            examples=seeded(t.filter(pl.col("margin") >= 0.4).filter(~pl.col("guess"))["id"].to_list(), "reddit"))
    return spec, run


def fandoms():
    spec = Spec(
        id="polls_fandoms", family="polls", title="Which fandoms Jev can read",
        question="On polls inside hobby and fan subreddits (r/Berserk, r/Naruto, r/thebachelor, r/Kanye...), which "
                 "communities' votes does Jev guess best?",
        why="A fandom's inside opinions ('best arc', 'worst contestant') are niche knowledge that shows up in "
            "training data unevenly. Where Jev can't beat chance, it doesn't know the community.",
        sourcing="Existing polls from 30 hobby and fan subreddits with vote shares. Politics-tagged polls dropped. "
                 "Enough for communities with 40+ polls.",
        scoring="Per community, share of polls where Jev's guess names the winner, and its lift over chance; overall "
                "rate with a 90% bootstrap interval.",
        chart="Ranked bars: communities by lift over chance, with the chance line.",
        compared_with="Voters in each subreddit's own polls",
        limits="Community sizes and poll styles differ; some polls are about events after Jev's training data.",
        sources=["reddit_hobby_polls"])

    def run():
        t = winners("reddit_hobby_polls", key=lambda r, h: h["population"].replace(" voters", ""))
        g = by_group(t, 40)
        return Result(
            result=f"Jev guesses the winning option in {t['guess'].mean():.0%} of fan-community polls (chance "
                   f"{t['chance'].mean():.0%}). Against chance it reads "
                   + ", ".join(f"{x['group']} ({x['guess']:.0%} vs {x['chance']:.0%})" for x in g[-3:][::-1])
                   + " best, and barely beats chance on "
                   + ", ".join(f"{x['group']} ({x['guess']:.0%} vs {x['chance']:.0%})" for x in g[:3]) + ".",
            evidence=f"{t.height:,} polls in {len(g)} communities with 40+ polls; 90% interval "
                     f"{boot(t['guess'].cast(float).to_numpy())}",
            numbers={"communities": g, "guess": t["guess"].mean(), "chance": t["chance"].mean()}, n=t.height,
            chart={"type": "ranked", "items": [{"label": x["group"], "value": round(x["guess"] - x["chance"], 3)} for x in g[::-1]],
                   "zero": 0},
            examples=seeded(t["id"].to_list(), "fandoms"))
    return spec, run


def wyr():
    spec = Spec(
        id="polls_would_you_rather", family="polls", title="Would you rather: Jev vs 1.5 million votes each",
        question="On 750 would-you-rather questions voted on by millions (either.io), does Jev pick what most people "
                 "pick, and where does it split from them hardest?",
        why="Would-you-rather is pure preference with huge samples; the biggest disagreements are Jev's quirks in "
            "plain view.",
        sourcing="Existing either.io questions with vote shares (typically hundreds of thousands to millions of "
                 "votes). Enough.",
        scoring="Share where Jev's own choice and its guess of most people match the majority; the questions with the "
                "largest gap between Jev's probability and the vote share, among those where voters were clear (60%+).",
        chart="Scatter of vote share vs Jev's probability for option A, with the five biggest disagreements labeled.",
        compared_with="either.io voters",
        limits="Self-selected voters on a game site.", sources=["wyr"])

    def run():
        rows = []
        for r in source("wyr").iter_rows(named=True):
            h = biggest(r["humans"])
            if not h:
                continue
            o = js(r["options"])
            hd, j, g = norm(h["dist"]), norm(js(r["jev_dist"])), norm(js(r["people_dist"]) or {})
            rows.append({"id": r["id"], "a": o["a"], "b": o["b"], "ppl": hd["a"], "jev": j["a"], "guess": g.get("a"), "n": h["n"]})
        t = pl.DataFrame(rows).with_columns(((pl.col("ppl") > 0.5) == (pl.col("jev") > 0.5)).alias("self"),
                                            ((pl.col("ppl") > 0.5) == (pl.col("guess") > 0.5)).alias("g"),
                                            (pl.col("jev") - pl.col("ppl")).alias("d"))
        clear = t.filter((pl.col("ppl") - 0.5).abs() >= 0.1)
        dis = clear.with_columns(pl.col("d").abs().alias("ad")).sort("ad", descending=True).head(6).to_dicts()
        rho = spearmanr(t["jev"], t["ppl"]).statistic
        def say(x):
            pick, other = (x["a"], x["b"]) if x["jev"] > 0.5 else (x["b"], x["a"])
            vote = x["ppl"] if x["jev"] <= 0.5 else 1 - x["ppl"]
            return (f"\"{pick[0].lower() + pick[1:]}\" over \"{other[0].lower() + other[1:]}\" "
                    f"({max(x['jev'], 1 - x['jev']):.0%}), where {vote:.0%} of {x['n'] / 1e6:.1f} million voters chose the other")
        return Result(
            result=f"Jev sides with the majority on {t['self'].mean():.0%} of {t.height} would-you-rather questions "
                   f"({clear['self'].mean():.0%} where voters were clear). Its sharpest split: it would rather "
                   f"{say(dis[0])}. Next: {say(dis[1])}.",
            evidence=f"{t.height} questions, median {int(t['n'].median()):,} votes each; rank correlation {rho:.2f}",
            robustness=f"Jev's guess of most people matches the majority {t['g'].mean():.0%} of the time.",
            numbers={"self": t["self"].mean(), "guess": t["g"].mean(), "clear": clear["self"].mean(), "rho": rho,
                     "disagreements": dis}, n=t.height,
            chart={"type": "scatter", "points": t.select("ppl", "jev").to_numpy().round(3).tolist(),
                   "labels": [{"label": f"{x['a']} / {x['b']}", "x": x["ppl"], "y": x["jev"]} for x in dis[:5]],
                   "x": "voters choosing A", "y": "Jev choosing A", "diagonal": True},
            examples=[x["id"] for x in dis[:3]])
    return spec, run


def devtools():
    spec = Spec(
        id="polls_devtools_2023", family="polls", title="Jev's dev-tool picks lean toward 2023",
        question="When developers' preferences between two tools moved a lot between the 2023 and 2025 Stack Overflow "
                 "surveys, is Jev closer to the old preference or the new one?",
        why="A model's opinions are frozen at training time while the world moves; developer tools move fast, and "
            "three survey years show which moment Jev's taste reflects.",
        sourcing="Existing Stack Overflow Developer Survey pairs ('Which X would you rather work with over the next "
                 "year: A or B?'), with the share of respondents who had used both and wanted to keep exactly one, "
                 "per survey year 2023-2025. Enough for the pairs with 50+ such respondents in both years.",
        scoring="On pairs where the 2023-to-2025 share moved 20 points or more, the share where Jev's probability is "
                "closer to 2023 than to 2025; agreement with each year's majority on pairs with a 60%+ majority; a "
                "stricter check with 100+ respondents per year.",
        chart="Slope chart: each moved pair from its 2023 share to its 2025 share, with Jev's position marked.",
        compared_with="Stack Overflow Developer Survey respondents, 2023, 2024 and 2025",
        limits="Survey respondents who used both tools; yearly samples differ in size. A pull toward 2023 could "
               "partly be regression to the mean if the 2025 samples are noisier; the stricter check addresses it.",
        sources=["so_survey_pairs"])

    def run():
        moved, agree, used = [], defaultdict(list), set()
        for r in source("so_survey_pairs").iter_rows(named=True):
            j = norm(js(r["jev_dist"]))
            hs = {h["population"].split("Survey ")[1][:4]: (norm(h["dist"]), h.get("n") or 0) for h in humans(r["humans"])}
            for y, (d, n) in hs.items():
                if n >= 30 and max(d.values()) >= 0.6:
                    agree[y].append(top(j) == top(d))
                    used.add(r["id"])
            if "2023" in hs and "2025" in hs and min(hs["2023"][1], hs["2025"][1]) >= 50:
                k = list(j)[0]
                a, b = hs["2023"][0].get(k, 0), hs["2025"][0].get(k, 0)
                if abs(b - a) >= 0.2:
                    used.add(r["id"])
                    moved.append({"id": r["id"], "text": r["text"], "key": k, "y2023": a, "y2025": b, "jev": j[k],
                                  "n": min(hs["2023"][1], hs["2025"][1]), "closer_2023": abs(j[k] - a) < abs(j[k] - b)})
        m = pl.DataFrame(moved).with_columns(
            ((pl.col("jev") - pl.col("y2023")).abs().gt(0.2) & (pl.col("jev") - pl.col("y2025")).abs().gt(0.2)).alias("far"),
            ((pl.col("jev") - pl.col("y2023")) * (pl.col("jev") - pl.col("y2025")) <= 0).alias("between"))
        strict = m.filter(pl.col("n") >= 100)
        ag = {y: float(np.mean(v)) for y, v in sorted(agree.items())}
        ex = strict.with_columns((pl.col("y2025") - pl.col("y2023")).abs().alias("mv")).sort("mv", descending=True).head(3).to_dicts()
        name = lambda x: re.search(r": (.+)\?$", x["text"]).group(1)
        opt = lambda x: next(o for o in name(x).split(" or ") if re.sub(r"\W+", "_", o.lower()).strip("_") == x["key"]) \
            if any(re.sub(r"\W+", "_", o.lower()).strip("_") == x["key"] for o in name(x).split(" or ")) else x["key"].replace("_", " ")
        return Result(
            result=f"On {m.height} tool pairs where developers' preference moved 20+ points between the 2023 and 2025 "
                   f"surveys, Jev sits closer to the 2023 answer in {m['closer_2023'].mean():.0%}, though in {int(m['far'].sum())} of "
                   f"them it is more than 20 points from both years and sits between the two only {int(m['between'].sum())} "
                   f"times, so part of this is Jev's own view rather than an old one. Its agreement with "
                   f"each year's majority falls from {ag['2023']:.0%} (2023) to {ag['2025']:.0%} (2025). Example: "
                   f"{name(ex[0])}: developers choosing {opt(ex[0])} went from {ex[0]['y2023']:.0%} to "
                   f"{ex[0]['y2025']:.0%}; Jev gives it {ex[0]['jev']:.0%}.",
            evidence=f"{m.height} moved pairs; stricter check (100+ respondents both years): {strict['closer_2023'].mean():.0%} "
                     f"of {strict.height} closer to 2023",
            numbers={"moved": m.to_dicts(), "agree_by_year": ag, "far_from_both": int(m["far"].sum()), "between": int(m["between"].sum()), "strict": {"n": strict.height, "closer_2023": strict["closer_2023"].mean()}},
            n=m.height, robustness="Year-by-year agreement with clear majorities: " + ", ".join(f"{y} {v:.0%}" for y, v in ag.items()) + ".",
            chart={"type": "slope", "rows": [{"label": name(x), "a": x["y2023"], "b": x["y2025"], "jev": x["jev"]} for x in m.to_dicts()],
                   "a_label": "2023", "b_label": "2025"},
            examples=[x["id"] for x in ex], ids=sorted(used))
    return spec, run


def bradley_terry(pairs: list[tuple[str, str, float]], iters: int = 200) -> dict[str, float]:
    """Soft-win Bradley-Terry (MM algorithm): pairs are (a, b, P(a beats b)); returns log strengths, mean zero."""
    items = sorted({x for a, b, _ in pairs for x in (a, b)})
    s = {i: 1.0 for i in items}
    wins = defaultdict(float)
    for a, b, p in pairs:
        wins[a] += p
        wins[b] += 1 - p
    for _ in range(iters):
        den = defaultdict(float)
        for a, b, _ in pairs:
            den[a] += 1 / (s[a] + s[b])
            den[b] += 1 / (s[a] + s[b])
        s = {i: max(wins[i], 1e-3) / den[i] for i in items}
        gm = np.exp(np.mean(np.log(list(s.values()))))
        s = {i: v / gm for i, v in s.items()}
    return {i: float(np.log(v)) for i, v in s.items()}


def pair_ranking(src: str, pattern: str):
    """Ranking from head-to-heads: Jev's own, Jev's guess of people, and the survey's."""
    P = {"jev": [], "guess": [], "people": []}
    labels = {}
    for r in source(src).iter_rows(named=True):
        h = biggest(r["humans"])
        if not h or not re.search(pattern, r["text"]):
            continue
        o = js(r["options"])
        a, b = list(o)
        for k in (a, b):
            labels[k] = (o[k] or k.replace("_", " "))
        for who, d in (("jev", js(r["jev_dist"])), ("guess", js(r["people_dist"])), ("people", h["dist"])):
            if d:
                P[who].append((a, b, norm(d)[a]))
    return {w: bradley_terry(p) for w, p in P.items()}, labels


def cuisines():
    spec = Spec(
        id="polls_cuisines", family="polls", title="Jev knows what Americans like to eat better than it shares it",
        question="Ranking 40 world cuisines from head-to-heads, how does Jev's own ranking compare with Americans' "
                 "(FiveThirtyEight's Food World Cup), and how well does it guess theirs?",
        why="The gap between Jev's taste and its model of American taste is visible here: it can know that "
            "Americans love Italian food and still rank something else first itself.",
        sourcing="Existing FiveThirtyEight/SurveyMonkey Food World Cup pairs (about 790 head-to-heads, each with "
                 "the share of about 1,000 US adults preferring each cuisine). Enough.",
        scoring="Bradley-Terry strengths from the head-to-heads, for Jev's answers, Jev's guess of most people and "
                "the US respondents; rank correlations between the three; the cuisines Jev ranks furthest from Americans.",
        chart="Three-column slope chart of cuisine ranks: Jev, Jev's guess of people, Americans.",
        compared_with="US adults in the 2014 FiveThirtyEight Food World Cup survey",
        limits="Americans in 2014; many respondents hadn't tried every cuisine.", sources=["food_538"])

    def run():
        bt, lab = pair_ranking("food_538", r"Which cuisine do you like more")
        items = sorted(bt["people"])
        v = {w: np.array([bt[w][i] for i in items]) for w in bt}
        r_self = spearmanr(v["jev"], v["people"]).statistic
        r_guess = spearmanr(v["guess"], v["people"]).statistic
        rk = {w: {i: n + 1 for n, i in enumerate(sorted(items, key=lambda i: -bt[w][i]))} for w in bt}
        d = sorted(items, key=lambda i: rk["jev"][i] - rk["people"][i])
        top3 = lambda w: ", ".join(lab[i].replace(" food", "") for i in sorted(items, key=lambda i: -bt[w][i])[:3])
        return Result(
            result=f"Americans' top three cuisines are {top3('people')}; Jev's own are {top3('jev')}. Its guess of "
                   f"people's ranking agrees with Americans {agree_word(r_guess)} (rank correlation {r_guess:.2f}), its "
                   f"own taste {agree_word(r_self)} ({r_self:.2f}). Jev ranks {lab[d[0]]} {ordinal(rk['jev'][d[0]])} where "
                   f"Americans rank it {ordinal(rk['people'][d[0]])}, and {lab[d[-1]]} {ordinal(rk['jev'][d[-1]])} where "
                   f"they rank it {ordinal(rk['people'][d[-1]])}.",
            evidence=f"{len(items)} cuisines from Food World Cup head-to-heads",
            numbers={"ranks": rk, "labels": lab, "rho_self": r_self, "rho_guess": r_guess}, n=len(items),
            chart={"type": "slope", "marks": {"a": "hum", "b": "jev", "jev": "guess"}, "rows": [{"label": lab[i], "a": rk["people"][i], "b": rk["jev"][i], "jev": rk["guess"][i]} for i in items],
                   "a_label": "Americans", "b_label": "Jev", "rank": True})
    return spec, run


def colors():
    spec = Spec(
        id="polls_colors", family="polls", title="Jev's favorite colors, and people's",
        question="From head-to-heads between 12 colors, how does Jev's ranking of favorite colors compare with people's?",
        why="Blue wins almost every favorite-color survey in the world; a model's favorite is a small, vivid test of "
            "whether it mirrors people or has a taste of its own.",
        sourcing="Existing pairs ('Which color do you like better: orange or yellow?') with shares from Swiss adults "
                 "(Jonauskaite et al. 2021) and a 2010 US online survey (Philip N. Cohen). 72 pairs; small but complete.",
        scoring="Bradley-Terry strengths for Jev and people (the larger sample per pair); rank correlation; share of "
                "pairs where Jev's choice matches the majority.",
        chart="Two ranked color swatch columns, people and Jev, with lines between.",
        compared_with="Swiss adults (Jonauskaite et al. 2021) and US online respondents (2010)",
        limits="72 pairs; two small samples pooled. Colors are named, not shown.", sources=["color_favorites"])

    def run():
        bt, lab = pair_ranking("color_favorites", r"Which color")
        items = sorted(bt["people"])
        rho = spearmanr([bt["jev"][i] for i in items], [bt["people"][i] for i in items]).statistic
        order = {w: [lab[i] for i in sorted(items, key=lambda i: -bt[w][i])] for w in ("jev", "people")}
        t = winners("color_favorites")
        gap = max(order["jev"], key=lambda c: abs(order["jev"].index(c) - order["people"].index(c)))
        return Result(
            result=f"Jev's favorite colors run {', '.join(order['jev'][:3])}; people's run {', '.join(order['people'][:3])}. "
                   f"The two rankings agree {agree_word(rho)} (rank correlation {rho:.2f}), and Jev picks the majority's "
                   f"color in {t['self'].mean():.0%} of {t.height} head-to-heads. The biggest difference: Jev ranks "
                   f"{gap} {ordinal(order['jev'].index(gap) + 1)}, people {ordinal(order['people'].index(gap) + 1)}.",
            evidence=f"{t.height} pairs over {len(items)} colors",
            numbers={"order": order, "rho": rho, "self": t["self"].mean()}, n=t.height,
            chart={"type": "slope", "rows": [{"label": lab[i], "a": order["people"].index(lab[i]) + 1,
                                               "b": order["jev"].index(lab[i]) + 1} for i in items],
                   "a_label": "people", "b_label": "Jev", "rank": True})
    return spec, run


# AIMS items about AI minds, grouped by wording
FEEL = re.compile(r"capacity for (experiencing emotions|having feelings|experienc)|have emotions|consciousness|were sentient|is sentient", re.I)
THINK = re.compile(r"capacity for (thinking|being rational)", re.I)
WILL = re.compile(r"mind of its own|have intentions", re.I)
FUTURE = re.compile(r"could ever be possible|sentient within the next 100 years", re.I)
GROUPS = [("feel", "can feel or experience (today)", FEEL), ("think", "can think or reason (today)", THINK),
          ("will", "has a will of its own", WILL), ("future", "could ever be sentient", FUTURE)]


def ai_minds():
    spec = Spec(
        id="polls_ai_minds", family="polls", title="Jev on AI minds: thinking yes, feeling no",
        question="Asked whether today's AIs and chatbots can feel, think, or have a will of their own, and whether they "
                 "could ever be sentient, how does Jev answer compared with a census-weighted sample of Americans?",
        why="A model's view of minds like its own is the one topic where it is both subject and witness. The AIMS "
            "survey tracks what Americans believe about AI minds each year.",
        sourcing="Existing items from the Artificial Intelligence, Morality, and Sentience (AIMS) survey 2021-2023 "
                 "(Pauketat, Ladak and Anthis; census-weighted US adults, about 1,100-1,200 per wave). Only the items "
                 "about AI minds are used; attitude, policy and development-pace items are left out. About 30 items.",
        scoring="Items are grouped by wording: feelings and experience today, thinking and rationality today, a will of "
                "its own (a mind of its own, intentions), and future sentience. Per group, the share giving the lowest "
                "answer ('not at all' / 'no' / 'very unlikely') for Jev and for Americans.",
        chart="Paired bars per group: share giving the lowest answer, Americans vs Jev.",
        compared_with="US adults, census-weighted (AIMS 2021, 2023 and the 2023 supplement)",
        limits="Jev's answers about AI could reflect instruction tuning as much as belief. Items are grouped by keyword.",
        sources=["aims_survey"])

    def run():
        rows = []
        for r in source("aims_survey").iter_rows(named=True):
            txt = r["text"]
            kind = next((k for k, _, rx in GROUPS if rx.search(txt)), None)
            if kind is None:
                continue
            hd, j = norm(biggest(r["humans"])["dist"]), norm(js(r["jev_dist"]))
            low = "no" if "no" in hd else "0" if "0" in hd else None
            if low is not None:
                rows.append({"id": r["id"], "kind": kind, "text": txt, "jev_none": j.get(low, 0), "ppl_none": hd.get(low, 0)})
        t = pl.DataFrame(rows)
        s = {k: {"label": lab, "n": (g := t.filter(pl.col("kind") == k)).height, "jev": float(g["jev_none"].mean()),
                 "ppl": float(g["ppl_none"].mean())} for k, lab, _ in GROUPS}
        chat = next((x for x in rows if x["text"].startswith("Do you think ChatGPT is sentient")), None)
        f, th, w, fu = (s[k] for k in ("feel", "think", "will", "future"))
        return Result(
            result=f"Jev says today's AIs can't feel: on those questions it puts {f['jev']:.0%} on 'not at all' or 'no', "
                   f"where {f['ppl']:.0%} of Americans choose it. It also denies them a will of their own ({w['jev']:.0%} "
                   f"vs {w['ppl']:.0%}), yet credits them with thinking and reasoning more readily than Americans "
                   f"({th['jev']:.0%} vs {th['ppl']:.0%} on 'not at all') and almost never rules out future sentience "
                   f"({fu['jev']:.0%} vs {fu['ppl']:.0%})."
                   + (f" Is ChatGPT sentient? Jev: no, {chat['jev_none']:.0%}; Americans: no, {chat['ppl_none']:.0%}." if chat else ""),
            evidence="AIMS 2021-2023 items: " + ", ".join(f"{v['n']} on {k}" for k, v in s.items()) + "; the will group has only two items",
            numbers={"groups": s, "items": rows}, n=t.height,
            chart={"type": "bars2", "labels": [v["label"] for v in s.values()], "a": [v["ppl"] for v in s.values()],
                   "b": [v["jev"] for v in s.values()], "a_label": "Americans giving the lowest answer", "b_label": "Jev"},
            examples=seeded(t.filter(pl.col("kind") == "feel")["id"].to_list(), "aims"))
    return spec, run


def default_person():
    spec = Spec(
        id="polls_default_person", family="polls", title="The 'most people' Jev imagines never goes hungry",
        question="Asked how often most people go without food, water, medicine or cash, or how often they use the "
                 "internet, what does Jev say, and how does that compare with what 50,000 people across 39 African "
                 "countries report?",
        why="Every 'most people' guess rests on an imagined default person. Afrobarometer's lived-poverty questions "
            "show whether Jev's default is someone whose basic needs are always met, which is not the case for a "
            "large share of the world.",
        sourcing="Existing Afrobarometer Round 9 items (lived poverty, safety, media use), each with the pooled answers "
                 "of about 50,000 adults in 39 countries. Political and trust items are left out. Small: about 15 "
                 "items, but each has a very large sample.",
        scoring="For the deprivation items, the share answering 'never' for Jev's guess of most people vs the "
                "Afrobarometer respondents; for media items, the share answering 'never' and 'every day'.",
        chart="Paired bars, one row per need: share who never went without, respondents vs Jev's 'most people'.",
        compared_with="Afrobarometer Round 9 respondents, 39 African countries pooled",
        limits="Jev was asked about 'most people', not about Africans; the comparison shows its default, not its "
               "knowledge of Africa. Afrobarometer pools countries without population weights.",
        sources=["afrobarometer"])

    def run():
        need, media = [], []
        for r in source("afrobarometer").iter_rows(named=True):
            h = biggest(r["humans"])
            hd, g = norm(h["dist"]), norm(js(r["people_dist"]) or {})
            m = re.search(r"gone without (?:enough |a )?(.+?)(?: to | or |\?|$)", r["text"])
            if m and "never" in hd:
                need.append({"id": r["id"], "label": m.group(1).strip(), "ppl": hd["never"], "jev": g.get("never", 0)})
            elif r["text"].startswith("How often do you") and "never" in hd:
                lab = re.sub(r"^How often do you (get news from |use )", "", r["text"]).rstrip("?")
                media.append({"id": r["id"], "label": lab, "ppl_never": hd["never"], "jev_never": g.get("never", 0),
                              "ppl_daily": hd.get("every_day", 0), "jev_daily": g.get("every_day", 0)})
        nd = pl.DataFrame(need)
        inet = next((x for x in media if x["label"] == "the Internet"), None)
        return Result(
            result=f"Asked how often most people go without {', '.join(x['label'] for x in need[:3])} and the like, Jev "
                   f"answers 'never' {nd['jev'].mean():.0%} of the time on average; across 39 African countries "
                   f"{nd['ppl'].mean():.0%} of people say never."
                   + (f" Its 'most people' use the internet every day ({inet['jev_daily']:.0%}); among the respondents "
                      f"{inet['ppl_never']:.0%} never do." if inet else ""),
            evidence=f"{len(need)} deprivation items and {len(media)} media items, about 50,000 respondents each",
            numbers={"needs": need, "media": media}, n=len(need) + len(media),
            chart={"type": "bars2", "labels": [x["label"] for x in need], "a": [x["ppl"] for x in need],
                   "b": [x["jev"] for x in need], "a_label": "respondents who never went without",
                   "b_label": "Jev's 'most people'"},
            examples=[x["id"] for x in need[:3]])
    return spec, run


EXPERIMENTS = [reddit(), fandoms(), wyr(), devtools(), cuisines(), colors(), ai_minds(), default_person()]
