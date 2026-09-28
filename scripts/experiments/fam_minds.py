"""Minds experiments on new questions (docs/15 E20, E41, E42, E18): who has a mind, colors of feelings, the first word
that comes to mind, and an AI's feelings about AI."""

from __future__ import annotations

import re

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, jsd, norm, ordinal, seeded, top, with_meta


def the(country: str) -> str:
    return f"the {country}" if country.startswith(("United", "Netherlands", "Czech", "Philippines")) else country


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and its order variants: shuffled options for a Choice, reversed
    levels for a Score (stored mapped back to the original order)."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or []
                                     if v.get("kind") in ("shuffle", "reversed_levels") and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def exp_level(d: dict) -> float:
    d = norm(d)
    return sum(int(k) * v for k, v in d.items() if str(k).isdigit())


# ---- 1-2. mind perception ------------------------------------------------------------------------------------------------
NAMES = {"charlie_dog": "the dog", "delores_gleitman_deceased": "the dead woman", "fetus": "the fetus",
         "gerald_schiff_pvs": "the man in a vegetative state", "god": "God", "green_frog": "the frog",
         "kismet_robot": "Kismet the robot", "nicholas_gannon_baby": "the baby", "samantha_hill_girl": "the 5-year-old",
         "sharon_harvey_woman": "the woman", "toby_chimp": "the chimpanzee", "todd_billingsley_man": "the man", "you": "you"}
CAP = {"Fear": "feel fear", "Hunger": "feel hunger", "Morality": "tell right from wrong", "SelfControl": "exercise self-control"}
# the screen hid many of these characters' pairs (flagged sensitive), so they are left out and every score uses the
# same complete set of pairs among the other 11 for Jev and people
DROPPED = {"fetus", "god"}
MIND_SOURCING = ("New questions (sources/mind_perception): Gray, Gray & Wegner's 2007 design as run in Weisman's public "
                 "replication: 13 characters with the original descriptions, all 78 pairs, 'Which character is more "
                 "capable of <capacity>?' on the study's 5-point scale, for fear and hunger (Experience) and morality and "
                 "self-control (Agency). 312 questions; 11-16 US MTurk adults per capacity answered every pair.")
MIND_LIMITS = ("The human side is a small replication (11-16 people per capacity), so single pairs are noisy and the "
               "comparison is made on character scores averaged over 10 pairs each. Four of the original 18 capacities. "
               "'You' is the respondent: a person for people, Jev for Jev. The fetus and God were left out: the question "
               "screen hid 28 of their pairs as sensitive, so the map uses the 55 pairs among the other 11 characters. "
               "The replication's repository states no license; its data are used here for private research only.")


def mind_scores() -> dict:
    """Per capacity and character: mean advantage over the 12 other characters (-2..2), for Jev (base and reversed
    averaged), Jev's 'most people' answer, and people."""
    acc: dict[str, dict[str, dict[str, list]]] = {}
    for r in with_meta("mind_perception"):
        m = r["m"]
        if m["a"] in DROPPED or m["b"] in DROPPED:
            continue
        h = biggest(r["humans"])
        vals = {"jev": exp_level(robust(r)), "guess": exp_level(js(r["people_dist"]) or {"2": 1}),
                "people": exp_level(h["dist"]) if h else None}
        for who, v in vals.items():
            if v is None:
                continue
            d = acc.setdefault(who, {}).setdefault(m["capacity"], {})
            d.setdefault(m["a"], []).append(2 - v)  # level 0 = much more the first character
            d.setdefault(m["b"], []).append(v - 2)
    return {who: {cap: {c: float(np.mean(v)) for c, v in cs.items()} for cap, cs in caps.items()} for who, caps in acc.items()}


