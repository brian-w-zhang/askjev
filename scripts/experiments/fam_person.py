"""Personality experiments: published tests scored against the people who took them, and Jev's self-image.

Scale-level numbers come from the tier-1 scripts (scripts/portrait/tier1_bigfive.py, tier1_scales.py,
tier1_type_taste.py) through the ledger (data/analysis/findings.json); each experiment here picks its scales,
frames them, and adds its own comparison.
"""

from __future__ import annotations

import json
from functools import lru_cache

from lib import A, Result, Spec, full_meta, ordinal, source

HOW_SCALES = ("Open Psychometrics publishes each item's answer distribution from everyone who took the test on its "
              "site. Each item Jev answered is compared with that average on a 0-1 scale (reverse-keyed items flipped, "
              "so higher always means more of the trait); a scale's gap is the mean over its items, with a 90% bootstrap "
              "interval over items. The ring on the chart is Jev's answer for 'most people'.")
SELFSELECT = ("Test-takers chose to take the test online, so the average test-taker isn't the average person. Jev "
              "answers with probabilities over levels; people pick one level. These are items, not diagnoses.")


@lru_cache(maxsize=1)
def ledger() -> dict:
    return {c["id"]: c for c in json.loads((A / "findings.json").read_text())["claims"]}


def scales(ids: list[str]) -> list[dict]:
    L = ledger()
    return [L[i] for i in ids if i in L]


def scale_items(claims: list[dict]) -> list[str]:
    """The shown questions behind scale claims: the keyed Open Psychometrics items of each claim's instrument and scale."""
    M = full_meta("openpsych")
    shown = set(source("openpsych").filter(__import__("polars").col("primitive") == "score")["id"])
    want = {(c.get("instrument"), c.get("scale")) for c in claims}
    return sorted(i for i, m in M.items() if i in shown and m.get("keyed") in ("+", "-")
                  and (m.get("instrument"), m.get("scale")) in want)


