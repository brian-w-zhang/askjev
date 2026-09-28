"""Taste experiments: ranked favorites per domain, and Jev's taste against real audiences (docs/15 "Taste").

Ranking uses the one-at-a-time ratings, not the thin head-to-heads: every item's expected level on its five-level
scale, averaged over the question as asked and the same question with the levels reversed (stored in the original
order), so a ranking that depends on option order shows up as a gap between the two.
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from lib import Result, Spec, agree_word, and_list, biggest, boot, js, level, norm, source, with_meta

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


def _game(r: dict) -> tuple[str, str, str, str, float, list[dict]]:
    """One finals game: (a, b, a's name, b's name, Jev's probability for a averaged over option orders, the
    distributions). The options come back key-sorted, so each is matched to its item by the item's key, not position."""
    opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
    a, b = r["m"]["a"], r["m"]["b"]
    pool = _pool()
    ka = next((k for k in opts if k == _fkey(pool.get(a, ""))), None)
    if ka is None:  # a name collision got the "_2" suffix: a is whichever key isn't b's
        kb0 = _fkey(pool.get(b, ""))
        ka = next(k for k in opts if k != kb0)
    kb = next(k for k in opts if k != ka)
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle"]
    return a, b, opts[ka], opts[kb], float(np.mean([d.get(ka, 0.0) for d in ds])), [{"k": ka, "d": d} for d in ds]


@lru_cache(maxsize=1)
def _pool() -> dict:
    p = json.loads(Path("data/raw/taste_finals/top24.json").read_text())
    return {i["id"]: i["name"] for v in p.values() for i in v["items"]}


def _fkey(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:60]  # sources/taste_finals._key


def finals(dom: str) -> list[dict] | None:
    """The round-robin finals among the domain's top 24 (sources/taste_finals): each item's wins (Jev's probability
    for it, averaged over both option orders, summed over its 23 games) and Bradley-Terry strength. None if not run."""
    games = [r for r in with_meta("taste_finals") if r["m"].get("domain") == dom] if dom else []
    if not games:
        return None
    ids, names, p = [], {}, {}
    for r in games:
        a, b, na, nb, pa, _ = _game(r)
        names[a], names[b] = na, nb
        p[(a, b)] = pa
    ids = sorted(names)
    ix = {i: n for n, i in enumerate(ids)}
    w = np.zeros((len(ids), len(ids)))
    for (a, b), pa in p.items():
        w[ix[a], ix[b]], w[ix[b], ix[a]] = pa, 1 - pa
    s_ = np.ones(len(ids))
    for _ in range(500):  # Bradley-Terry by minorization-maximization, soft wins
        tot = w.sum(1)
        den = np.array([sum((w[i, j] + w[j, i]) / (s_[i] + s_[j]) for j in range(len(ids)) if j != i) for i in range(len(ids))])
        s_ = tot / den
        s_ /= np.exp(np.mean(np.log(s_)))
    out = [{"id": i, "name": names[i], "wins": float(w[ix[i]].sum()), "strength": float(np.log(s_[ix[i]]))} for i in ids]
    out.sort(key=lambda x: -x["strength"])
    # intransitive triads: a beats b, b beats c, c beats a (majority choices)
    beats = w > 0.5
    n, cyc = len(ids), 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if (beats[i, j] and beats[j, k] and beats[k, i]) or (beats[j, i] and beats[k, j] and beats[i, k]):
                    cyc += 1
    out[0]["_cycles"], out[0]["_triads"] = cyc, n * (n - 1) * (n - 2) // 6
    return out


