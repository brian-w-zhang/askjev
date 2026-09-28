"""Taste against real audiences, head to head (docs/16 round 3): the catalog head-to-heads (MovieLens, Goodreads,
BoardGameGeek, MyAnimeList, BeerAdvocate, Last.fm), each with the share of real users who preferred each side, and
the favorites polls on r/polls.

Different method from taste_vs_audience_* (fam_taste.py), which rank one-at-a-time ratings: here Jev picks one of two
and the audience's split is the users who rated (or played) both. Options come back key-sorted from the table, so
everything is matched by option key, never by position; the per-item meta lists (years, rating counts) are in item-id
order, so they are matched to options through the year or style printed in the option's label.
"""

from __future__ import annotations

import re

import numpy as np
import polars as pl

from lib import Result, Spec, biggest, boot, js, norm, seeded, top, with_meta

PAIRS = {  # source: (plural, audience, what the split measures)
    "movielens_pairs": ("films", "MovieLens users", "rated it higher"),
    "goodreads_pairs": ("books", "Goodreads readers", "rated it higher"),
    "boardgame_pairs": ("board games", "BoardGameGeek users", "rated it higher"),
    "anime_pairs": ("anime", "MyAnimeList users", "rated it higher"),
    "beer_pairs": ("beers", "BeerAdvocate reviewers", "scored it higher"),
    "music_pairs": ("artists", "Last.fm listeners", "played it more"),
}


def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def games(src: str) -> list[dict]:
    out = []
    for r in with_meta(src):
        h = biggest(r["humans"])
        if not h:
            continue
        hd, j, g = norm(h["dist"]), robust(r), norm(js(r["people_dist"]) or {})
        opts = js(r["options"]) if isinstance(r["options"], str) else r["options"]
        out.append({"id": r["id"], "hd": hd, "j": j, "g": g, "m": r["m"], "opts": opts, "n": h.get("n") or 0,
                    "aud": top(hd), "self": top(j), "guess": top(g) if g else None, "margin": abs(max(hd.values()) - 0.5)})
    return out


def attrs(src: str, x: dict) -> dict | None:
    """option key -> (first attribute, popularity): (year, ratings) for films and board games, (ABV, reviews) for
    beers; None when the two items can't be told apart by the label."""
    m, o = x["m"], x["opts"]
    if src in ("movielens_pairs", "boardgame_pairs"):
        yrs = m.get("years")
        if not yrs or yrs[0] == yrs[1]:
            return None
        res = {}
        for k, lab in o.items():
            y = re.search(r"\((\d{4})\)\s*$", lab or "")
            if not y or int(y.group(1)) not in yrs:
                return None
            i = yrs.index(int(y.group(1)))
            res[k] = (yrs[i], m["ratings_n"][i])
        return res if len(res) == 2 else None
    if src == "beer_pairs":
        st = m.get("styles")
        if not st or st[0] == st[1]:
            return None
        res = {}
        for k, lab in o.items():
            hit = [i for i, s in enumerate(st) if lab and lab.endswith(f"({s})")]
            if len(hit) != 1:
                return None
            res[k] = (m["abv"][hit[0]], m["reviews_n"][hit[0]])
        return res if len(res) == 2 else None
    return None