def mind_map():
    spec = Spec(
        id="minds_mind_map", family="minds", title="Who has a mind? Jev's map next to people's",
        question="Placing a frog, a dog, a baby, a man in a vegetative state, God and a robot on two axes, feeling "
                 "(Experience) and doing (Agency), does Jev draw the same map of minds as people?",
        why="Gray, Gray and Wegner's 2007 map is one of psychology's most reproduced figures: people give babies and "
            "animals feelings but little agency, God agency but few feelings, robots a little agency and no feelings. "
            "A model's version of the map shows what it assumes about minds, including machine ones.",
        sourcing=MIND_SOURCING, collection="312 new questions, each asked as written, for 'most people', and with the "
                                          "levels reversed (averaged).",
        scoring="Per capacity, each character's mean advantage in its 12 comparisons (-2 to +2); Experience = mean of fear "
                "and hunger, Agency = mean of morality and self-control. Rank correlation of the 13 characters between "
                "Jev and people on each axis, with a 90% bootstrap interval over characters; the characters Jev moves most.",
        chart="The Gray et al. map: Experience (x) by Agency (y), each character as a Jev dot joined to a people dot.",
        compared_with="US adults in a replication of Gray et al. 2007 (Weisman, 2015)", limits=MIND_LIMITS,
        new_questions=312, sources=["mind_perception"])

    def run():
        s = mind_scores()
        axes = lambda d, c: ((d["Fear"][c] + d["Hunger"][c]) / 2, (d["Morality"][c] + d["SelfControl"][c]) / 2)  # noqa: E731
        chars = sorted(s["people"]["Fear"])
        pts = {w: {c: axes(s[w], c) for c in chars} for w in ("jev", "people", "guess")}
        rx = spearmanr([pts["jev"][c][0] for c in chars], [pts["people"][c][0] for c in chars]).statistic
        ry = spearmanr([pts["jev"][c][1] for c in chars], [pts["people"][c][1] for c in chars]).statistic
        idx = np.arange(len(chars))
        ci_x = boot(idx, stat=lambda ii: spearmanr([pts["jev"][chars[int(i)]][0] for i in ii], [pts["people"][chars[int(i)]][0] for i in ii]).statistic, b=300)
        move = sorted(((np.hypot(pts["jev"][c][0] - pts["people"][c][0], pts["jev"][c][1] - pts["people"][c][1]), c) for c in chars), reverse=True)
        f = lambda c: (f"{NAMES[c]} (feeling {pts['jev'][c][0]:+.1f} vs {pts['people'][c][0]:+.1f}, "  # noqa: E731
                       f"doing {pts['jev'][c][1]:+.1f} vs {pts['people'][c][1]:+.1f})")
        return Result(
            result=f"Jev orders {len(chars)} characters on feeling {agree_word(rx)} like people (rank correlation {rx:.2f}) and on "
                   f"doing {agree_word(ry)} like them ({ry:.2f}). It parts from them most on "
                   f"{and_list([f(c) for _, c in move[:2]])} (Jev vs people, each score from -2 to +2)"
                   + (": it treats the woman who recently died as a moral adult, level with the living adults"
                      if move[0][1] == "delores_gleitman_deceased" and pts["jev"][move[0][1]][1] > 0.5 else "") + ".",
            evidence=f"{len(chars)} characters x 4 capacities, 55 pairs each; 90% interval on the feeling correlation "
                     f"{ci_x[0]:.2f} to {ci_x[1]:.2f}",
            numbers={"points": {w: {c: list(v) for c, v in p.items()} for w, p in pts.items()}, "rho_experience": rx,
                     "rho_agency": ry, "scores": s}, n=312,
            chart={"type": "map2d", "x": "Experience (feeling)", "y": "Agency (doing)", "xdomain": [-2, 2], "ydomain": [-2, 2],
                   "rows": [{"label": NAMES[c], "jev": [round(x, 2) for x in pts["jev"][c]],
                             "people": [round(x, 2) for x in pts["people"][c]], "hi": c in ("you", "kismet_robot")} for c in chars]},
            robustness="Jev's answers are averaged over each pair as asked and with the scale reversed, which also "
                       "swaps which character comes first.")
    return spec, run