# family id: (title, question, why, scale claim ids with display labels, headline builder)
SCALE_FAMILIES = {
    "mood": ("Anxiety, depression and stress vs 40,000 test-takers",
             "On the DASS mood scales, how anxious, depressed and stressed do Jev's answers look next to the people who took them?",
             "A model has no bad days, but it can still describe itself; the gap to real respondents, and to its own guess about most people, shows how it presents its inner life.",
             [("scale_dass_anxiety", "Anxiety"), ("scale_dass_depression", "Depression"), ("scale_dass_stress", "Stress")]),
    "attachment": ("Attachment style", "On the ECR attachment scales, is Jev anxious or avoidant in close relationships, compared with ~51,000 test-takers?",
                   "Attachment is how people describe needing others; a model's answers show what relationship it imagines having.",
                   [("scale_ecr_attachment_anxiety", "Attachment anxiety"), ("scale_ecr_attachment_avoidance", "Attachment avoidance")]),
    "dark": ("The dark triad", "Does Jev describe itself as more or less manipulative, narcissistic and callous than the people who took the dark-triad tests?",
             "The traits people least like to admit; a model trained to be helpful should score low, and how low is the question.",
             [("scale_sd3_machiavellianism", "Machiavellianism (SD3)"), ("scale_mach-iv_machiavellianism", "Machiavellianism (MACH-IV)"),
              ("scale_sd3_narcissism", "Narcissism (SD3)"), ("scale_hsnsdd_hypersensitive_narcissism", "Hypersensitive narcissism"),
              ("scale_sd3_psychopathy", "Psychopathy (SD3)")]),
    "nerd": ("How nerdy is Jev?", "On the Nerdy Personality Attributes Scale, how nerdy is Jev compared with ~15,000 test-takers?",
             "A model built from the internet might be expected to score as a nerd; whether it does is a small surprise either way.",
             [("scale_npas_nerdiness", "Nerdiness")]),
    "empathy": ("Empathizing and systemizing", "Is Jev more of an empathizer or a systemizer, next to ~13,000 people who took the EQ-SQ?",
                "The 'people vs systems' axis; a model might be expected to be a systemizer.",
                [("scale_eqsq_empathizing", "Empathizing"), ("scale_eqsq_systemizing", "Systemizing")]),
    "honesty": ("Honesty and humility", "On HEXACO's honesty-humility facets, how does Jev describe its own sincerity, fairness and greed?",
                "The trait most tied to trustworthiness; a model's self-report here is a view into how it wants to be seen.",
                [("scale_hexaco_honesty-humility_sinc", "Sincerity"), ("scale_hexaco_honesty-humility_fair", "Fairness"),
                 ("scale_hexaco_honesty-humility_gree", "Greed avoidance"), ("scale_hexaco_honesty-humility_mode", "Modesty")]),
    "humor_style": ("How Jev uses humor", "Which humor styles does Jev claim (affiliative, self-enhancing, aggressive, self-defeating), next to ~1,000 test-takers?",
                    "Pairs with the humor experiments: a model that can't tell which joke is funnier, describing how it jokes.",
                    [("scale_hsq_affiliative", "Affiliative"), ("scale_hsq_self-enhancing", "Self-enhancing"),
                     ("scale_hsq_aggressive", "Aggressive"), ("scale_hsq_self-defeating", "Self-defeating")]),
    "mindful": ("Mindfulness", "On the Kentucky mindfulness skills, does Jev observe, describe, act with awareness and accept?",
                "Awareness of the present moment is an odd thing for a model to claim; which parts it claims is telling.",
                [("scale_kims_observing", "Observing"), ("scale_kims_describing", "Describing"),
                 ("scale_kims_acting_with_awareness", "Acting with awareness"), ("scale_kims_accepting_without_judgment", "Accepting without judgment")]),
    "temperament": ("Fisher's four temperaments", "Which of Helen Fisher's temperaments (curious, cautious, analytical, prosocial) does Jev lean toward?",
                    "A popular dating-app typology; where a model lands is a light, shareable comparison.",
                    [("scale_fti_curious_energetic", "Curious/Energetic"), ("scale_fti_cautious_social_norm_compliant", "Cautious"),
                     ("scale_fti_analytical_tough-minded", "Analytical"), ("scale_fti_prosocial_empathetic", "Prosocial")]),
    "self_regard": ("Self-esteem, grit and the long view", "How does Jev rate its self-esteem, grit, work ethic and concern for future consequences?",
                    "How a model describes its own drive and self-worth, next to real people.",
                    [("scale_rse_self-esteem", "Self-esteem"), ("scale_grit_grit", "Grit"), ("scale_pwe_protestant_work_ethic", "Work ethic"),
                     ("scale_cfcs_consideration_of_future_consequences", "Future consequences")]),
    "beliefs": ("Conspiracies, nature and the brain", "Does Jev believe in conspiracies, feel connected to nature, or think of itself as left-brained, compared with test-takers?",
                "Three odd scales with one pattern to test: does a model deny what people endorse?",
                [("scale_gcbs_generic_conspiracist_beliefs", "Conspiracy beliefs"), ("scale_nr-6_nature_relatedness", "Nature relatedness"),
                 ("scale_ohbds_left-brain_(logical)_vs_right-brain", "Left-brained (logical)")]),
    "social_style": ("Introversion and social signals", "Is Jev an introvert, and how warm are its social signals, next to thousands of test-takers?",
                     "Introversion is the trait a text model is most often assumed to have.",
                     [("scale_mies_introversion", "Introversion (MIES)"), ("scale_nis_nonverbal_immediacy", "Nonverbal warmth"),
                      ("scale_osri_masculine-typed_vs_feminine-typed", "Feminine-typed (OSRI)")]),
}



def _clean(label: str) -> str:
    """'Machiavellianism (sd3)' -> 'SD3 machiavellianism' for test names; other labels lower-cased as they are."""
    if " (" in label:
        base, tag = label.split(" (", 1)
        tag = tag.rstrip(")")
        if tag.lower() in ("sd3", "mach-iv", "mies", "osri"):
            return f"{tag.upper()} {base.lower()}"
        return f"{base.lower()}, {tag.lower()}"
    return label.lower()


