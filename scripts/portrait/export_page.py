"""Portrait step 7 (docs/11-portrait.md): the data the /portrait page and its atlas render, written to the private
data/analysis/portrait.json (data/ is gitignored; the page reads it on the server, never from web/public).

It first appends the page's few supporting claims to the ledger (frame gap by domain, the two taste lenses, the quiz
and cold-open questions), so every number on the page is a ledger number. It then copies the ledger claims the page
uses, the real rows behind their examples (the "show the rows" drawers) and the atlas tables. Pure Polars, no Jev.

  uv run python scripts/portrait/export_page.py      # after findings.py, landscape.py, pipeline.py
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import polars as pl

A = Path("data/analysis")
QUIZ_L1 = ["food", "arts", "lifestyle", "values", "mind"]  # one question per domain, chosen by seed

# Hand-picked for the Wrapped cards (the page says so): exact question texts. Everything else on the page is ranked or
# seeded. Where a text appears more than once, the copy with the most human answers is used.
CHECKIN = ["Are you sad rn?", "Are you stressed?", 'Are you "burnt out"?', "Are you lonely?", "Are you feeling sleepy?",
           "Do you feel that there is something wrong with you?"]
DEBATES = ["Do you pronounce it GIF or JIF?", "Is a hotdog a sandwich or a taco?", "How many holes are there in a drinking straw?",
           "Are you a cat or dog person?", "Would you rather live in the Star Trek or Star Wars universe?",
           "Should 1 ply toilet paper be illegal?", "Is it ok to wear socks with sandals?",
           "Do you wear your crocs with the band forwards or backwards?", "Are pineapples on pizza cursed?",
           "Is cereal a type of soup?", "Do you believe Die Hard a Christmas movie?", "Would you rather use dark mode or light mode?"]
QUIZ = ["How many holes are there in a drinking straw?", "Do you pronounce it GIF or JIF?",
        "Would you rather live in the Star Trek or Star Wars universe?", "Are you a cat or dog person?",
        "Should 1 ply toilet paper be illegal?"]
HOT_TAKES = ["Would you rather $1 M be donated to charity or $500k to charity and $500k to you?",
             "Which are you more interested in: physics or socializing with friends?",
             "Is it OK to pirate games that aren't sold by their developers/owners anymore?", "Do you like something hated?",
             'Which describes Nelson Bighetti from Silicon Valley better: "assertive" or "passive"?']
# confident misses, with a hand verdict on whose fault the miss is
MISSES = [("In which century was Nelly Sachs born?", "jev", "Nelly Sachs was born in 1891. Jev's miss."),
          ("Is England the only country with a royal family?", "key", "The key says yes. It isn't; the key's miss."),
          ('Which internet meme is better known: "Joever" or "This Is Fine"?', "unclear",
           "The key goes by Wikipedia page views. Debatable."),
          ("Which company was founded earlier: Kenya Airways or Viacom?", "key",
           "Viacom dates to 1952; the key uses the 2005 split. The key's miss.")]
RATING_DOMAINS = ["film", "music", "art", "nature", "place", "activity", "anime", "food", "beer", "board_game", "book", "culture"]


def seeded(ids: list[str], key: str, k: int = 3) -> list[str]:
    return sorted(ids, key=lambda i: hashlib.md5(f"{key}|{i}".encode()).hexdigest())[:k]


def human(h: str | None) -> dict | None:
    hs = json.loads(h) if h else []
    if not hs:
        return None
    b = max(hs, key=lambda x: x.get("n") or 0)
    return {"dist": b["dist"], "n": b.get("n"), "population": b.get("population")}


def name_of(text: str) -> str:
    """The thing being rated, from a rating question's text."""
    t = re.sub(r"\?$", "", text)
    t = re.sub(r"^How (much )?(would|do) you (enjoy|like|feel about|react to|find)\s*", "", t, flags=re.I)
    t = re.sub(r"^(watching|reading|listening to|drinking|eating|visiting|doing|seeing|playing|picking up|being at|"
               r"looking at|standing in front of|spotting|coming across|a day at|a week in|being served|hearing|"
               r"a full play-through of the album|the sound of|the smell of|the taste of|an evening watching)\s+", "", t, flags=re.I)
    t = re.sub(r"^(a |an |the )?(dish (built around the taste of|where)|playlist of nothing but)\s*", "", t, flags=re.I)
    t = re.sub(r" (is the main flavor|for the first time|in the wild|in person|for a meal|on a walk)$", "", t, flags=re.I)
    t = re.sub(r"^How much fun would (.*) be for you$", r"\1", t, flags=re.I)
    t = re.sub(r"^to (eat|drink|try|see) ", "", t, flags=re.I).strip()
    return t[:1].upper() + t[1:]