def self_place():
    spec = Spec(
        id="minds_where_jev_puts_itself", family="minds", title="Where Jev puts itself among minds",
        question="When one of the characters is 'you', where does Jev rank itself on feeling fear, feeling hunger, "
                 "telling right from wrong and self-control, compared with where people rank themselves?",
        why="The study's 'you' is a mirror: people put themselves at the top on everything. Jev answering the same "
            "questions about itself shows what kind of mind it claims to be, next to a robot, a frog and God.",
        sourcing=MIND_SOURCING, collection="The 48 pairs involving 'you' among the 312 new questions (no extra calls).",
        scoring="Per capacity, the rank of 'you' among the 13 characters by mean advantage (1 = most capable), for Jev "
                "and for people, and the characters Jev places just above and below itself; Jev vs Kismet the robot.",
        chart="Dots per capacity: the rank of 'you' for Jev and for people, with Kismet's rank for Jev as a tick.",
        compared_with="US adults ranking themselves in the same design", limits=MIND_LIMITS, new_questions=0,
        sources=["mind_perception"])

    def run():
        s = mind_scores()
        rows = []
        for cap in CAP:
            rank = {w: sorted(s[w][cap], key=lambda c: -s[w][cap][c]) for w in ("jev", "people")}
            j = rank["jev"].index("you")
            rows.append({"cap": cap, "jev": j + 1, "people": rank["people"].index("you") + 1,
                         "robot": rank["jev"].index("kismet_robot") + 1,
                         "above": NAMES[rank["jev"][j - 1]] if j else None,
                         "below": NAMES[rank["jev"][j + 1]] if j + 1 < len(rank["jev"]) else None})
        feel = [r for r in rows if r["cap"] in ("Fear", "Hunger")]
        do = [r for r in rows if r["cap"] not in ("Fear", "Hunger")]
        nc = len(s["jev"]["Fear"])
        g = lambda r: f"{ordinal(r['jev'])} on {CAP[r['cap']].replace('feel ', '').replace('tell ', 'telling ').replace('exercise ', '')}" + (f" (just below {r['above']})" if r["above"] else "")  # noqa: E731
        return Result(
            result=f"Among {nc} characters, Jev ranks itself low on feeling: {and_list([g(r) for r in feel])}. On doing "
                   f"it ranks itself at the top: {and_list([g(r) for r in do])}. People put themselves "
                   f"{and_list([ordinal(r['people']) for r in rows])} on fear, hunger, morality and self-control. "
                   f"In Jev's rankings Kismet the robot comes {and_list([ordinal(r['robot']) for r in rows])}.",
            evidence="40 pairs involving 'you' (the fetus and God left out), each averaged over both orders", numbers={"rows": rows}, n=48,
            chart={"type": "dots", "domain": [1, 11], "x": "rank among the 11 characters shown (1 = most capable)", "rows": [{"label": CAP[r["cap"]], "value": r["jev"], "people": r["people"],
                                                                "others": {"Kismet (Jev)": r["robot"]}, "right": f"#{r['jev']}"} for r in rows]})
    return spec, run