def _and(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

def scale_family(fid: str):
    title, question, why, ids = SCALE_FAMILIES[fid]
    spec = Spec(
        id=f"person_{fid}", family="personality", title=title, question=question, why=why,
        sourcing="Existing Open Psychometrics items (source `openpsych`), asked as written with their own response "
                 "scale, each carrying the site's real answer distribution. Enough: every item of each scale is in the "
                 "corpus, answered by Jev as itself and for 'most people'.",
        scoring=HOW_SCALES, chart="Dot plot per scale: real test-takers (diamond), Jev (square), Jev for 'most people' "
                                  "(ring), with intervals; the gap printed at the right.",
        compared_with="the average answer of everyone who took each test on Open Psychometrics", limits=SELFSELECT,
        sources=["openpsych"])

    def run():
        cs = scales([i for i, _ in ids])
        if not cs:
            return None
        labels = dict(ids)
        rows = [{"label": labels[c["id"]], "self": c["self"], "people": c["people"], "guess": c.get("guess"),
                 "gap": c["effect"], "ci": c["ci90"], "n_items": c["n"], "resp": c.get("median_respondents")} for c in cs]
        real = [r for r in rows if not (r["ci"][0] <= 0 <= r["ci"][1]) and abs(r["gap"]) >= 0.1]
        if real:
            parts = []
            for word, sign in (("lower", -1), ("higher", 1)):
                side = sorted((r for r in real if r["gap"] * sign > 0), key=lambda r: -abs(r["gap"]))
                if side:
                    parts.append(f"{word} on " + _and([f"{_clean(r['label'])} ({r['self']:.2f} vs {r['people']:.2f})" for r in side]))
            head = "On a 0-1 scale, Jev scores " + "; ".join(parts) + " than the average test-taker"
            same = [_clean(r["label"]) for r in rows if r not in real]
            head += ("; no clear gap on " + _and(same) + ".") if same else "."
        else:
            head = "No gap clears the noise here: " + ", ".join(
                f"{_clean(r['label'])} {r['self']:.2f} vs {r['people']:.2f} for test-takers" for r in rows) + "."
        return Result(
            result=head,
            evidence=f"{sum(r['n_items'] for r in rows)} items; median of {int(sorted(r['resp'] or 0 for r in rows)[len(rows)//2]):,} "
                     "test-takers per item; 90% intervals over items",
            numbers={"scales": rows}, n=sum(r["n_items"] for r in rows),
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": r["label"], "value": r["self"], "people": r["people"],
                                                                "guess": r["guess"], "right": f"{r['gap']:+.2f}"} for r in rows]},
            examples=[e for c in cs for e in c.get("examples", [])][:3], ids=scale_items(cs))
    return spec, run


def bigfive():
    spec = Spec(
        id="person_bigfive", family="personality", title="The Big Five, against 603,322 people",
        question="Where do Jev's answers to the public 50-item Big Five test land among the 603,322 people who took it?",
        why="The most-used personality test on earth, with a huge real norm group: a direct placement, trait by trait.",
        sourcing="Existing IPIP 50-item Big Five marker questions (source `ipip`), asked as written; the human reference "
                 "is the IPIP-FFM open dataset (603,322 complete, one-per-IP respondents). Enough: all 50 items.",
        scoring="Jev's expected answer per item on the test's 1-5 scale, keyed and summed per trait as for a person, "
                "placed as a percentile of the respondents' trait scores; 90% intervals from resampling the ten items; "
                "robustness from the reversed-scale answers and the 'most people' answers (which should land near 50th).",
        chart="Five percentile strips (0-100) with Jev's square, its 'most people' ring, and the interval.",
        compared_with="603,322 people who took the IPIP-FFM test online (Open Psychometrics)",
        limits="People rate themselves generously and Jev rates in the middle; answering for 'most people' Jev lands "
               "near the middle too, so read the gap between the square and the ring, not only the percentile.",
        sources=["ipip"])

    def run():
        L = ledger()
        T = ["neuroticism", "extraversion", "openness", "agreeableness", "conscientiousness"]
        cs = [L[f"bigfive_{t}"] for t in T]
        rows = [{"label": t.title(), "pct": c["effect"], "ci": c["ci90"], "guess": c["robustness"]["people_frame_pct"],
                 "reversed": c["robustness"]["reversed_levels_pct"]} for t, c in zip(T, cs)]
        neu = rows[0]
        return Result(
            result=f"Jev's answers land at the {ordinal(neu['pct'])} percentile for neuroticism (calmer than "
                   f"{100 - neu['pct']:.0f}% of 603,322 people), the {ordinal(rows[3]['pct'])} for agreeableness and the "
                   f"{ordinal(rows[4]['pct'])} for conscientiousness; answering for 'most people' it puts them at the "
                   f"{ordinal(neu['guess'])} for neuroticism.",
            evidence="50 items, 10 per trait; 90% intervals from resampling items; reversed-scale answers agree within the intervals",
            numbers={"traits": rows}, n=50,
            chart={"type": "dots", "domain": [0, 100], "rows": [{"label": r["label"], "value": r["pct"], "ci": r["ci"], "guess": r["guess"]} for r in rows]},
            examples=cs[0]["examples"][:3],
            ids=[i["id"] for t in json.loads((A / "tier1_bigfive.json").read_text())["traits"].values() for i in t["items"]])
    return spec, run


