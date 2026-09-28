"""Taste experiments: ranked favorites per domain, and Jev's taste against real audiences (docs/15 "Taste").

Ranking uses the one-at-a-time ratings, not the thin head-to-heads: every item's expected level on its five-level
scale, averaged over the question as asked and the same question with the levels reversed (stored in the original
order), so a ranking that depends on option order shows up as a gap between the two.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, biggest, boot, js, level, source

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "portrait"))
from export_page import name_of  # noqa: E402

# domain: (node suffix, noun, plural display, catalog, audience source name or None)
DOMAINS = {
    "film": ("film_ratings", "film", "films", "MovieLens (films with enough ratings to be well known)", "MovieLens users"),
    "book": ("book_ratings", "book", "books", "Goodreads (books with many ratings)", "Goodreads readers"),
    "board_game": ("board_game_ratings", "board game", "board games", "BoardGameGeek (ranked games)", "BoardGameGeek users"),
    "anime": ("anime_ratings", "anime", "anime", "MyAnimeList (series and films)", "MyAnimeList users"),
    "beer": ("beer_ratings", "beer", "beers", "BeerAdvocate (reviewed beers)", "BeerAdvocate reviewers"),
    "music": ("music_ratings", "album or sound", "albums and sounds", "lists written for this project (classic albums, everyday sounds)", None),
    "food": ("food_ratings", "food", "foods", "lists written for this project (dishes, ingredients, cheeses, drinks)", None),
    "place": ("place_ratings", "place", "places", "lists written for this project (landmarks, cities, natural wonders)", None),
    "art": ("art_ratings", "artwork or art form", "artworks", "lists written for this project (famous works, genres)", None),
    "nature": ("nature_ratings", "animal, sight or smell in nature", "things in nature", "lists written for this project (animals, sights, smells, weather)", None),
    "activity": ("activity_ratings", "game or activity", "games and activities", "lists written for this project (video games, pastimes, events)", None),
    "culture": ("culture_ratings", "festival or tradition", "festivals and traditions", "lists written for this project (festivals, performances, media)", None),
}


def rated(dom: str) -> pl.DataFrame:
    """One row per rated item: robust level (mean of base and reversed), both levels, audience level if any."""
    node = DOMAINS[dom][0]
    q = source("taste_ratings", "g5_w13_ratings").filter(pl.col("node_id").str.ends_with(node))
    rows = []
    for r in q.iter_rows(named=True):
        base = level(js(r["jev_dist"]))
        rev = next((level(v["dist"]) for v in js(r["variants"]) or [] if v["kind"] == "reversed_levels"), None)
        h = biggest(r["humans"])
        rows.append({"id": r["id"], "name": name_of(r["text"]), "base": base, "rev": rev,
                     "score": (base + rev) / 2 if rev is not None else base,
                     "people": level(js(r["people_dist"])), "aud": level(h["dist"]) if h else None,
                     "aud_n": h.get("n") if h else None})
    return pl.DataFrame(rows).sort("score", descending=True)


def ranked(dom: str):
    key, noun, plural, catalog, _ = DOMAINS[dom]
    spec = Spec(
        id=f"taste_top_{dom}", family="taste", title=f"Jev's favorite {plural}, ranked",
        question=f"If Jev ranked every {noun} it was asked about, what would its top ten be?",
        why="Wrapped-style favorites, but from every item it rated rather than a handful of head-to-heads; the "
            "interesting part is what rises to the top and what sinks.",
        sourcing=f"Existing one-at-a-time rating questions (\"How much would you enjoy ...\", five situation-described "
                 f"levels) under Self > Lifestyle > Ratings > {key}; items from {catalog}. Enough: every item is rated, "
                 "so the whole list can be ranked; the old head-to-heads (about 7 per item) are too thin to rank.",
        scoring="Each item's expected level (0-4) from Jev's probability over the five levels, averaged with the same "
                "question asked with the levels reversed; the gap between the two shows how much the order of the "
                "options matters. Ties are left as ties. The top 24 go to a head-to-head final (taste_finals).",
        chart="A ranked list, Wrapped style: the top ten with their level bars, and the bottom five for contrast.",
        compared_with="nothing outside the model: a ranking of Jev's own ratings",
        limits=f"A winner is only the best of what was on the list ({catalog}). Levels are Jev's probabilities over "
               "described situations, not a star rating.",
        sources=["taste_ratings" if DOMAINS[dom][4] else "g5_w13_ratings"],
    )

    def run():
        t = rated(dom)
        if t.height < 50:
            return None
        gap = float((t["base"] - t["rev"]).abs().mean()) if t["rev"].is_not_null().any() else None
        top10 = t.head(10).to_dicts()
        bottom = t.tail(5).reverse().to_dicts()
        rho = spearmanr(t["base"], t["rev"], nan_policy="omit").statistic if t["rev"].is_not_null().sum() > 20 else None
        names = ", ".join(x["name"] for x in top10[:3])
        return Result(
            result=f"Out of {t.height:,} {plural}, Jev's top three are {names}; its least favorite is {bottom[0]['name']}.",
            evidence=f"{t.height:,} items rated; rank agreement between the question as asked and with reversed levels "
                     f"{rho:.2f}" if rho is not None else f"{t.height:,} items rated",
            numbers={"n": t.height, "top": top10, "bottom": bottom, "mean_abs_gap_reversed": gap, "rho_reversed": rho},
            chart={"type": "ranked", "items": [{"label": x["name"], "value": round(x["score"], 2)} for x in top10],
                   "bottom": [{"label": x["name"], "value": round(x["score"], 2)} for x in bottom], "max": 4},
            examples=[x["id"] for x in top10[:2]] + [bottom[0]["id"]], n=t.height,
            robustness=f"Rank correlation between base and reversed-level answers: {rho:.2f}." if rho is not None else "")
    return spec, run


def audience(dom: str):
    key, noun, plural, catalog, aud = DOMAINS[dom]
    spec = Spec(
        id=f"taste_vs_audience_{dom}", family="taste", title=f"Jev's taste in {plural} vs {aud}",
        question=f"Does Jev like the {plural} that {aud} like, and where does it disagree most?",
        why="A real test of taste against a real crowd, not against Jev's own guess about people; the disagreements "
            "are the portrait.",
        sourcing=f"Existing rating questions under Self > Lifestyle > Ratings > {key}, each with the real rating "
                 f"distribution of {aud} (their ratings binned to the same five levels). Enough: thousands of items.",
        scoring="Rank correlation (Spearman) between Jev's robust level and the audience's mean level, with a 90% "
                "bootstrap interval over items; the items with the largest rank disagreement in each direction. Ranks, "
                "not levels, because Jev's described levels and the audience's star ratings aren't the same scale.",
        chart="A scatter of audience rank vs Jev's rank, with the ten biggest disagreements labeled on each side.",
        compared_with=f"{aud} (their average rating of each item)",
        limits="Audiences rate what they chose to watch or drink; Jev rates everything. Rank comparisons only.",
        sources=["taste_ratings"],
    )

    def run():
        t = rated(dom).filter(pl.col("aud").is_not_null())
        if t.height < 100:
            return None
        rho = spearmanr(t["score"], t["aud"]).statistic
        idx = np.arange(t.height)
        ci = boot(idx, stat=lambda ii: spearmanr(t["score"].to_numpy()[ii.astype(int)], t["aud"].to_numpy()[ii.astype(int)]).statistic, b=300)
        t = t.with_columns((pl.col("score").rank() / t.height).alias("rj"), (pl.col("aud").rank() / t.height).alias("ra"))
        t = t.with_columns((pl.col("rj") - pl.col("ra")).alias("d"))
        more = t.sort("d", descending=True).head(10).to_dicts()
        less = t.sort("d").head(10).to_dicts()
        return Result(
            result=f"Jev's ranking of {t.height:,} {plural} agrees {agree_word(rho)} with {aud}' (rank correlation "
                   f"{rho:.2f}). It likes {more[0]['name']} and {more[1]['name']} far more than they do, and "
                   f"{less[0]['name']} and {less[1]['name']} far less.",
            evidence=f"{t.height:,} items; 90% interval {ci[0]:.2f} to {ci[1]:.2f}",
            numbers={"n": t.height, "rho": rho, "ci90": ci, "more": more, "less": less},
            chart={"type": "rankscatter", "points": t.select("rj", "ra").to_numpy().round(3).tolist(),
                   "labels": [{"label": x["name"], "x": x["ra"], "y": x["rj"]} for x in more[:5] + less[:5]],
                   "x": f"{aud}' rank", "y": "Jev's rank"},
            examples=[more[0]["id"], less[0]["id"]], n=t.height)
    return spec, run


def self_vs_guess():
    spec = Spec(
        id="taste_self_vs_guess", family="taste", title="Where Jev thinks its taste differs from everyone's",
        question="In which kinds of things does Jev rate itself differently from how it thinks most people would?",
        why="The gap between 'I'd like this' and 'most people would like this' is how a model separates itself from "
            "the crowd; the domains and items where it's largest say what it thinks is distinctive about itself.",
        sourcing="Every rating question in the 12 taste domains, asked for Jev and again for 'most people' (the human "
                 "frame every question carries). Enough: ~20,000 items.",
        scoring="Per domain, mean of (Jev's level minus its level for most people), with a 90% bootstrap interval over "
                "items; the items with the largest gap either way.",
        chart="A dot plot, one row per domain, with the gap and its interval; top items per side as labels.",
        compared_with="Jev's own guess about most people (not real people; the audience experiments do that)",
        limits="Both sides are Jev's answers; this is self-image, not a comparison with a crowd.",
        sources=["taste_ratings", "g5_w13_ratings"],
    )

    def run():
        rows, tops = [], {}
        for dom in DOMAINS:
            t = rated(dom).filter(pl.col("people").is_not_null())
            if t.height < 50:
                continue
            g = (t["base"] - t["people"]).to_numpy()
            rows.append({"domain": DOMAINS[dom][2], "gap": float(g.mean()), "ci90": boot(g), "n": t.height})
            tt = t.with_columns((pl.col("base") - pl.col("people")).alias("g")).sort("g")
            tops[dom] = {"above": tt.tail(3).reverse()["name"].to_list(), "below": tt.head(3)["name"].to_list()}
        rows.sort(key=lambda r: r["gap"])
        lo, hi = rows[0], rows[-1]
        return Result(
            result=f"Jev rates things lower for itself than for most people in almost every domain, most in "
                   f"{lo['domain']} ({lo['gap']:+.2f} levels) and least in {hi['domain']} ({hi['gap']:+.2f}).",
            evidence=f"{sum(r['n'] for r in rows):,} items across {len(rows)} domains",
            numbers={"domains": rows, "items": tops},
            chart={"type": "dots", "rows": [{"label": r["domain"], "value": r["gap"], "ci": r["ci90"]} for r in rows], "zero": 0},
            n=sum(r["n"] for r in rows))
    return spec, run


EXPERIMENTS = [ranked(d) for d in DOMAINS] + [audience(d) for d in DOMAINS if DOMAINS[d][4]] + [self_vs_guess()]
