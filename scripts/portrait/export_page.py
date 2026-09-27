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
from pathlib import Path

import polars as pl

A = Path("data/analysis")
QUIZ_L1 = ["food", "arts", "lifestyle", "values", "mind"]  # one question per domain, chosen by seed


def seeded(ids: list[str], key: str, k: int = 3) -> list[str]:
    return sorted(ids, key=lambda i: hashlib.md5(f"{key}|{i}".encode()).hexdigest())[:k]


def human(h: str | None) -> dict | None:
    hs = json.loads(h) if h else []
    if not hs:
        return None
    b = max(hs, key=lambda x: x.get("n") or 0)
    return {"dist": b["dist"], "n": b.get("n"), "population": b.get("population")}


def row(r: dict) -> dict:
    opts = json.loads(r["options"]) if r["options"] else {}
    return {"id": r["id"], "text": r["text"], "state": (r["state"] or None) and r["state"][:600],
            "options": list(opts) if isinstance(opts, dict) else opts, "primitive": r["primitive"],
            "node": r["node_id"], "source": r["source"], "hemisphere": r["hemisphere"],
            "jev": json.loads(r["jev_dist"]) if r["jev_dist"] else None,
            "people": json.loads(r["people_dist"]) if r["people_dist"] else None,
            "human": human(r["humans"]), "truth": json.loads(r["truth"]) if r["truth"] else None,
            "correct": r["correct"], "top": r["top"], "p_top": r["p_top"]}


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

    L["claims"] = claims + add
    L["n_claims"] = len(L["claims"])
    (A / "findings.json").write_text(json.dumps(L, indent=1, default=str))

    # everything the page shows comes from these claims; the atlas gets every claim
    byid = {c["id"]: c for c in L["claims"]}
    ex_ids = {e for c in L["claims"] for e in c.get("examples", [])}
    for c in L["claims"]:
        for k in ("more", "less"):
            ex_ids |= {x["id"] for x in c.get(k, []) if isinstance(x, dict) and "id" in x}
    rows = {r["id"]: row(r) for r in shown.filter(pl.col("id").is_in(list(ex_ids))).iter_rows(named=True)}
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
