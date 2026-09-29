"""Portrait §3b (docs/11-portrait.md): the data landscape. Where the 1.09M questions come from and what shape they
have, as claims appended to data/analysis/findings.json (replacing any earlier landscape claims), plus the full
per-source table at data/analysis/landscape_sources.parquet for the atlas. Pure Polars; counts use every question
(shown and hidden) except where a claim says "shown".

  uv run python scripts/portrait/landscape.py      # after findings.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl

from askjev import db

A = Path("data/analysis")
FAMILIES = [  # (family, regex over source name); first match wins; authored banks are decided by origin
    ("instruments & norms", r"^(ipip|ipip_neo_norms|openpsych|icar_sapa|oejts|mfq|bbrs_risk|lancaster|lancaster_modality|glasgow_norms|concreteness|iconicity_ratings|pseudoword_shapes|bouba_kiki|choices13k|wulff_description|behavioral_econ|moral_vignettes|onet_interests|scalar_adjectives|scalar_implicature|metaphor_norms|humor_words|idiom_norms|category_norms|word_associations|mind_perception|recall_norms|health_states|perception_words|mental_maps|wellbeing)$"),
    ("polls & surveys", r"^(reddit_polls|reddit_hobby_polls|gss|pisa_questionnaire|afrobarometer|globalopinionqa|young_people_survey|philpapers_survey|aims_survey|mxmh_music|color_favorites|wyr|protoqa|onet_context|color_emotion|country_values|trolley_countries|science_literacy|ai_attitudes|fair_prices|gallup_honesty|occupation_prestige)$"),
    ("crowd judgments", r"^(moral_machine|social_chem|scruples|scruples_anecdotes|social_iqa|moral_stories|moralchoice|daily_dilemmas|ethics_.*|humicroedit|caption_contest|jester|storycommonsense|empathetic_dialogues|isear|character_traits|emoji_sentiment|xkcd_colors|crowd_envent|chaosnli|politeness|crowd_estimates|effort_forecasts|ai_poetry)$"),
    ("taste pairs & ratings", r"(_pairs$|^taste_ratings$|^food_538$)"),
    ("internet culture", r"^(imgflip_captions|rjokes_pairs|wikidata_memes)$"),
    ("real asked questions", r"^(stackexchange_closed|quora_closed|yahoo_closed|wildchat_closed|ask-box|manifold)$"),
    ("records & statistics", r"^(baby_names|bls_prices|lethal_events|whr_ladder|atus_day|lost_wallets|vehicles_park|upworthy_headlines)$"),
    ("experiment designs", r"^(taste_finals|influence_variants|reasoning_traps|beauty_contest|philosophy_vignettes|anchoring)$"),
    ("knowledge & exams", r"^(mmlu|arc|sciq|openbookqa|boolq|strategyqa|truthfulqa|commonsense_qa|medmcqa|head_qa|uscg_mariner|nrc_gfe|ham_radio_pools|uscis_civics|opentdb|natural_questions_yn|vital\d*|wikidata_.*|pantheon_.*|worldbank_pairs|usda_nutrients|anage_pairs|wikidata_companies|hotpot_compare|nba)$"),
]


def family(source: str, origin: str, hemisphere: str) -> str:
    if origin == "synthetic" or source == "g2_menus":
        return "authored banks"
    if source in ("rjokes_pairs",):
        return "internet culture"
    for name, rx in FAMILIES:
        if re.search(rx, source):
            if name == "taste pairs & ratings" and source in ("worldbank_pairs", "anage_pairs"):
                return "knowledge & exams"
            return name
    return "machine task datasets" if hemisphere == "machine" else "other"


def main():
    q = pl.read_parquet(A / "questions.parquet", columns=["id", "source", "origin", "hemisphere", "kind", "primitive",
                                                           "options", "truth", "humans", "display_ok", "harmful", "flags",
                                                           "node_id", "l1", "jev_dist"])
    q = q.with_columns(pl.struct(["source", "origin", "hemisphere"]).map_elements(
        lambda r: family(r["source"], r["origin"], r["hemisphere"]), return_dtype=pl.Utf8).alias("family"),
        pl.col("truth").is_not_null().alias("has_truth"), pl.col("humans").is_not_null().alias("has_humans"))
    N = q.height
    claims = []

    def add(cid, sentence, n, effect, **extra):
        claims.append({"id": cid, "section": "landscape", "sentence": sentence, "tier": "corpus", "n": int(n),
                       "effect": effect, "ci90": None, "examples": [], "script": "scripts/portrait/landscape.py", **extra})

    fam = q.group_by("family").agg(n=pl.len(), sources=pl.col("source").n_unique(),
                                   truth=pl.col("has_truth").mean(), humans=pl.col("has_humans").mean()).sort("n", descending=True)
    add("landscape_families", f"{N:,} questions from {q['source'].n_unique()} sources in {fam.height} families.", N, None,
        families=fam.to_dicts())
    auth = q.filter(pl.col("family") == "authored banks").height
    add("landscape_real_vs_authored", f"{1 - auth / N:.0%} of questions come from real data; {auth / N:.0%} were written for "
        f"this project and filtered by a blind round trip.", N, round(1 - auth / N, 3))
    prim = q.group_by("hemisphere", "primitive").agg(pl.len()).sort("hemisphere", "primitive")
    add("landscape_primitives", "How the three answer shapes (yes/no, pick one, rate) split across World, Self and Machine.",
        N, None, primitives=prim.to_dicts())
    kinds = q.filter(pl.col("hemisphere") != "machine").group_by("kind").agg(pl.len()).sort("len", descending=True)
    add("landscape_kinds", "What the World and Self questions ask about: facts, taste, judgments, social norms, values, "
        "personality, perception, forecasts.", kinds["len"].sum(), None, kinds=kinds.to_dicts())
    anch = q.select(truth=pl.col("has_truth").mean(), humans=pl.col("has_humans").mean(),
                    both=(pl.col("has_truth") & pl.col("has_humans")).mean(),
                    neither=(~pl.col("has_truth") & ~pl.col("has_humans")).mean()).to_dicts()[0]
    with db.connect() as c:
        resp = c.execute("select count(*) c, percentile_cont(0.5) within group (order by n) med from human_dists where n is not null").fetchone()
        calls = c.execute("select count(*) c from probes").fetchone()["c"]
        answers = c.execute("select count(*) c from answers").fetchone()["c"]
    add("landscape_anchoring", f"{anch['truth']:.0%} of questions have a right answer and {anch['humans']:.0%} have real human "
        f"answers ({resp['c']:,} human answer distributions, median {int(resp['med']):,} people each); {anch['neither']:.0%} have neither.",
        N, round(1 - anch["neither"], 3), anchoring=anch, human_distributions=resp["c"], median_n=resp["med"])
    fl = q.filter(~pl.col("display_ok"))
    reasons = {}
    for f in fl["flags"].fill_null(""):
        for x in [y for y in f.split(",") if y in ("sensitive", "political", "duplicate", "biographical", "harmful")] or ["other"]:
            reasons[x] = reasons.get(x, 0) + 1
    add("landscape_hidden", f"{fl.height:,} questions ({fl.height / N:.1%}) are answered and measured but hidden from the map.",
        fl.height, round(fl.height / N, 4), reasons=reasons)
    opt = q.filter(pl.col("primitive") == "choice").with_columns(
        pl.col("options").map_elements(lambda s: len(json.loads(s)) if s else None, return_dtype=pl.Int64).alias("k"))
    add("landscape_options", "How many options each pick-one question offers.", opt.height, None,
        option_counts=opt.group_by("k").agg(pl.len()).sort("k").to_dicts())
    depth = q.with_columns(pl.col("node_id").str.count_matches(r"\.").alias("d")).group_by("d").agg(pl.len()).sort("d")
    add("landscape_tree", f"The questions sit on {q['node_id'].n_unique():,} topic nodes up to {depth['d'].max() + 1} levels deep.",
        q["node_id"].n_unique(), None, depth=depth.to_dicts())
    add("landscape_jev", f"Jev answered every question several ways: {calls:,} probes and {answers:,} answers "
        f"(the question as asked, 'most people', reordered options, reversed scales).", calls, answers)
    src = q.group_by("source", "family", "hemisphere").agg(n=pl.len(), truth=pl.col("has_truth").mean(),
                                                            humans=pl.col("has_humans").mean(), shown=pl.col("display_ok").mean()).sort("n", descending=True)
    src.write_parquet(A / "landscape_sources.parquet")
    other = src.filter(pl.col("family") == "other")
    L = json.loads((A / "findings.json").read_text())
    L["claims"] = [c for c in L["claims"] if c.get("section") != "landscape"] + claims
    L["n_claims"] = len(L["claims"])
    (A / "findings.json").write_text(json.dumps(L, indent=1, default=str))
    print(fam)
    print(f"landscape: {len(claims)} claims; unmapped 'other' sources: {other['source'].to_list()[:20]}")


if __name__ == "__main__":
    main()