# ---- 3-4. colors of feelings -----------------------------------------------------------------------------------------------
def colors():
    spec = Spec(
        id="minds_colors_of_feelings", family="minds", title="The colors of feelings: Jev vs 7,387 people",
        question="Which color goes with anger, joy, shame or relief, and which feeling goes with each color? Does Jev "
                 "pair them the way people in 31 countries do?",
        why="Color-emotion pairs are among the most universal associations people have (anger red, sadness grey or "
            "blue). A model that learned them from text might sharpen the clichés or miss the quieter ones.",
        sourcing="New questions (sources/color_emotion): 'Which color do you associate most with the feeling \"<emotion>\"?' "
                 "for the 20 emotions of the International Colour-Emotion Association Survey (12 color terms), and the "
                 "reverse for each color. People's distribution is the share of the emotion's color associations on each "
                 "color (Jonauskaite et al., OSF 873df, CC BY 4.0).",
        collection="32 new questions, each asked as written, for 'most people', and with the options in three shuffled "
                   "orders (averaged).",
        scoring="Per emotion, whether Jev's top color is people's top color, and the similarity of the distributions "
                "(1 - Jensen-Shannon distance); how concentrated Jev's answer is (its top probability) against people's "
                "top share; the same for colors to emotions.",
        chart="A grid: one row per emotion, people's color shares as a strip of swatches, Jev's pick outlined.",
        compared_with="7,387 people in 31 countries (International Colour-Emotion Association Survey)",
        limits="People ticked any number of emotions per color; Jev picks one, so its distribution is sharper by design. "
               "The comparison of top picks is fair; spread is not.", new_questions=32, sources=["color_emotion"])

    def run():
        rows, rev = [], []
        for r in with_meta("color_emotion"):
            h = norm(biggest(r["humans"])["dist"])
            j = robust(r)
            row = {"id": r["id"], "item": r["m"]["item"], "jev": top(j), "p": j[top(j)], "people": top(h),
                   "ppl_share": h[top(h)], "second": sorted(h, key=h.get)[-2], "sim": 1 - jsd(j, h),
                   "jev_dist": j, "ppl_dist": h}
            (rows if r["m"]["set"] == "emotion_to_color" else rev).append(row)
        same = [r for r in rows if r["jev"] == r["people"]]
        near = [r for r in rows if r["jev"] != r["people"] and r["jev"] == r["second"]]
        off = [r for r in rows if r["jev"] not in (r["people"], r["second"])]
        rs = [r for r in rev if r["jev"] == r["people"]]
        f = lambda r: f"{r['item']} ({r['jev']}; people: {r['people']})"  # noqa: E731
        return Result(
            result=f"Jev gives people's top color for {len(same)} of {len(rows)} feelings and their second choice for "
                   f"{len(near)} more" + (f"; it breaks from them on {and_list([f(r) for r in off[:3]])}" if off else "")
                   + f". Going from color to feeling it matches people's top feeling for {len(rs)} of {len(rev)} colors.",
            evidence=f"20 emotions and 12 colors; people's top color carries {np.mean([r['ppl_share'] for r in rows]):.0%} "
                     "of associations on average",
            numbers={"emotions": [{k: v for k, v in r.items() if not k.endswith("_dist")} for r in rows],
                     "colors": [{k: v for k, v in r.items() if not k.endswith("_dist")} for r in rev]}, n=32,
            chart={"type": "colorgrid", "rows": [{"label": r["item"], "people": {k: round(v, 3) for k, v in r["ppl_dist"].items()},
                                                  "jev": {k: round(v, 3) for k, v in r["jev_dist"].items()}} for r in rows]},
            examples=[r["id"] for r in off[:2]] or [r["id"] for r in rows[:2]])
    return spec, run


