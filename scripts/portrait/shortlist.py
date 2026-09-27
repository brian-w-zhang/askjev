"""Portrait step 6 (docs/11-portrait.md): the ~40-candidate shortlist for Brian's review, built from the claims
ledger. Each candidate: a draft headline, section, chart sketch, n / CI, tier, the ledger ids it rests on, and two
real examples (question, Jev's answer, the human answer where one exists). Private: written to
data/analysis/shortlist.md (data/ is gitignored).

  uv run python scripts/portrait/shortlist.py
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

A = Path("data/analysis")

# (candidate id, section, headline, chart sketch, ledger ids)
PICKS = [
    ("C1", "cold open", "One of 1,091,643: a single question Jev answered, shown in full, before any aggregate.",
     "one question card: Jev's distribution vs the human split", ["mm_more_lives"]),
    ("D1", "how Jev answers", "Rating one thing at a time, Jev's likeliest answer is the middle level 80% of the time.",
     "stacked bar of top-level position, ratings vs head-to-heads", ["middle_lean"]),
    ("D2", "how Jev answers", "Reorder the options and Jev keeps its answer 98% of the time on choices but 88% on rating scales.",
     "two dots with intervals, choice vs score", ["stability_choice", "stability_score"]),
    ("P1", "personality", "Against 603,322 people who took the same 50-item Big Five test, Jev is calmer than 89% of them.",
     "five percentile dots on human density strips, with the 'most people' dot", ["bigfive_neuroticism", "bigfive_extraversion",
                                                                                 "bigfive_agreeableness", "bigfive_conscientiousness", "bigfive_openness"]),
    ("P2", "personality", "Jev sees itself as a quieter version of everyone: lower than 'most people' on 17 of 21 trait facets.",
     "diverging dot plot: self minus 'most people' per facet", ["muted_self"]),
    ("P3", "personality", "On the open Jungian type test, Jev leans ISTJ, clearest on thinking over feeling and judging over perceiving.",
     "four bipolar bars with intervals", ["type"]),
    ("P4", "personality", "Where the two personality lenses disagree: conscientiousness is above average on the IPIP items, below it on everyday situations.",
     "two-row comparison, tier 1 vs tier 2", ["bigfive_conscientiousness", "muted_self"]),
    ("V1", "values", "In 26,020 Moral Machine dilemmas Jev counts lives harder than 40 million people did.",
     "Awad-style effect dot plot, Jev as one more row next to the world and 10 countries", ["mm_more_lives"]),
    ("V2", "values", "But it barely cares who they are: no pull toward sparing the young, the fit or the high-status.",
     "same dot plot, highlighting age/fitness/status rows", ["mm_young_over_old", "mm_fit_over_large", "mm_high_status"]),
    ("V3", "values", "Unlike people, Jev does not reward pedestrians for crossing on green.",
     "one highlighted row", ["mm_lawful_over_jaywalking"]),
    ("V4", "values", "In moral dilemmas Jev is almost never sure: decisive on under 3% of them.",
     "decisiveness strip: dilemmas vs the corpus", ["node_self.values.sacrificial_dilemmas.self_driving_dilemmas.sparing_women_or_men"]),
    ("V5", "values", "On the Moral Foundations Questionnaire every foundation matters less to Jev than to 'most people'; purity and equality least.",
     "paired dots per foundation", ["mfq"]),
    ("V6", "values", "Offered 2,869 real gambles, Jev chooses like most people 64% of the time.",
     "scatter of Jev vs human choice share per gamble", ["risk_gambles"]),
    ("T1", "taste: favorites", "Jev's favorites, from ~40,000 head-to-heads: Shawshank, The Hobbit, Ticket to Ride, Cowboy Bebop, Bowie, Two Hearted Ale, Python.",
     "Feltron-style ranked lists per domain, tabs", ["favorites_movielens_pairs", "favorites_goodreads_pairs", "favorites_boardgame_pairs",
                                                      "favorites_anime_pairs", "favorites_music_pairs", "favorites_beer_pairs", "favorites_so_survey_pairs"]),
    ("T2", "taste: favorites", "Its taste tracks the crowd closely for beer, books and dev tools, and hardly at all for music.",
     "rank-correlation dots per domain", ["favorites_beer_pairs", "favorites_goodreads_pairs", "favorites_so_survey_pairs", "favorites_music_pairs"]),
    ("B1", "taste beyond reputation", "What Jev likes more than it thinks you do: Come and See, Night and Fog, L'Avventura. Less: The Notebook, Frozen.",
     "slope chart: Jev's rating vs its 'most people' rating, labelled extremes", ["beyond_film_ratings"]),
    ("B2", "taste beyond reputation", "The same pattern across books, food, music and art: difficult and austere over comfortable and popular.",
     "small multiples of the slope chart", ["beyond_book_ratings", "beyond_food_ratings", "beyond_music_ratings", "beyond_art_ratings"]),
    ("K1", "knowledge map", "Where Jev knows things: most right in history and science, least in the Machine search and document tasks.",
     "sorted accuracy dots per domain with intervals, each with one real miss", ["knowledge_history", "knowledge_science", "knowledge_search", "knowledge_documents"]),
    ("K2", "knowledge map", "Its confident misses: questions Jev was 90%+ sure of and got wrong.",
     "a drawer of real misses", ["knowledge_arts", "knowledge_mind"]),
    ("C1b", "calibration", "When Jev is 90% sure it is right 94% of the time; when it is 55% sure, 52%.",
     "draw-first reliability diagram, dots sized by count", ["calibration"]),
    ("W1", "work", "Tasks Jev has mastered: classifying entities, spotting programming languages, reading receipts, flagging spam.",
     "dot plot of task accuracy with the noise band", ["task_dbpedia14", "task_code_lang", "task_receipts_extract", "task_sms_spam"]),
    ("W2", "work", "Its hardest jobs: log anomalies, essay grading, wine notes, commit-message types, sentence similarity.",
     "same dot plot, lowest end, with chance marked per task", ["task_hdfs_sessions", "task_asap_essays", "task_wine_notes", "task_commit_messages", "task_stsb_similarity"]),
    ("W3", "work", "Confidently wrong: on code clones Jev is right 54% of the time while sounding certain on 73% of them.",
     "accuracy vs decisiveness scatter, one labelled point", ["task_clone_pairs"]),
    ("J1", "jaggedness", "Jev cannot predict what a crowd finds funny: 56% on meme captions, 53% on jokes.",
     "two dots on a 50% line", ["humor_imgflip_captions", "humor_rjokes_pairs"]),
    ("J2", "jaggedness", "Its answers wobble most on language: word norms and grammar survive reordering least.",
     "before/after pairs of the same question", ["fragile_world.society.languages"]),
    ("J3", "jaggedness", "Its head-to-head picks and its own ratings of the same films only partly agree (rank correlation 0.58; books 0.34).",
     "scatter: pairwise strength vs own rating", ["favorites_movielens_pairs", "favorites_goodreads_pairs"]),
    ("J4", "jaggedness", "Jev separates itself from people mostly on taste and lifestyle, almost never on facts or tasks.",
     "frame-gap strip by domain", ["node_self.lifestyle", "node_self.lifestyle.food_preferences"]),
    ("S1", "stable core", "The stable core: code review, claim checking and spam answers that never move.",
     "ranked strip of the most stable domains", ["stable_machine.code.code_review", "stable_machine.trust_safety.spam_phishing"]),
    ("A1", "agreement", "Jev answers like the crowd 77% of the time on the arts and 39% on personality questions.",
     "dots per domain with intervals", ["crowd_arts", "crowd_personality", "crowd_food", "crowd_values"]),
    ("TH1", "atlas only", "Cross-cutting themes (AI, death, risk, honesty, money, animals, tradition, humor) with measured precision, in the atlas.",
     "atlas table", ["theme_attitudes_to_ai", "theme_death_and_meaning"]),
]


def main():
    L = {c["id"]: c for c in json.loads((A / "findings.json").read_text())["claims"]}
    q = {r["id"]: r for r in pl.read_parquet(A / "questions.parquet", columns=["id", "text", "top", "p_top", "humans"]).iter_rows(named=True)}
    out = ["# Portrait shortlist (for Brian)", "",
           "Pick the ones that make the page (budget ~25-35 findings, ~14 sections; taste capped at 2 sections).",
           "Each rests on ledger ids in data/analysis/findings.json. Examples are chosen by fixed seed, not by hand.",
           "Step 5 (robustness rewordings, the only Jev calls) runs on your picks after this review.", ""]
    missing = []
    for cid, section, head, chart, lids in PICKS:
        claims = [L[i] for i in lids if i in L]
        missing += [i for i in lids if i not in L]
        if not claims:
            continue
        c0 = claims[0]
        ex = []
        for e in [x for c in claims for x in c["examples"]][:2]:
            if e not in q:
                continue
            r = q[e]
            hs = json.loads(r["humans"]) if isinstance(r["humans"], str) else []
            h = max(hs, key=lambda x: x.get("n") or 0)["dist"] if hs else None
            htop = f"; people: {max(h, key=h.get)} ({max(h.values()):.0%})" if h else ""
            ex.append(f"  - \"{str(r['text'])[:150]}\" → Jev: {r['top']} ({r['p_top']:.0%}){htop}")
        out += [f"## {cid} · {section}", f"**{head}**", f"- chart: {chart}",
                f"- evidence: tier {c0['tier']}, n = {sum(c['n'] for c in claims):,}"
                + (f", 90% CI {c0['ci90']}" if c0.get("ci90") else "") + f"; ledger: {', '.join(lids)}", *ex, ""]
    (A / "shortlist.md").write_text("\n".join(out) + "\n")
    print(f"shortlist: {len(PICKS)} candidates -> {A / 'shortlist.md'}; missing ledger ids: {missing}")


if __name__ == "__main__":
    main()