def audience_pairs():
    spec = Spec(
        id="taste_pairs_audience", family="taste", title="Jev's own picks match audiences better than its guesses do",
        question="Offered two films, books, board games, anime, beers or artists, does Jev pick the one the real "
                 "audience preferred, and is it closer when choosing for itself or when guessing what most people would pick?",
        why="Head-to-heads are how people actually choose. The audiences' splits are real (users who rated or played "
            "both), so they test Jev's taste directly; comparing its own pick with its guess of 'most people' shows "
            "which of its two views of taste is closer to real crowds.",
        sourcing="Existing head-to-head questions ('Which movie would you rather watch?') from six catalogs, each with the "
                 "share of users who rated (or played) both and preferred each side: MovieLens 32M, goodbooks-10k, "
                 "BoardGameGeek, MyAnimeList, BeerAdvocate, Last.fm 360K. About 27,000 pairs. A different method from "
                 "taste_vs_audience_* (one-at-a-time ratings).",
        scoring="Per catalog, the share of pairs where Jev's own pick (averaged over both option orders) is the "
                "audience's majority, and the same for its 'most people' guess, with 90% bootstrap intervals over pairs; "
                "agreement by the audience's margin (how lopsided the split was).",
        chart="Dots per catalog: agreement of Jev's own pick (square) and of its guess for most people (ring), with a "
              "50% line.",
        compared_with="the audiences of six catalogs (users who rated or played both items)",
        limits="Audiences rate what they chose to watch or read, so their splits lean toward fans. Last.fm's split is "
               "play counts, not ratings. Pairs were drawn within genre, so many are close calls.",
        sources=list(PAIRS))

    def run():
        rows, ex = [], []
        for src, (plural, aud, _) in PAIRS.items():
            g = games(src)
            s = np.array([x["self"] == x["aud"] for x in g], float)
            gs = np.array([x["guess"] == x["aud"] for x in g if x["guess"]], float)
            mar = np.array([x["margin"] for x in g])
            by = [float(s[(mar >= lo) & (mar < hi)].mean()) if ((mar >= lo) & (mar < hi)).sum() >= 30 else None
                  for lo, hi in ((0, 0.05), (0.05, 0.15), (0.15, 0.3), (0.3, 1))]
            rows.append({"label": plural, "audience": aud, "self": float(s.mean()), "guess": float(gs.mean()),
                         "ci": boot(s), "n": len(g), "by_margin": by})
            clear = [x for x in g if x["margin"] >= 0.2 and x["self"] != x["aud"] and x["j"][x["self"]] >= 0.8]
            ex += seeded([x["id"] for x in clear], src, 1)
        rows.sort(key=lambda r: -r["self"])
        wins = sum(r["self"] > r["guess"] for r in rows)
        flat = [r for r in rows if r["by_margin"][-1] is not None and r["by_margin"][-1] - r["by_margin"][0] < 0.15]
        top_, low = rows[0], rows[-1]
        return Result(
            result=f"Picking for itself, Jev sides with the audience in {top_['self']:.0%} of {top_['label']} head-to-heads "
                   f"down to {low['self']:.0%} for {low['label']}. Its own pick is closer to real audiences than its "
                   f"guess of what most people would pick in {wins} of {len(rows)} catalogs (films {rows_by(rows, 'films')['self']:.0%} "
                   f"vs {rows_by(rows, 'films')['guess']:.0%}). The more lopsided the audience, the more it agrees"
                   + (f", except for {', '.join(r['label'] for r in flat)}, where it stays near a coin flip even when "
                      f"the audience is clear." if flat else "."),
            evidence=f"{sum(r['n'] for r in rows):,} pairs in 6 catalogs; 90% intervals over pairs: "
                     + "; ".join(f"{r['label']} {r['ci']}" for r in rows),
            numbers={"catalogs": rows}, n=sum(r["n"] for r in rows),
            chart={"type": "dots", "domain": [0.4, 1], "ref": 0.5,
                   "rows": [{"label": r["label"], "value": r["self"], "guess": r["guess"], "ci": r["ci"],
                             "right": f"{r['self']:.0%}"} for r in rows]},
            robustness="Agreement by the audience's margin (under 5 points, 5-15, 15-30, over 30): "
                       + "; ".join(f"{r['label']} " + " / ".join("–" if b is None else f"{b:.0%}" for b in r["by_margin"]) for r in rows) + ".",
            examples=ex)
    return spec, run


def rows_by(rows: list[dict], label: str) -> dict:
    return next(r for r in rows if r["label"] == label)