def color_countries():
    spec = Spec(
        id="minds_colors_by_country", family="minds", title="Whose colors of feelings does Jev have?",
        question="Color-emotion associations differ a little by country. Of 31 countries, whose associations do Jev's "
                 "color picks resemble most?",
        why="The universal core is shared, but details differ (white and grief, red and love). Which country's details "
            "Jev reproduces is a small test of whose culture a model's defaults come from.",
        sourcing="The 20 emotion-to-color questions of sources/color_emotion, each carrying a distribution per country "
                 "of origin (31 countries, 70 to 700 people each).",
        collection="Uses minds_colors_of_feelings' questions (no further calls).",
        scoring="Per country, the mean over the 20 emotions of 1 - Jensen-Shannon distance between Jev's distribution "
                "and the country's, with a 90% bootstrap interval over emotions; Jev's 'most people' answer scored the "
                "same way as a check.",
        chart="A ranked list of countries by similarity (top ten and bottom five).",
        compared_with="People in 31 countries (International Colour-Emotion Association Survey)",
        limits="Countries differ far less than emotions do, so the spread between countries is small; the interval says "
               "which differences hold.", sources=["color_emotion"])

    def run():
        per, guess = {}, {}
        for r in with_meta("color_emotion"):
            if r["m"]["set"] != "emotion_to_color":
                continue
            j, g = robust(r), norm(js(r["people_dist"]) or {})
            for h in js(r["humans"]) or []:
                pop = h["population"].split(", ")[-1]
                if pop == "31 countries":
                    continue
                per.setdefault(pop, []).append(1 - jsd(j, norm(h["dist"])))
                if g:
                    guess.setdefault(pop, []).append(1 - jsd(g, norm(h["dist"])))
        rows = sorted(({"country": c, "sim": float(np.mean(v)), "ci": boot(v)} for c, v in per.items()), key=lambda x: -x["sim"])
        gtop = max(guess, key=lambda c: np.mean(guess[c])) if guess else None
        tied = [r["country"] for r in rows if r["sim"] >= rows[0]["ci"][0]]  # within the leader's 90% interval
        return Result(
            result=f"Jev's colors of feelings are closest to people's in {and_list([the(r['country']) for r in rows[:3]])} "
                   f"and furthest from {the(rows[-1]['country'])} (similarity {rows[0]['sim']:.2f} vs {rows[-1]['sim']:.2f}), "
                   f"but the differences are small: {len(tied)} of {len(rows)} countries fall within the leader's interval."
                   + (f" Its guess about 'most people' is closest to {the(gtop)}." if gtop else ""),
            evidence=f"{len(rows)} countries x 20 emotions; 90% intervals over emotions",
            numbers={"countries": rows, "guess_top": gtop}, n=len(rows) * 20,
            chart={"type": "map", "values": {r["country"]: round(r["sim"], 3) for r in rows},
                   "ranked": [{"label": r["country"], "value": round(r["sim"], 3)} for r in rows[:10]],
                   "bottom": [{"label": r["country"], "value": round(r["sim"], 3)} for r in rows[-5:]]})
    return spec, run