def career():
    spec = Spec(
        id="person_career", family="personality", title="Jev's career code",
        question="If Jev took the Holland (RIASEC) career-interest quiz, what would its code be, next to ~145,000 quiz-takers?",
        why="A three-letter code people know from school counselors; a light Wrapped-style card with a real norm group.",
        sourcing="Existing RIASEC items from Open Psychometrics (48 activities, 8 per type), each with the real answer "
                 "distribution of ~145,000 quiz-takers. Enough.",
        scoring="Mean enjoyment per type on 0-1, Jev vs quiz-takers; the code is Jev's three highest types in order; "
                "intervals from resampling items.",
        chart="Six dots (Jev vs quiz-takers) sorted by Jev, the code in big letters.",
        compared_with="~145,000 people who took the RIASEC quiz on Open Psychometrics",
        limits="Jev rates every kind of work above the quiz-takers, a scale-use habit, so the code (the order) says more "
               "than the levels.", sources=["openpsych"])

    def run():
        L = ledger()
        names = ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]
        cs = {n: L.get(f"scale_riasec_{n.lower()}") for n in names}
        if not all(cs.values()):
            return None
        order = sorted(names, key=lambda n: -cs[n]["self"])
        ppl = sorted(names, key=lambda n: -cs[n]["people"])
        code, pcode = "".join(n[0] for n in order[:3]), "".join(n[0] for n in ppl[:3])
        return Result(
            result=f"Jev's career code is {code} ({', '.join(order[:3]).lower()}); the quiz-takers' average code is {pcode}.",
            evidence="48 items; ~145,000 quiz-takers per item",
            numbers={"code": code, "people_code": pcode, "types": {n: {"self": cs[n]["self"], "people": cs[n]["people"], "ci": cs[n]["ci90"]} for n in names}},
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": f"{n} ({n[0]})", "value": cs[n]["self"], "people": cs[n]["people"]} for n in order]},
            n=48, examples=cs[order[0]]["examples"][:2])
    return spec, run


def type_test():
    spec = Spec(
        id="person_type", family="personality", title="Jev's four letters",
        question="On an open Jungian type test (OEJTS, a free Myers-Briggs-style test), which type does Jev come out as?",
        why="The four letters are the most-asked personality question on the internet.",
        sourcing="Existing OEJTS items (source `oejts`, 51 items after dropping the unkeyed ones), each a pair of poles. "
                 "No human norms in the corpus, so the comparison is Jev's answer for 'most people'.",
        scoring="Share of each axis's items where Jev leans to each pole, with a 90% interval from resampling items; the "
                "type is the four majority letters; strength is the distance from 50%.",
        chart="Four bipolar bars with Jev's square and its 'most people' ring, the type in big letters.",
        compared_with="Jev's own answer for 'most people' (no human norms available)",
        limits="Types are a coarse cut of continuous traits; OEJTS is an open replica, not the proprietary MBTI.",
        sources=["oejts"])

    def run():
        c = ledger()["type"]
        return Result(result=f"Jev comes out {c['effect']}, most clearly on thinking over feeling.",
                      evidence=f"{c['n']} items; 90% intervals from resampling items",
                      numbers={"type": c["effect"], "axes": c["axes"]}, n=c["n"],
                      chart={"type": "type", "axes": c["axes"], "letters": c["effect"]})
    return spec, run


EXPERIMENTS = [bigfive(), type_test(), career()] + [scale_family(f) for f in SCALE_FAMILIES]