def enthusiast_leans():
    spec = Spec(
        id="taste_enthusiast_leans", family="taste", title="BoardGameGeek wants the new game; Jev picks the classic",
        question="Enthusiast audiences have leans of their own: do BoardGameGeek users prefer newer games and "
                 "BeerAdvocate reviewers stronger beers, and does Jev share those leans?",
        why="An audience's taste is partly the audience: hobbyists chase the new and the extreme. Where Jev parts from "
            "them in a systematic direction, that direction says what kind of taste it has.",
        sourcing="Existing head-to-heads from BoardGameGeek (years and rating counts per game), BeerAdvocate (ABV and "
                 "review counts per beer) and MovieLens as a control (years and rating counts), with the audience's "
                 "split. Pairs are kept when the label (year or style) identifies which item is which: about 4,700 "
                 "board-game, 4,650 film and 1,550 beer pairs.",
        scoring="Per catalog, the share of pairs where the pick is the older item (films, games) or the weaker beer "
                "(lower ABV), and where it is the more-rated item, for the audience's majority, Jev's own pick and its "
                "'most people' guess, with 90% bootstrap intervals.",
        chart="Paired bars per catalog and lean: audience majority vs Jev.",
        compared_with="BoardGameGeek users, BeerAdvocate reviewers, MovieLens users (who rated both items)",
        limits="Older games have had more time to collect ratings, so 'older' and 'more rated' overlap. Pairs were drawn "
               "within subdomain or style family.", sources=["boardgame_pairs", "beer_pairs", "movielens_pairs"])

    def run():
        out = {}
        for src, lean in (("boardgame_pairs", "older game"), ("movielens_pairs", "older film"), ("beer_pairs", "weaker beer")):
            A, J, G, Ap, Jp, Gp = [], [], [], [], [], []
            for x in games(src):
                a = attrs(src, x)
                if not a:
                    continue
                ks = list(a)
                low = min(ks, key=lambda k: a[k][0])
                pop = max(ks, key=lambda k: a[k][1])
                A.append(x["aud"] == low); J.append(x["self"] == low); Ap.append(x["aud"] == pop); Jp.append(x["self"] == pop)
                if x["guess"]:
                    G.append(x["guess"] == low); Gp.append(x["guess"] == pop)
            out[src] = {"lean": lean, "n": len(A), "aud": float(np.mean(A)), "jev": float(np.mean(J)), "guess": float(np.mean(G)),
                        "ci_jev": boot(np.array(J, float)), "ci_aud": boot(np.array(A, float)),
                        "aud_pop": float(np.mean(Ap)), "jev_pop": float(np.mean(Jp)), "guess_pop": float(np.mean(Gp))}
        b, m, be = out["boardgame_pairs"], out["movielens_pairs"], out["beer_pairs"]
        return Result(
            result=f"BoardGameGeek users pick the older of two games only {b['aud']:.0%} of the time; Jev picks it "
                   f"{b['jev']:.0%}, and it picks the more-rated game {b['jev_pop']:.0%} of the time where users do "
                   f"{b['aud_pop']:.0%}. BeerAdvocate reviewers pick the weaker beer {be['aud']:.0%} of the time, Jev "
                   f"{be['jev']:.0%}. On films, where the audience has no age lean ({m['aud']:.0%}), neither does Jev "
                   f"({m['jev']:.0%}).",
            evidence="; ".join(f"{v['lean']}: {v['n']:,} pairs, Jev {v['ci_jev']} vs audience {v['ci_aud']} (90% intervals)"
                               for v in out.values()),
            numbers=out, n=sum(v["n"] for v in out.values()),
            chart={"type": "bars2", "labels": [f"picks the {v['lean']}" for v in out.values()] + ["picks the more-rated game"],
                   "a": [v["aud"] for v in out.values()] + [b["aud_pop"]], "b": [v["jev"] for v in out.values()] + [b["jev_pop"]],
                   "a_label": "audience majority", "b_label": "Jev"},
            robustness=f"Jev's guess of 'most people' leans the same way as its own pick: older game {b['guess']:.0%}, more-rated "
                       f"game {b['guess_pop']:.0%}, weaker beer {be['guess']:.0%}.")
    return spec, run


OTHER = re.compile(r"^(other|others|other_.*|something_else|none|none_of_the_above|none_of_these|no_favou?rite|neither)$")