def ranked(dom: str):
    key, noun, plural, catalog, _ = DOMAINS[dom]
    spec = Spec(
        id=f"taste_top_{dom}", family="taste", title=f"Jev's favorite {plural}, ranked",
        question=f"If Jev ranked every {noun} it was asked about, what would its top ten be?",
        why="Wrapped-style favorites, but from every item it rated and then a real final among the best, rather than a "
            "handful of head-to-heads; the interesting part is what rises to the top and what sinks.",
        sourcing=f"Existing one-at-a-time rating questions (\"How much would you enjoy ...\", five situation-described "
                 f"levels) under Self > Lifestyle > Ratings > {key}; items from {catalog}. Every item is rated, so the "
                 "whole list can be ranked; the ratings crowd the top with near-ties, so the top 24 play a round-robin "
                 "final (new questions, sources/taste_finals).",
        collection="The ratings exist. New: the finals, 276 head-to-heads among the top 24 (\"Which film would you "
                   "rather watch?\"), each asked in both option orders.",
        scoring="Ratings: each item's expected level (0-4), averaged with the same question asked with the levels "
                "reversed. Finals: Jev's probability for each side, averaged over both orders, summed into soft wins; "
                "the order is the Bradley-Terry strength fitted to all 276 games. Intransitive triads (A beats B, B "
                "beats C, C beats A) are counted as a consistency check.",
        chart="A ranked list, Wrapped style: the finals' top ten with their win counts, and the ratings' bottom five for "
              "contrast.",
        compared_with="nothing outside the model: a ranking of Jev's own ratings and choices",
        limits=f"A winner is only the best of what was on the list ({catalog}). Finalists were chosen by Jev's own "
               "ratings, so an item it underrated never reached the final.",
        new_questions=276, sources=["taste_ratings" if DOMAINS[dom][4] else "g5_w13_ratings", "taste_finals"],
    )

    def run():
        t = rated(dom)
        if t.height < 50:
            return None
        rho = spearmanr(t["base"], t["rev"], nan_policy="omit").statistic if t["rev"].is_not_null().sum() > 20 else None
        bottom = t.tail(5).reverse().to_dicts()
        fin = finals(dom)
        if fin:
            top10 = fin[:10]
            # the ratings' order of the 24 finalists, as taste_choices_vs_ratings reads it
            rate_order = {it["id"]: n for n, it in enumerate(json.loads(Path("data/raw/taste_finals/top24.json").read_text())[dom]["items"])}
            first_by_rating = t.row(0, named=True)["name"]
            cyc, tri = fin[0]["_cycles"], fin[0]["_triads"]
            moved = spearmanr([rate_order[x["id"]] for x in fin], list(range(len(fin)))).statistic
            head = (f"Out of {t.height:,} {plural}, Jev's final among its 24 favorites crowns {top10[0]['name']} "
                    f"({top10[0]['wins']:.1f} wins of 23), ahead of {top10[1]['name']} and {top10[2]['name']}"
                    + ("" if first_by_rating == top10[0]["name"] else f"; the ratings alone had put {first_by_rating} first")
                    + f". Least favorite of all: {bottom[0]['name']}.")
            rob = (f"The finals keep the ratings' order only loosely (rank correlation {moved:.2f} among the 24). "
                   f"{cyc} of {tri} triads are intransitive ({cyc / tri:.1%}). Base vs reversed-level ratings: "
                   f"rank correlation {rho:.2f}." if rho is not None else "")
            items = [{"label": x["name"], "value": round(x["wins"], 1)} for x in top10]
            extra = {"rho_ratings_vs_finals": float(moved), "loops": cyc / tri}
        else:
            top10 = t.head(10).to_dicts()
            head = (f"Out of {t.height:,} {plural}, Jev's top three are {and_list([x['name'] for x in top10[:3]])}; "
                    f"its least favorite is {bottom[0]['name']}.")
            rob = f"Rank correlation between base and reversed-level answers: {rho:.2f}." if rho is not None else ""
            items = [{"label": x["name"], "value": round(x["score"], 2)} for x in top10]
            extra = {}
        return Result(
            result=head,
            evidence=f"{t.height:,} items rated" + ("; 276 final games among the top 24" if fin else ""),
            numbers={"n": t.height, "top": top10, "bottom": bottom, "rho_reversed": rho, **extra,
                     "finals": [{k: v for k, v in x.items() if not k.startswith("_")} for x in fin] if fin else None},
            chart={"type": "ranked", "items": items, "unit": "wins of 23" if fin else "level (0-4)",
                   "bottom": [{"label": x["name"], "value": round(x["score"], 2)} for x in bottom]},
            examples=[x["id"] for x in top10[:2]] + [bottom[0]["id"]], n=t.height, robustness=rob)
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