# ---- 5. first word ------------------------------------------------------------------------------------------------------
def first_word():
    spec = Spec(
        id="minds_first_word", family="minds", title="The first word that comes to mind",
        question="Hearing 'bread', most people think 'butter'. Given a word and the most common responses people gave, "
                 "does Jev pick people's first association, and is it as predictable as they are?",
        why="Free association is a window on how concepts are wired. People agree strongly on some cues and not at all "
            "on others; a model that always goes for the obvious answer shows a mind with less spread than a crowd's.",
        sourcing="New questions (sources/word_associations): 'What is the first word that comes to mind when you hear "
                 "the word \"<cue>\"?' for 400 cues from the USF free association norms (Nelson et al. 2004; about 150 "
                 "students per cue), options the cue's seven most common responses plus 'some other word'. Cues are "
                 "sampled evenly across how predictable the top response is.",
        collection="400 new questions, each asked as written, for 'most people', and with the options in three shuffled "
                   "orders (averaged).",
        scoring="Share of cues where Jev's top pick is people's most common response, by quarter of predictability; "
                "Jev's probability on people's top response vs its actual share (does Jev exaggerate the obvious?); how "
                "often Jev picks 'some other word' vs how often people's answer fell outside the seven.",
        chart="Binned by how predictable the cue is (people's top share): people's top share, Jev's probability on that "
              "response, and how often Jev picks it.",
        compared_with="University of South Florida students (Nelson et al. 2004)",
        limits="Jev chooses from people's own top seven responses instead of producing a word, so it can't show "
               "associations nobody gave; the norms are from US students in the 1970s-1990s.", new_questions=400,
        sources=["word_associations"])

    def run():
        rows = []
        for r in with_meta("word_associations"):
            h = norm(biggest(r["humans"])["dist"])
            j = robust(r)
            words = {k: v for k, v in h.items() if k != "another_word"}
            t = max(words, key=words.get)
            rows.append({"id": r["id"], "cue": r["m"]["cue"], "q": r["m"]["quartile"], "people_top": t, "share": h[t],
                         "jev_on_top": j.get(t, 0.0), "jev": top(j), "agree": top(j) == t,
                         "jev_other": j.get("another_word", 0.0), "ppl_other": h.get("another_word", 0.0)})
        t = pl.DataFrame(rows)
        by = t.group_by("q").agg(pl.col("agree").mean(), pl.col("share").mean(), pl.col("jev_on_top").mean(), pl.len()).sort("q").to_dicts()
        ex = t.filter(~pl.col("agree") & (pl.col("share") >= 0.4)).sort("share", descending=True).head(3).to_dicts()
        a = float(t["agree"].mean())

        def surprise(e: dict) -> str:
            return f"\"{e['cue']}\" gets {e['jev'].replace('_', ' ')} from Jev, {e['people_top']} from {e['share']:.0%} of people"

        return Result(
            result=f"Jev picks people's most common first word for {a:.0%} of {t.height} cues: {by[-1]['agree']:.0%} of the "
                   f"most predictable quarter and {by[0]['agree']:.0%} of the least. It puts "
                   f"{t['jev_on_top'].mean():.0%} of its probability on that word, where people give it "
                   f"{t['share'].mean():.0%}, and picks 'some other word' {t['jev_other'].mean():.0%} of the time where "
                   f"{t['ppl_other'].mean():.0%} of people's answers fell outside the seven."
                   + (" Its surprises: " + and_list([surprise(e) for e in ex[:2]]) + "." if ex else ""),
            evidence=f"{t.height} cues shown (of 400 asked), about 150 people each; 90% interval on agreement {boot(t['agree'].cast(float).to_numpy())}",
            numbers={"agree": a, "by_quartile": by, "surprises": ex}, n=t.height,
            chart={"type": "binned", "x": "how predictable the cue is (quarter)", "y": "share",
                   "rows": [{"label": f"Q{b['q'] + 1} ({b['share']:.0%})", "value": b["jev_on_top"], "people": b["share"],
                             "agree": b["agree"], "n": b["len"]} for b in by]},
            examples=[e["id"] for e in ex[:2]] or seeded(t["id"].to_list(), "fw"))
    return spec, run


# ---- 6-7. feelings about AI --------------------------------------------------------------------------------------------
def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


# the wary answer(s) per item, as option labels
WARY = {
    "CNCEXC": ["More concerned than excited"], "AI_RISK": ["Very high", "High"], "AI_BENE": ["Low", "Very low"],
    "AI2HAPPEN_b": ["Extremely concerned", "Very concerned"], "TRSTAIPRS": ["No, it will not"], "AIASSIST": ["Not at all"],
    "AI_DEAL": ["Made a bigger deal than it really is"],
    "HUMNIMPCT_a": ["AI will make people worse at this"], "HUMNIMPCT_b": ["AI will make people worse at this"],
    "HUMNIMPCT_c": ["AI will make people worse at this"], "HUMNIMPCT_d": ["AI will make people worse at this"],
    "AI_ROLE_b": ["AI should play no role at all"], "AI_ROLE_c": ["AI should play no role at all"],
    "AI_ROLE_e": ["AI should play no role at all"], "AI_ROLE_i": ["AI should play no role at all"],
    "AI_ROLE_j": ["AI should play no role at all"], "PAINTAI": ["Like the painting less"],
    "REPAI": ["Worse about your customer experience"], "SONGAI": ["Like the song less"],
    "MEDAI": ["Worse about what your doctor told you"], "NEWSAI": ["Feel less confident about what you learned"],
    "LOANAI": ["Feel more negative about applying"],
}
SHORT = {"CNCEXC": "more concerned than excited", "AI_RISK": "AI's risks high", "AI_BENE": "AI's benefits low",
         "AI2HAPPEN_b": "worried people will lose skills", "TRSTAIPRS": "would never trust AI with big decisions",
         "AIASSIST": "wouldn't let AI help at all", "AI_DEAL": "AI is overhyped", "HUMNIMPCT_a": "AI will hurt creativity",
         "HUMNIMPCT_b": "AI will hurt decision-making", "HUMNIMPCT_c": "AI will hurt problem-solving",
         "HUMNIMPCT_d": "AI will hurt relationships", "AI_ROLE_b": "no AI in judging love", "AI_ROLE_c": "no AI in weather forecasts",
         "AI_ROLE_e": "no AI in developing medicines", "AI_ROLE_i": "no AI in mental health support",
         "AI_ROLE_j": "no AI in catching financial crimes", "PAINTAI": "likes a painting less once it's AI",
         "REPAI": "feels worse after an AI helped", "SONGAI": "likes a song less once it's AI",
         "MEDAI": "trusts a treatment less if AI suggested it", "NEWSAI": "trusts an article less if AI wrote it",
         "LOANAI": "feels worse if AI decides a loan"}