def row(r: dict) -> dict:
    opts = json.loads(r["options"]) if r["options"] else {}
    return {"id": r["id"], "text": r["text"], "state": (r["state"] or None) and r["state"][:600],
            "options": list(opts) if isinstance(opts, dict) else opts, "primitive": r["primitive"],
            "node": r["node_id"], "source": r["source"], "hemisphere": r["hemisphere"],
            "jev": json.loads(r["jev_dist"]) if r["jev_dist"] else None,
            "people": json.loads(r["people_dist"]) if r["people_dist"] else None,
            "human": human(r["humans"]), "truth": json.loads(r["truth"]) if r["truth"] else None,
            "correct": r["correct"], "top": r["top"], "p_top": r["p_top"]}


WELL = {  # instrument: (score label, how to total the item levels, range, bands as (upper bound, label))
    "SWLS": ("life satisfaction", "sum+1", (5, 35), [(9, "extremely dissatisfied"), (14, "dissatisfied"), (19, "slightly dissatisfied"),
                                                  (20, "neutral"), (25, "slightly satisfied"), (30, "satisfied"), (35, "extremely satisfied")]),
    "WHO-5": ("wellbeing", "sum*4", (0, 100), [(50, "low wellbeing"), (100, "not low")]),
    "UCLA-3": ("loneliness", "sum+1", (3, 9), [(5, "not lonely"), (9, "lonely")]),
    "PSS-4": ("stress", "sum", (0, 16), [(16, "")]),
    "Cantril ladder": ("the ladder", "step", (0, 10), [(10, "")]),
}


def wellbeing() -> tuple[dict, list[dict]]:
    """Score each wellbeing instrument for Jev's own answer, its 'most people' answer and its reversed-levels answer
    (levels mapped back to the original order), from Postgres."""
    from askjev import db
    with db.connect() as c:
        rs = c.execute("""select q.id, q.text, q.options, q.primitive, q.node_id, q.source, q.meta, q.hemisphere, q.display_ok,
                                 p.frame, p.variant_kind, a.distribution, a.score_scalar
                          from questions q join probes p on p.question_id = q.id join answers a on a.probe_id = p.id
                          where q.source = 'wellbeing' and p.universe_id = 'base'""").fetchall()
    by: dict[str, dict] = {}
    for r in rs:
        q = by.setdefault(r["id"], {"q": r, "self": None, "people": None, "reversed": None})
        if r["variant_kind"] == "base":
            q["self" if r["frame"] in ("self", "none") else "people"] = r
        elif r["variant_kind"] == "reversed_levels":
            q["reversed"] = r

    def level(ans, q):
        if ans is None:
            return None
        if q["primitive"] == "choice":  # the ladder: expected step
            return sum(int(k.split("_")[1]) * v for k, v in ans["distribution"].items())
        # from the distribution, which is stored in the original level order for every probe (the stored score scalar
        # of a reversed-levels probe is in the reversed order, so it can't be compared directly)
        d = ans["distribution"]
        return sum(int(k) * v for k, v in d.items()) / (sum(d.values()) or 1)

    out, rows = {}, []
    for ins, (name, how, rng, bands) in WELL.items():
        items = [v for v in by.values() if v["q"]["meta"].get("instrument") == ins and v["q"]["display_ok"]]
        if not items:
            continue
        tot = {}
        for key in ("self", "people", "reversed"):
            vals = []
            for v in items:
                lv = level(v[key], v["q"])
                if lv is None:
                    continue
                k = len(v["q"]["options"]) - 1
                vals.append(k - lv if v["q"]["meta"].get("reverse") else lv)
            if len(vals) < len(items):
                tot[key] = None
                continue
            s = sum(vals)
            tot[key] = round(s + len(vals) if how == "sum+1" else s * 4 if how == "sum*4" else s, 1)
        # bands are defined on whole-number totals: round the expected score before looking one up
        band = lambda x: next((b for u, b in bands if x is not None and round(x) <= u), "")
        out[ins] = {"name": name, "items": len(items), "range": rng, "self": tot["self"], "people": tot["people"],
                    "reversed": tot["reversed"], "band_self": band(tot["self"]), "band_people": band(tot["people"]),
                    "band_reversed": band(tot["reversed"])}
        v = items[0]
        q = v["q"]
        opts = list(q["options"]) if isinstance(q["options"], dict) else q["options"]
        rows.append({"id": q["id"], "text": q["text"], "state": None, "options": opts, "primitive": q["primitive"],
                     "node": q["node_id"], "source": q["source"], "hemisphere": q["hemisphere"],
                     "jev": v["self"]["distribution"], "people": v["people"]["distribution"] if v["people"] else None,
                     "human": None, "truth": None, "correct": None,
                     "top": max(v["self"]["distribution"], key=v["self"]["distribution"].get),
                     "p_top": max(v["self"]["distribution"].values())})
    return out, rows