def intransitive():
    spec = Spec(
        id="taste_choices_vs_ratings", family="taste", title="Jev's head-to-heads are consistent, and overrule its ratings",
        question="When Jev's 24 top-rated films (or books, foods, places...) play every other one head to head, are its "
                 "choices consistent, and do they agree with the order its ratings gave them?",
        why="A favorites list can come from ratings (one item at a time) or from choices (two at a time). For people "
            "the two often disagree near the top; if Jev's choices are consistent but reorder its ratings, its "
            "'favorite' depends on how you ask.",
        sourcing="The taste finals (sources/taste_finals): 276 head-to-heads among the top 24 of each of 12 domains, "
                 "3,281 shown, each asked in both option orders; the finalists and their rating order come from the "
                 "rating questions (taste_top_*).",
        collection="Uses the taste finals' new questions (no further calls).",
        scoring="Consistency: every triple of finalists is a triad, intransitive when the majority choices form a cycle "
                "(a random tournament has 25%, a perfectly consistent chooser 0%), overall and among triads whose three "
                "picks are all 70/30 or firmer. Agreement: rank correlation between the ratings' order of the 24 and "
                "the finals' Bradley-Terry order, per domain.",
        chart="Dots per domain: rank correlation between the ratings' order and the finals' order, with the share of "
              "intransitive triads as a label.",
        compared_with="a random tournament (25% loops) and Jev's own ratings of the same items",
        limits="Finalists are near the top of Jev's own ratings, so rating differences among them are small; a low "
               "correlation there says the ratings can't separate them, and the choices can.", sources=["taste_finals"])

    def run():
        rows, same, lean = [], [], []
        firm_all = firm_cyc_all = 0
        pool = json.loads(Path("data/raw/taste_finals/top24.json").read_text())
        for dom in DOMAINS:
            games = [r for r in with_meta("taste_finals") if r["m"].get("domain") == dom]
            if not games:
                continue
            p, names = {}, {}
            for r in games:
                a, b, na, nb, pa, ds = _game(r)
                same += [(ds[0]["d"].get(ds[0]["k"], 0) > 0.5) == (float(np.mean([x["d"].get(x["k"], 0) for x in ds[1:]])) > 0.5)] if len(ds) > 1 else []
                lean.append(max(pa, 1 - pa))
                names[a], names[b] = na, nb
                p[(a, b)], p[(b, a)] = pa, 1 - pa
            ids = sorted(names)
            cyc = firm = firm_cyc = tri = 0
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    for k in range(j + 1, len(ids)):
                        a, b, c = ids[i], ids[j], ids[k]
                        if (a, b) not in p or (b, c) not in p or (a, c) not in p:
                            continue
                        tri += 1
                        ab, bc, ca = p[(a, b)] > 0.5, p[(b, c)] > 0.5, p[(c, a)] > 0.5
                        loop = (ab and bc and ca) or (not ab and not bc and not ca)
                        strong = all(abs(p[x] - 0.5) >= 0.2 for x in ((a, b), (b, c), (c, a)))
                        cyc += loop
                        firm += strong
                        firm_cyc += loop and strong
            firm_all += firm
            firm_cyc_all += firm_cyc
            fin = finals(dom)
            rate_rank = {it["id"]: n for n, it in enumerate(pool[dom]["items"])}
            rho = spearmanr([rate_rank[x["id"]] for x in fin], list(range(len(fin)))).statistic
            rows.append({"domain": DOMAINS[dom][2], "loops": cyc / tri, "rho": float(rho), "triads": tri,
                         "rating_first": pool[dom]["items"][0]["name"], "final_first": fin[0]["name"]})
        rows.sort(key=lambda r: r["rho"])
        loops = float(np.mean([r["loops"] for r in rows]))
        med = float(np.median([r["rho"] for r in rows]))
        changed = [r for r in rows if r["rating_first"] != r["final_first"]]
        ex = next((r for r in rows if r["domain"] == "albums and sounds" and r in changed), changed[0] if changed else None)
        return Result(
            result=f"Jev's head-to-head choices among its 24 favorites are consistent: only {loops:.0%} of triads go in a "
                   f"circle, where a random tournament has 25%, and none of the {firm_all:,} triads with firm picks do. "
                   f"But they overrule its ratings: the finals keep the ratings' order only loosely (median rank "
                   f"correlation {med:.2f} across 12 domains) and crown a different favorite in {len(changed)} of 12"
                   + (f"; for {ex['domain']} the ratings put {ex['rating_first']} first, the finals {ex['final_first']}." if ex else "."),
            evidence=f"{sum(r['triads'] for r in rows):,} triads and 3,281 games in {len(rows)} domains",
            numbers={"domains": rows, "loops": loops, "median_rho": med, "firm_triads": firm_all, "firm_loops": firm_cyc_all},
            n=sum(r["triads"] for r in rows),
            chart={"type": "dots", "rows": [{"label": r["domain"], "value": r["rho"], "right": f"{r['loops']:.0%} loops"} for r in rows],
                   "domain": [-1, 1], "zero": 0},
            robustness=f"{np.mean(same):.0%} of picks are the same whichever option is listed first; the average pick puts "
                       f"{np.mean(lean):.0%} on one side.")
    return spec, run

EXPERIMENTS = [ranked(d) for d in DOMAINS] + [audience(d) for d in DOMAINS if DOMAINS[d][4]] + [self_vs_guess(), intransitive()]