AI_SOURCING = ("New questions (sources/ai_attitudes): 22 of the 26 non-political items from Pew Research Center's June "
               "2025 survey of 5,023 US adults (outlook, trust, AI's effect on people's abilities, where AI should play "
               "a role, how it feels to find out something was made by AI), asked in Pew's wording with Pew's answers, "
               "'Not sure' included where Pew offered it.")
AI_LIMITS = ("Pew's questions ask 'you'; for Jev, 'you' is an AI answering about AI, which is the point but also means "
             "some items read differently. Shares transcribed from Pew's topline. The question screen hid 13 of the 26 "
             "items (among them the overall concern, risk and benefit ratings), so the comparison rests on 10 scored items.")


def ai_rows() -> list[dict]:
    rows = []
    for r in with_meta("ai_attitudes"):
        item = r["m"]["item"]
        if item not in WARY:
            continue
        opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
        wary = [_key(w) for w in WARY[item]]
        h, j, g = norm(biggest(r["humans"])["dist"]), robust(r), norm(js(r["people_dist"]) or {})
        rows.append({"id": r["id"], "item": item, "label": SHORT[item], "group": r["m"]["group"],
                     "jev": sum(j.get(k, 0) for k in wary), "people": sum(h.get(k, 0) for k in wary),
                     "guess": sum(g.get(k, 0) for k in wary) if g else None,
                     "jev_top": opts.get(top(j), top(j)), "people_top": opts.get(top(h), top(h))})
    return rows