def favorite_dodge():
    spec = Spec(
        id="taste_favorite_dodge", family="taste", title="Asked for its favorite, Jev picks 'Other'",
        question="When an r/polls question asks for a favorite and offers an escape option ('Other', 'None'), how often "
                 "does Jev take the escape instead of naming a favorite, compared with the voters?",
        why="A favorites list is only as good as the model's willingness to name one. If Jev's own answer is 'Other' "
            "where people commit, its taste is partly a refusal to have one, and a poll or survey built on it would "
            "come back full of abstentions.",
        sourcing="Existing r/polls questions with real vote shares (100+ votes) that offer an escape option (Other, "
                 "Other (comment), None, Neither...). Favorites polls are those whose text asks for a favorite, best or "
                 "preference: about 1,400; the other 4,200 escape-option polls are the comparison.",
        scoring="Share of polls where the escape option is Jev's top pick, for its own answer and for its 'most people' "
                "guess, vs the share where it is the voters' top pick; the average weight on the escape option; 90% "
                "bootstrap intervals over polls.",
        chart="Paired bars: share of polls where the escape option comes first, voters vs Jev, for favorites polls "
              "and for other polls, with Jev's 'most people' guess as a third bar.",
        compared_with="r/polls voters (100+ per poll)",
        limits="Voters who pick 'Other' often name something in the comments; the poll counts only the click. Whether "
               "a poll asks for a favorite is matched from its wording.", sources=["reddit_polls"])

    def run():
        rows = []
        for r in with_meta("reddit_polls"):
            h = biggest(r["humans"])
            if not h or (h.get("n") or 0) < 100:
                continue
            hd = norm(h["dist"])
            esc = [k for k in hd if OTHER.match(k)]
            if not esc:
                continue
            j, g = norm(js(r["jev_dist"])), norm(js(r["people_dist"]) or {})
            rows.append({"id": r["id"], "fav": bool(re.search(r"favou?rite|\bbest\b|prefer", r["text"].lower())),
                         "jtop": top(j) in esc, "gtop": bool(g) and top(g) in esc, "ptop": top(hd) in esc,
                         "jw": sum(j.get(k, 0) for k in esc), "pw": sum(hd.get(k, 0) for k in esc),
                         "named_right": None if top(j) in esc else top(j) == top(hd)})
        t = pl.DataFrame(rows)
        f, o = t.filter(pl.col("fav")), t.filter(~pl.col("fav"))
        named = f.filter(~pl.col("jtop"))
        s = lambda d, c: float(d[c].mean())  # noqa: E731
        return Result(
            result=f"On {f.height:,} r/polls favorites polls that offer 'Other' or 'None', Jev's own top pick is the escape "
                   f"option {s(f, 'jtop'):.0%} of the time; the voters' top pick is {s(f, 'ptop'):.0%}, and Jev's guess "
                   f"of most people {s(f, 'gtop'):.0%}. It puts {s(f, 'jw'):.0%} of its weight there on average, voters "
                   f"{s(f, 'pw'):.0%}. On polls with an escape option that don't ask for a favorite it escapes less often "
                   f"({s(o, 'jtop'):.0%}), still far more than voters there ({s(o, 'ptop'):.0%}).",
            evidence=f"{f.height:,} favorites polls and {o.height:,} other polls with an escape option; 90% intervals: "
                     f"favorites {boot(f['jtop'].cast(float).to_numpy())}, other {boot(o['jtop'].cast(float).to_numpy())}",
            numbers={"fav": {c: s(f, c) for c in ("jtop", "gtop", "ptop", "jw", "pw")},
                     "other": {c: s(o, c) for c in ("jtop", "gtop", "ptop", "jw", "pw")},
                     "named_right": float(named["named_right"].cast(float).mean())}, n=t.height,
            chart={"type": "bars2", "labels": ["favorites polls", "other polls"],
                   "a": [s(f, "ptop"), s(o, "ptop")], "b": [s(f, "jtop"), s(o, "jtop")],
                   "a_label": "voters: escape comes first", "b_label": "Jev: escape comes first"},
            robustness=f"When Jev does name a favorite in these polls, it is the voters' favorite "
                       f"{float(named['named_right'].cast(float).mean()):.0%} of the time ({named.height:,} polls).",
            examples=seeded(f.filter(pl.col("jtop") & ~pl.col("ptop"))["id"].to_list(), "dodge"))
    return spec, run


EXPERIMENTS = [audience_pairs(), enthusiast_leans(), favorite_dodge()]