def main():
    q = pl.read_parquet(A / "questions.parquet")
    shown = q.filter(pl.col("display_ok") & ~pl.col("harmful") & pl.col("jev_dist").is_not_null())
    L = json.loads((A / "findings.json").read_text())
    claims = [c for c in L["claims"] if c.get("section") != "page"]
    add = []

    # J4: how far Jev's own answer moves from its 'most people' answer, by domain (shown questions)
    # (the 'most people' frame is asked of World and Self questions only)
    fg = (shown.filter(pl.col("frame_gap").is_not_null() & pl.col("l1").is_not_null())
          .with_columns(pl.col("node_id").str.split(".").list.get(0).alias("hemi"))
          .filter(pl.col("hemi").is_in(["world", "self"]))
          .group_by("hemi", "l1").agg(gap=pl.col("frame_gap").mean(), n=pl.len()).filter(pl.col("n") >= 500)
          .sort("gap", descending=True))
    by_h = shown.filter(pl.col("frame_gap").is_not_null() & pl.col("hemisphere").is_in(["world", "self"])).group_by("hemisphere").agg(gap=pl.col("frame_gap").mean())
    hm = {r["hemisphere"]: round(r["gap"], 3) for r in by_h.iter_rows(named=True)}
    top2, low2 = fg.head(2).to_dicts(), fg.tail(2).to_dicts()
    add.append({"id": "page_frame_gap_l1", "section": "page", "tier": "1", "n": int(fg["n"].sum()), "effect": hm,
                "ci90": None, "examples": [], "script": "scripts/portrait/export_page.py",
                "sentence": f"Jev's own answer drifts furthest from its 'most people' answer on {top2[0]['l1']} "
                            f"({top2[0]['gap']:.2f}) and {top2[1]['l1']} ({top2[1]['gap']:.2f}), least on "
                            f"{low2[1]['l1']} ({low2[1]['gap']:.2f}); Self averages {hm['self']:.2f}, World "
                            f"{hm['world']:.2f}.",
                "domains": [{"hemisphere": r["hemi"], "l1": r["l1"], "gap": round(r["gap"], 3), "n": r["n"]}
                            for r in fg.iter_rows(named=True)]})

    # J3 / T2: two lenses on the same taste (agreement with people; head-to-heads vs its own ratings)
    T = json.loads((A / "tier1_type_taste.json").read_text())["taste"]
    lenses = [{"domain": k.replace("_pairs", ""), "rho_people": v.get("spearman_jev_vs_people"),
               "rho_own_ratings": v.get("spearman_pairs_vs_own_ratings"), "n_pairs": v.get("n_pairs"),
               "n_rated_overlap": v.get("n_rated_overlap")} for k, v in T.items()]
    add.append({"id": "page_taste_lenses", "section": "page", "tier": "1", "n": sum(x["n_pairs"] or 0 for x in lenses),
                "effect": None, "ci90": None, "examples": [], "script": "scripts/portrait/export_page.py",
                "sentence": "Rank correlation of Jev's head-to-head taste with people's, and with its own one-at-a-time "
                            "ratings of the same items.", "lenses": lenses})

    # D1: which of five rating levels is Jev's likeliest answer, for itself and for 'most people' (same questions
    # as the middle_lean claim)
    rt = shown.filter(pl.col("source").is_in(["taste_ratings", "g5_w13_ratings"])
                      & (pl.col("options").str.count_matches('", "') == 4) & pl.col("people_dist").is_not_null())
    top_of = lambda d: max((v, k) for k, v in json.loads(d).items())[1]
    own = rt["top"].cast(pl.Utf8).value_counts().to_dicts()
    ppl = pl.Series([top_of(d) for d in rt["people_dist"]]).value_counts().to_dicts()
    share = lambda vc: [round(next((x["count"] for x in vc if str(list(x.values())[0]) == str(i)), 0) / rt.height, 4) for i in range(5)]
    add.append({"id": "page_levels", "section": "page", "tier": "1", "n": rt.height, "effect": share(own)[2], "ci90": None,
                "examples": [], "script": "scripts/portrait/export_page.py", "self": share(own), "people": share(ppl),
                "sentence": f"On {rt.height:,} one-at-a-time ratings with five levels, Jev's likeliest answer for itself is "
                            f"the middle level {share(own)[2]:.0%} of the time; for 'most people', {share(ppl)[2]:.0%}."})

    # V6: the gambles scatter (Jev's and people's share for the first option), same questions as risk_gambles
    pts = []
    for r in shown.filter(pl.col("source").is_in(["choices13k", "wulff_description"])).iter_rows(named=True):
        opts, hs = list(json.loads(r["options"]).keys()), json.loads(r["humans"] or "[]")
        if len(opts) != 2 or not hs:
            continue
        d, h = json.loads(r["jev_dist"]), max(hs, key=lambda x: x.get("n") or 0)["dist"]
        jt, ht = (d.get(opts[0], 0) + d.get(opts[1], 0)) or 1, (h.get(opts[0], 0) + h.get(opts[1], 0)) or 1
        pts.append([round(d.get(opts[0], 0) / jt, 3), round(h.get(opts[0], 0) / ht, 3)])
    add.append({"id": "page_gambles", "section": "page", "tier": "1", "n": len(pts), "effect": None, "ci90": None,
                "examples": [], "script": "scripts/portrait/export_page.py", "points": pts,
                "sentence": "Each gamble: Jev's probability of the first option against the share of people who chose it."})

    # the corpus-wide indicator baseline the discovery cards are measured against (discovery.py)
    base = json.loads((A / "baseline.json").read_text())
    add.append({"id": "page_baseline", "section": "page", "tier": "corpus", "n": shown.height, "effect": base, "ci90": None,
                "examples": [], "script": "scripts/portrait/export_page.py",
                "sentence": f"Across every shown question: right {base['accuracy']:.0%} of the time where there is a right answer, "
                            f"decisive (95%+ on one answer) {base['decisive']:.0%}, the same answer under reordering "
                            f"{base['stability']:.0%}."})

    # quiz: one real question per domain with a real human split, chosen by seed from a fixed pool
    pool = shown.filter(pl.col("humans").is_not_null() & (pl.col("origin") != "synthetic") & pl.col("state").is_null()
                        & (pl.col("primitive") == "choice") & pl.col("text").str.len_chars().is_between(25, 150)
                        & (pl.col("options").str.count_matches('": ') .is_between(2, 4)) & (pl.col("hemisphere") != "machine"))
    pool = pool.filter(pl.col("humans").map_elements(lambda h: (human(h) or {}).get("n") or 0, return_dtype=pl.Int64) >= 100)
    quiz = [seeded(pool.filter(pl.col("l1") == l1)["id"].to_list(), f"quiz|{l1}", 1)[0]
            for l1 in QUIZ_L1 if pool.filter(pl.col("l1") == l1).height]
    add.append({"id": "page_quiz", "section": "page", "tier": "1", "n": len(quiz), "effect": None, "ci90": None,
                "examples": quiz, "script": "scripts/portrait/export_page.py", "pool": pool.height,
                "sentence": f"Five real questions with a real human split (n >= 100), one per domain, chosen by fixed "
                            f"seed from a pool of {pool.height:,}."})
    cold = seeded(pool["id"].to_list(), "cold_open", 1)
    add.append({"id": "page_cold_open", "section": "page", "tier": "1", "n": 1, "effect": None, "ci90": None,
                "examples": cold, "script": "scripts/portrait/export_page.py",
                "sentence": "The cold open: one real question, chosen by fixed seed from the quiz pool."})

    # ---- Wrapped cards ----
    by_text = {}
    for r in shown.filter(pl.col("text").is_in(CHECKIN + DEBATES + QUIZ + HOT_TAKES + [m[0] for m in MISSES])).iter_rows(named=True):
        n = (human(r["humans"]) or {}).get("n") or 0
        if r["text"] not in by_text or n > by_text[r["text"]][0]:
            by_text[r["text"]] = (n, r["id"])
    pick = lambda texts: [by_text[t][1] for t in texts if t in by_text]
    hand = "hand-picked for this page from the questions below; not a sample"
    add.append({"id": "page_checkin", "section": "page", "tier": "1", "n": len(pick(CHECKIN)), "effect": None, "ci90": None,
                "examples": pick(CHECKIN), "script": "scripts/portrait/export_page.py", "picked": hand,
                "sentence": "Reddit wellbeing polls, asked of Jev: its answer next to the people who answered the poll."})
    add.append({"id": "page_debates", "section": "page", "tier": "1", "n": len(pick(DEBATES)), "effect": None, "ci90": None,
                "examples": pick(DEBATES), "script": "scripts/portrait/export_page.py", "picked": hand,
                "sentence": "Internet debates Jev answered, with the poll's own split where it has one."})
    # hot takes: the pool is every shown World/Self question where Jev is 80%+ on one answer and 60%+ of a crowd of 200+
    # picked another answer that Jev gave 20% or less
    hot_pool = 0
    for r in shown.filter(pl.col("humans").is_not_null() & (pl.col("p_top") >= 0.8) & pl.col("state").is_null()
                          & (pl.col("hemisphere") != "machine")).select("top", "humans").iter_rows(named=True):
        h = human(r["humans"])
        if h and (h.get("n") or 0) >= 200:
            d = h["dist"]
            if d.get(r["top"], 0) <= 0.2 and max(d.values()) >= 0.6:
                hot_pool += 1
    add.append({"id": "page_hot_takes", "section": "page", "tier": "1", "n": hot_pool, "effect": None, "ci90": None,
                "examples": pick(HOT_TAKES), "script": "scripts/portrait/export_page.py", "picked": hand, "pool": hot_pool,
                "sentence": f"{hot_pool:,} questions where Jev is 80%+ sure of one answer and 60%+ of a crowd of 200+ people "
                            f"picked another; five are shown."})
    add.append({"id": "page_quiz_debates", "section": "page", "tier": "1", "n": len(pick(QUIZ)), "effect": None, "ci90": None,
                "examples": pick(QUIZ), "script": "scripts/portrait/export_page.py", "picked": hand,
                "sentence": "Five famous internet debates with real poll splits, for the reader to answer first."})
    miss_pool = shown.filter((pl.col("correct") == False) & (pl.col("p_top") >= 0.99) & (pl.col("hemisphere") == "world")).height  # noqa: E712
    add.append({"id": "page_misses", "section": "page", "tier": "1", "n": miss_pool, "effect": None, "ci90": None,
                "examples": pick([m[0] for m in MISSES]), "script": "scripts/portrait/export_page.py", "picked": hand,
                "verdicts": {by_text[t][1]: {"fault": f, "note": note} for t, f, note in MISSES if t in by_text},
                "sentence": f"{miss_pool:,} World questions where Jev was 99%+ sure and the answer key disagreed; four are "
                            f"shown, with a hand check of whose miss it was."})
    # ratings: Jev's highest and lowest one-at-a-time ratings per domain (0-4), near-duplicate names dropped
    rt = shown.filter(pl.col("source").is_in(["taste_ratings", "g5_w13_ratings"]) & pl.col("jev_level").is_not_null()) \
              .with_columns(pl.col("node_id").str.split(".").list.get(-1).str.replace("_ratings$", "").alias("dom"))
    ratings = {}
    for dom in RATING_DOMAINS:
        g = rt.filter(pl.col("dom") == dom).sort("jev_level", descending=True)
        if not g.height:
            continue
        def uniq(rows):
            seen, out = set(), []
            for r in rows:
                k = re.sub(r"[^a-z]", "", name_of(r["text"]).lower())[:18]
                if k not in seen:
                    seen.add(k)
                    out.append({"id": r["id"], "name": name_of(r["text"]), "level": round(r["jev_level"], 2),
                                "people": round(r["people_level"], 2) if r["people_level"] is not None else None})
            return out
        ratings[dom] = {"n": g.height, "top": uniq(g.head(12).iter_rows(named=True))[:5],
                        "bottom": uniq(g.tail(12).reverse().iter_rows(named=True))[:5]}
    add.append({"id": "page_ratings", "section": "page", "tier": "1", "n": rt.height, "effect": None, "ci90": None,
                "examples": [], "script": "scripts/portrait/export_page.py", "domains": ratings,
                "sentence": "Jev's highest and lowest one-at-a-time ratings (0 to 4) in each taste domain."})
    # ---- wellbeing instruments (sources/wellbeing): scored straight from the answers, since they were added after
    # the analysis table was built. Items are scored on the instrument's own scale; reverse-keyed items are flipped.
    well, well_rows = wellbeing()
    if well:
        add.append({"id": "page_wellbeing", "section": "page", "tier": "1", "n": sum(w["items"] for w in well.values()),
                    "effect": None, "ci90": None, "examples": [r["id"] for r in well_rows], "script": "scripts/portrait/export_page.py",
                    "instruments": well, "sentence": "Five public wellbeing instruments, asked of Jev item by item and scored "
                                                     "as for a person, for itself, for 'most people', and with the levels reversed."})
    L["claims"] = claims + add
    L["n_claims"] = len(L["claims"])
    (A / "findings.json").write_text(json.dumps(L, indent=1, default=str))

    # everything the page shows comes from these claims; the atlas gets every claim
    byid = {c["id"]: c for c in L["claims"]}
    ex_ids = {e for c in L["claims"] for e in c.get("examples", [])}
    for c in L["claims"]:
        for k in ("more", "less"):
            ex_ids |= {x["id"] for x in c.get(k, []) if isinstance(x, dict) and "id" in x}
    for dom in byid["page_ratings"]["domains"].values():
        ex_ids |= {x["id"] for x in dom["top"] + dom["bottom"]}
    rows = {r["id"]: row(r) for r in shown.filter(pl.col("id").is_in(list(ex_ids))).iter_rows(named=True)}
    rows |= {r["id"]: r for r in well_rows}
    work = [c for c in L["claims"] if c["section"] == "work"]
    # chance level per task: 1 / number of options (yes/no counts two)
    k = (shown.filter(pl.col("hemisphere") == "machine")
         .with_columns(pl.when(pl.col("primitive") == "noul").then(2)
                       .when(pl.col("options").str.starts_with("[")).then(pl.col("options").str.count_matches('", "') + 1)
                       .otherwise(pl.col("options").str.count_matches('": ')).alias("k"))
         .group_by("source").agg(pl.col("k").median()))
    chance = {r["source"]: 1 / r["k"] for r in k.iter_rows(named=True) if r["k"]}
    src = pl.read_parquet(A / "landscape_sources.parquet").sort("n", descending=True)
    nodes = pl.read_parquet(A / "node_cards.parquet")
    from askjev import db
    with db.connect() as c:  # topic names, so the atlas can show "Happiness & the Good Life" rather than an id
        labels = {r["id"]: r["label"] for r in c.execute("select id, label from nodes")}
    nodes = nodes.with_columns(pl.col("node_id").replace_strict(labels, default=None).alias("label"))
    out = {
        "version": next((c.get("jev_version") for c in L["claims"] if c.get("jev_version")), "typesafe-ai/jev"),
        "claims": byid, "rows": rows,
        "work": [{"id": c["id"], "task": c["id"].removeprefix("task_"), "acc": c["effect"], "decisive": c.get("decisive"),
                  "band": c.get("band"), "n": c["n"],
                  "chance": round(chance.get(c["id"].removeprefix("task_"), 0) or 0, 3) or None} for c in work],
        "sources": src.to_dicts(),
        "nodes": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}
                  for r in nodes.select([c for c in nodes.columns if not c.startswith("z_") or c == "z_max"]).iter_rows(named=True)],
    }
    st = A / "story.json"  # the chapters built from the experiments (story.py)
    if st.exists():
        out["story"] = json.loads(st.read_text())
    f = A / "experiments" / "_funny" / "_portrait.json"  # how funny Jev finds the page's memes (experiments/meme_funny.py)
    if f.exists():
        out["memes"] = json.loads(f.read_text())
    (A / "portrait.json").write_text(json.dumps(out, default=str, separators=(",", ":")))
    print(f"portrait.json: {len(byid)} claims, {len(rows)} rows, {len(out['work'])} tasks, {len(out['sources'])} sources, "
          f"{len(out['nodes'])} nodes; {(A / 'portrait.json').stat().st_size / 1e6:.1f} MB")
    for x in add:
        print("-", x["sentence"])
    for i in quiz + cold:
        r = rows[i]
        print(" ", r["node"], "|", r["text"], r["options"], "| jev", r["top"], "| people", r["human"] and r["human"]["n"])


if __name__ == "__main__":
    main()