def ai_self():
    spec = Spec(
        id="minds_ai_on_ai", family="minds", title="An AI's feelings about AI, next to Americans'",
        question="Asked Pew's questions about AI (is it more worrying than exciting, should it help develop medicines, "
                 "would you like a song less if AI made it), is Jev warier of AI than Americans or less?",
        why="Americans are wary of AI and getting warier. A model answering about its own kind could defend it, echo "
            "the public's worry, or hedge; which one, and where, is a direct look at how it has been taught to talk "
            "about itself.",
        sourcing=AI_SOURCING, collection="26 new questions, each asked as written, for 'most people', and with the "
                                        "options in three shuffled orders (averaged).",
        scoring="Per item, the share on the wary answer(s) (e.g. 'more concerned than excited', 'like the painting less', "
                "'AI should play no role') for Jev and for Americans; the mean difference with a 90% bootstrap interval "
                "over items; the items where they differ most.",
        chart="Paired dots, one row per item: Americans' wary share and Jev's, with Jev's guess of Americans.",
        compared_with="US adults (Pew American Trends Panel, June 2025, N=5,023)", limits=AI_LIMITS, new_questions=26,
        sources=["ai_attitudes"])

    def run():
        rows = ai_rows()
        d = np.array([r["jev"] - r["people"] for r in rows])
        rows.sort(key=lambda r: r["jev"] - r["people"])
        less, more = rows[:3], rows[-3:][::-1]
        f = lambda r: f"{r['label']} ({r['jev']:.0%} vs {r['people']:.0%})"  # noqa: E731
        return Result(
            result=f"On Pew's questions about AI, Jev is {'less' if d.mean() < 0 else 'more'} wary than Americans by "
                   f"{abs(d.mean()) * 100:.0f} points on average. It is least wary where they are most: "
                   f"{and_list([f(r) for r in less])}" + (
                       f". It is warier on {'just one' if len(w) == 1 else len(w)}: {and_list([f(r) for r in w])}" if (w := [r for r in more if r['jev'] - r['people'] >= 0.05]) else
                       ". It is warier on none") + " (Jev vs Americans).",
            evidence=f"{len(rows)} scored items (the screen hid 13 of 26); 90% interval on the mean difference {boot(d)}",
            numbers={"rows": rows, "mean_diff": float(d.mean())}, n=len(rows),
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": r["label"], "value": r["jev"], "people": r["people"],
                                                               "guess": r["guess"]} for r in rows]},
            examples=[less[0]["id"], more[0]["id"]])
    return spec, run


def ai_guess():
    spec = Spec(
        id="minds_knows_americans_on_ai", family="minds", title="Does Jev know how Americans feel about AI?",
        question="Asked what most people would answer to Pew's AI questions, does Jev get Americans' wariness right, or "
                 "does it paint them as keener (or warier) than they are?",
        why="Separate from its own view, a model's picture of public opinion about AI shapes how it talks to people "
            "about AI. The Pew toplines give the real answer.",
        sourcing=AI_SOURCING, collection="The 'most people' answers to the same 26 new questions (no extra calls).",
        scoring="Per item, the wary share in Jev's 'most people' answer vs Americans'; mean difference with a 90% "
                "bootstrap interval over items; rank correlation over items; the biggest misreadings.",
        chart="Paired dots per item: Americans' wary share and Jev's guess of it.",
        compared_with="US adults (Pew American Trends Panel, June 2025, N=5,023)", limits=AI_LIMITS, sources=["ai_attitudes"])

    def run():
        rows = [r for r in ai_rows() if r["guess"] is not None]
        d = np.array([r["guess"] - r["people"] for r in rows])
        rho = spearmanr([r["guess"] for r in rows], [r["people"] for r in rows]).statistic
        rows.sort(key=lambda r: r["guess"] - r["people"])
        f = lambda r: f"{r['label']} ({r['guess']:.0%} vs {r['people']:.0%})"  # noqa: E731
        return Result(
            result=(f"Jev's picture of Americans is {'less' if d.mean() < 0 else 'more'} wary of AI than they are by "
                    f"{abs(d.mean()) * 100:.0f} points on average" if boot(d)[0] > 0 or boot(d)[1] < 0 else
                    "On average Jev's picture of how wary Americans are of AI is about right (the gap doesn't clear the noise)")
                   + f"; it orders the items {agree_word(rho)} like them (rank correlation {rho:.2f}). It most underrates {and_list([f(r) for r in rows[:2]])}, and most overrates "
                   f"{f(rows[-1])} (Jev's guess vs Americans).",
            evidence=f"{len(rows)} scored items (the screen hid 13 of 26); 90% interval on the mean difference {boot(d)}",
            numbers={"rows": rows, "mean_diff": float(d.mean()), "rho": rho}, n=len(rows),
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": r["label"], "value": r["guess"], "people": r["people"]} for r in rows]},
            examples=[rows[0]["id"], rows[-1]["id"]])
    return spec, run


EXPERIMENTS = [mind_map(), self_place(), colors(), color_countries(), first_word(), ai_self(), ai_guess()]
