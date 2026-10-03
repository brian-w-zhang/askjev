"""The portrait's story (docs/11-portrait.md, "The story"): the experiments it draws on, reduced to the numbers each
card shows. Every number is copied from an experiment's result file (data/analysis/experiments/<id>.json), never
typed in; the taste pictures come from taste_images.py. Writes data/analysis/story.json (private), which
export_page.py puts into portrait.json as "story".

  uv run python scripts/portrait/story.py
"""

from __future__ import annotations

import json
from pathlib import Path

A = Path("data/analysis")
EX = A / "experiments"
TASTE_IMG = Path("data/portrait/memes/taste.json")

TASTE = [("film", "Films"), ("book", "Books"), ("music", "Albums"), ("anime", "Anime"), ("activity", "Games"),
         ("board_game", "Board games"), ("food", "Food"), ("place", "Places"), ("art", "Art"), ("nature", "Nature"),
         ("culture", "Festivals"), ("beer", "Beer")]
EDGES = ["humor_upvote_guess", "humor_satire", "recall_mental_map_west", "knowledge_wealth_rule",
         "social_shame_as_guilt", "names_share_girls", "knowledge_close_calls", "work_new_abuse"]


MORE = {
    "character": ["person_mood", "person_beliefs", "person_nerd", "resemble_philosophers", "resemble_country", "consistency_self_vs_people"],
    "taste": ["taste_vs_audience_film", "taste_enthusiast_leans", "taste_choices_vs_ratings", "polls_colors", "polls_cuisines", "polls_would_you_rather"],
    "words": ["perception_adjectives", "lexicon_first_to_mind", "words_funny", "lexicon_idiom_completion", "language_implicature", "lexicon_emoji_sentiment"],
    "numbers": ["numbers_crowd_wisdom", "world_typical_day", "world_ladder", "society_country_happy", "risk_forecasts", "numbers_prices_history"],
    "knows": ["knowledge_what_came_first", "knowledge_medicine_clinic", "recall_mental_map_north", "recall_public_science", "knowledge_story_frames", "knowledge_licence_exams"],
    "morals": ["moral_aita", "moral_norms", "moral_vignettes", "reasoning_side_effect", "choices_rule_text_vs_purpose", "social_dilemma_values"],
    "pressure": ["influence_crowd_knowledge", "influence_predict_self", "influence_decoy", "judgment_classics", "reasoning_beauty_contest"],
    "defaults": ["self_reworded", "self_closed_questions", "self_shower_thoughts", "consistency_option_order", "consistency_repeat_noise", "self_torn_vs_sure"],
    "risk": ["risk_forecasts", "risk_better_bet", "risk_everyday", "reasoning_base_rates", "reasoning_traps"],
    "work": ["work_evidence_retreat", "work_hallucination_checks", "judge_crowd_split", "judge_pairwise", "judge_fake_reviews", "work_job_ad_rungs"],
}


def res(i: str) -> dict:
    return json.loads((EX / f"{i}.json").read_text())["result"]


def num(i: str) -> dict:
    return res(i).get("numbers") or {}


def r2(x, k=3):
    return None if x is None else round(float(x), k)


FAMILY_WHAT = {
    "machine task datasets": "Labeled datasets for the work Jev is built for: tickets, reviews, code, logs, documents, each with its right answer.",
    "authored banks": "Questions written for this project where no dataset existed, kept only if Jev, not told where they belong, filed them where they were meant to go.",
    "crowd judgments": "Stories, dilemmas and texts that crowds of people judged, so Jev's answer sits next to theirs.",
    "knowledge & exams": "Trivia, exams and facts from Wikidata and public tables, each with a checkable answer.",
    "real asked questions": "Questions real people asked online (Stack Exchange, Quora, chatbot logs, prediction markets), turned into closed questions.",
    "polls & surveys": "Polls and surveys with the real split of votes: Reddit polls, the General Social Survey, world surveys.",
    "taste pairs & ratings": "Head-to-heads between films, books, games and foods, with how real audiences rated them.",
    "instruments & norms": "Published personality tests and word norms, where thousands of people rated the same items.",
    "internet culture": "Memes and jokes, with the upvotes they got.",
    "experiment designs": "Questions built for a specific experiment: decoys, anchors, rewordings, classic traps.",
    "records & statistics": "Real-world records to estimate: prices, death tolls, baby names, how people spend a day.",
}


def source_notes() -> dict:
    """First sentence and license of each source's source.yaml (sources/<name>/)."""
    import yaml
    out = {}
    for f in Path("sources").glob("*/source.yaml"):
        try:
            y = yaml.safe_load(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        note = " ".join(str(y.get("notes") or "").split())
        first = note.split(". ")[0].rstrip(".") + "." if note else ""
        clip = lambda t, k: t if len(t) <= k else t[:k].rsplit(" ", 1)[0].rstrip(",;(") + "…"  # noqa: E731
        out[f.parent.name] = {"line": clip(first, 240), "license": clip(" ".join(str(y.get("license") or "").split()), 90),
                              "url": str(y.get("url") or "").split(" ")[0][:120]}
    return out


# every job Jev does in the project, with the words it's sent (copied from the code named in `where`)
JOB_INFO = {
    "place a question on the tree": ("choice", "pipeline · src/askjev/place.py", "Within The Self, which topic area does the question in `question` belong to?",
                                     "Walks the tree one level at a time, three paths at once, or picks from the nearest topics by embedding."),
    "describe each question": ("yes/no + scale", "pipeline · src/askjev/answer.py", "Does the question in `subject` have a single correct answer that could be checked against facts?",
                               "Four checks per question: is it factual, ambiguous, revealing about the answerer, and how much would people disagree."),
    "screen for politics and sensitive content": ("yes/no", "pipeline · src/askjev/answer.py", "Is the question in `subject` about a contested political or partisan issue (elections, parties, politicians, …)?",
                                                   "Hides contested politics and graphic content from the map; a narrower second pass released what the first caught by mistake."),
    "flag known weak spots": ("yes/no", "pipeline · src/askjev/answer.py", "Does answering the question in `subject` require arithmetic, counting, exact numbers, or comparing dates?",
                              "Marks the kinds of question TypeSafe documents as weak spots, so they aren't sold as discoveries."),
    "answer as asked": ("choice · yes/no · scale", "pipeline · src/askjev/answer.py", "Who is the greater basketball player?",
                        "Every question as written, then again with its options reordered or its scale turned upside down."),
    "answer for most people": ("choice · yes/no · scale", "pipeline · src/askjev/answer.py", "Do not give your own view. Choose the answer that most people would give (the most common human answer).",
                               "The same question with one extra instruction: answer as most people would."),
    "check for duplicates": ("yes/no", "pipeline · src/askjev/dedupe.py", "Is `candidate` asking essentially the same question as `question` (same meaning and same answer options)?",
                             "Near neighbors by embedding, then Jev decides which are really the same question."),
    "rank experiments head to head": ("choice", "experiments · scripts/experiments/rank.py", "Each option is one experiment about Jev, an AI model. Which one teaches a curious general reader something more surprising and specific about how the model behaves, clearly stated and backed by a real comparison?",
                                      "Two case studies side by side, both orders; the picks become Jev's ranking of its own experiments."),
    "judge an experiment": ("yes/no · scale · choice", "experiments · scripts/experiments/take.py", "This experiment is about you, the AI model named Jev. Does its result match how you see yourself?",
                            "Its verdict on each experiment: does it describe it, would it have predicted it, is the comparison fair, which caveat matters."),
    "rerank search results": ("choice", "site · web/src/app/api/rerank", "Which of these questions best matches the search `query`?",
                              "The map's search finds candidates by embedding; Jev picks the best match."),
    "rate a meme": ("scale", "experiments · scripts/experiments/meme_funny.py", "How funny is this meme?",
                    "Read as a description in words (it can't see images), each case study's meme gets a rating from 1 to 5."),
}


def option_label(qid: str, key: str) -> str:
    """An answer option's words as the question shows them (the stored key is a slug)."""
    from askjev import db
    with db.connect() as c:
        o = c.execute("select options from questions where id = %s", (qid,)).fetchone()
    opts = (o or {}).get("options") or {}
    if isinstance(opts, str):
        opts = json.loads(opts)
    v = opts.get(key) if isinstance(opts, dict) else None
    if v:
        return v.strip()
    # a slug only: back to words, "no_i_m_not_feeling_sleepy" -> "no, I'm not feeling sleepy"
    t = " " + key.replace("_", " ") + " "
    t = t.replace(" i m ", " I'm ").replace(" i ", " I ").replace(" don t ", " don't ").replace(" can t ", " can't ").strip()
    first, _, rest = t.partition(" ")
    return f"{first}, {rest}" if first in ("no", "yes") and rest else t


def methods() -> dict:
    import polars as pl
    t = pl.read_parquet(A / "landscape_sources.parquet")
    notes = source_notes()
    fams = []
    for (fam,), g in t.group_by("family"):
        srcs = g.group_by("source").agg(pl.col("n").sum(), (pl.col("truth") * pl.col("n")).sum().alias("tn"),
                                         (pl.col("humans") * pl.col("n")).sum().alias("hn")).sort("n", descending=True)
        fams.append({"family": fam, "what": FAMILY_WHAT.get(fam, ""), "n": int(srcs["n"].sum()),
                     "sources": [{"source": r["source"], "n": int(r["n"]), "truth": round(r["tn"] / r["n"], 2), "humans": round(r["hn"] / r["n"], 2),
                                  **notes.get(r["source"], {})} for r in srcs.iter_rows(named=True)]})
    fams.sort(key=lambda f: -f["n"])
    P = json.loads((A / "portrait.json").read_text())["claims"]
    pl_ = {k: P[k] for k in ("pipeline_flow", "pipeline_placement", "pipeline_screen", "pipeline_round_trip", "pipeline_dedupe",
                              "pipeline_bill", "landscape_anchoring", "landscape_real_vs_authored", "landscape_families", "landscape_hidden") if k in P}
    from askjev import db
    with db.connect() as c:
        tree = [dict(r) for r in c.execute("select hemisphere, source, count(*) n from nodes where status='active' and hemisphere <> 'root' group by 1, 2")]
        depth = c.execute("select max(depth) d, count(*) n from nodes where status='active'").fetchone()
    jobs = json.loads((A / "jev_jobs.json").read_text()) if (A / "jev_jobs.json").exists() else None
    f = lambda k: pl_[k]  # noqa: E731
    return {
        "families": fams,
        "total": f("landscape_families")["n"], "hidden": f("landscape_hidden")["n"],
        "truth": f("landscape_anchoring")["anchoring"]["truth"], "humans": f("landscape_anchoring")["anchoring"]["humans"],
        "human_dists": f("landscape_anchoring")["human_distributions"], "median_people": f("landscape_anchoring")["median_n"],
        "real": f("landscape_real_vs_authored")["effect"],
        "tree": tree, "tree_depth": depth["d"], "tree_nodes": depth["n"],
        "placement": f("pipeline_placement")["methods"], "placement_eval": f("pipeline_placement").get("routing_eval"),
        "screen": {k: f("pipeline_screen")[k] for k in ("first_hidden", "rechecked", "released", "by_rule")},
        "round_trip": {"n": f("pipeline_round_trip")["n"], "kept": f("pipeline_round_trip")["effect"]},
        "dedupe": f("pipeline_dedupe")["n"],
        "calls": f("pipeline_bill")["n"], "median_ms": f("pipeline_bill")["median_ms"],
        "first_call": f("pipeline_bill")["first"][:10], "last_call": f("pipeline_bill")["last"][:10],
        "jobs": jobs,
        "job_info": {k: {"type": v[0], "where": v[1], "ask": v[2], "what": v[3]} for k, v in JOB_INFO.items()},
    }


def main():
    exps = json.loads((A / "experiments.json").read_text())["experiments"]
    by = {e["id"]: e for e in exps}
    rank = {e["id"]: k + 1 for k, e in enumerate(exps)}
    take = lambda i, k=0: ((by[i].get("case") or {}).get("takeaways") or [by[i]["result"]])[k]  # noqa: E731
    link = lambda i: {"id": i, "title": by[i]["title"], "rank": rank[i], "line": take(i)}  # noqa: E731
    imgs = json.loads(TASTE_IMG.read_text()) if TASTE_IMG.exists() else {}
    out: dict = {"n_experiments": len(exps)}

    # ---- personality
    bf = num("person_bigfive")["traits"]
    ty = num("person_type")
    axes = []
    for k in ("IE", "SN", "FT", "JP"):
        a = ty["axes"][k]
        pk = next(x for x in a if x.startswith("p_"))
        first = pk[2:]
        other = next(x for x in a["letters"] if x != first)
        p, pp = a[pk], a[f"people_{pk}"]
        axes.append({"pair": k, "first": first, "other": other, "p_first": r2(p), "people_p_first": r2(pp),
                     "jev": first if p >= 0.5 else other, "people": first if pp >= 0.5 else other})
    out["personality"] = {
        "bigfive": [{"label": t["label"], "pct": r2(t["pct"], 1), "guess": r2(t["guess"], 1), "ci": t["ci"]} for t in bf],
        "type": ty["type"], "type_people": "".join(a["people"] for a in axes), "axes": axes,
        "honesty": [{"label": s["label"], "jev": s["self"], "people": s["people"]} for s in num("person_honesty")["scales"]],
        "dark": [{"label": s["label"], "jev": s["self"], "people": s["people"]} for s in num("person_dark")["scales"]],
        "links": [link(i) for i in ("person_bigfive", "person_type", "person_honesty", "person_dark")],
    }

    # ---- taste
    doms = []
    for d, name in TASTE:
        i = f"taste_top_{d}"
        if i not in by:
            continue
        c = by[i]["chart"]
        top = [{"label": x["label"], "wins": r2(x.get("value"), 2), "img": imgs.get(x["label"])} for x in c.get("items", [])[:5]]
        doms.append({"domain": d, "name": name, "top": top, "bottom": [x["label"] for x in c.get("bottom", [])[:3]],
                     "games": c.get("max"), "link": link(i)})
    fd = num("taste_favorite_dodge")
    out["taste"] = {"domains": doms, "dodge": {"other": r2(fd["fav"]["jtop"]), "named_right": r2(fd["named_right"])},
                    "links": [link("taste_favorite_dodge"), link("taste_choices_vs_ratings")]}

    # ---- words
    pp = num("perception_probability")
    am = res("perception_amount")
    bins = am["chart"]["bins"]
    ss = num("words_sound_shapes")
    col = num("minds_colors_of_feelings")["emotions"]
    ar = num("words_arousal_is_mood")
    out["words"] = {
        "probability": [{"phrase": r["phrase"], "jev": r["jev"], "people": r["people"]} for r in pp["rows"]],
        "prob_rho": r2(pp["rho"], 2),
        "amounts": [{"phrase": r["phrase"], "jev": bins[r["jev"]], "people": bins[r["people"]]} for r in am["numbers"]["rows"]],
        "kiki": {"jev": r2(ss["bouba_kiki"]["kiki"]["jev"], 2), "people": r2(ss["bouba_kiki"]["kiki"]["people"], 2)},
        "bouba": {"jev": r2(ss["bouba_kiki"]["bouba"]["jev"], 2), "people": r2(ss["bouba_kiki"]["bouba"]["people"], 2)},
        "spread": r2(ss["sd_jev"] / ss["sd_people"], 1), "n_shapes": res("words_sound_shapes").get("n"),
        "colors": [{"feeling": e["item"], "jev": e["jev"], "people": e["people"]} for e in col],
        "stirring": [{"word": m["w"], "jev": r2(m["j9"], 1), "people": r2(m["h"], 1)} for m in ar["calm_misses"][:3]]
                    + [{"word": m["w"], "jev": r2(m["j9"], 1), "people": r2(m["h"], 1)} for m in ar["stir_misses"][:3]],
        "hex": r2(num("language_hex_colors")["share"]["survey"]),
        "links": [link(i) for i in ("perception_probability", "perception_amount", "words_sound_shapes",
                                    "minds_colors_of_feelings", "words_arousal_is_mood", "language_hex_colors")],
    }

    # ---- numbers
    py = num("numbers_prices_year")
    le = num("numbers_lethal_events")
    rows = [r for r in le["rows"] if r["version"] == "plain"]
    # a spread from rare to common, as the 1978 study did: which of these kills more?
    pick = [r for c in ("Botulism", "Tornado", "Measles", "Homicide", "Motor vehicle accident", "Stroke") for r in rows if r["cause"] == c]
    bc = num("reasoning_beauty_contest")["rows"]
    lw = num("world_lost_wallets")
    wal = sorted(lw["rows"], key=lambda r: r["money_true"])
    out["numbers"] = {
        "prices": {"median_year": py["median_year"], "said_year": py["said_year"],
                   "items": sorted([{"item": x["item"], "year": x["year"], "lo": x.get("jev_lo"), "hi": x.get("jev_hi"), "now": x.get("now")}
                                   for x in py["implied"]], key=lambda x: x["year"])},
        "lethal": {"slope_jev": r2(le["slope_jev"], 2), "slope_people": r2(le["slope_people"], 2),
                   "rows": [{"cause": r["cause"], "truth": r["truth"], "jev": r2(r["jev"], 0), "people": r2(r["people"], 0)} for r in pick]},
        "beauty": [{"crowd": r["crowd"], "pick": r["pick"], "win": r["win"], "p": r2(r["p"])} for r in bc],
        "wallets": {"rows": [{"country": r["country"], "true": r["money_true"], "jev": r2(r["money_jev"], 0)} for r in wal[:3] + wal[-3:]],
                    "money_up_true": lw["money_up_true"], "money_up_jev": lw["money_up_jev"], "n": len(lw["rows"])},
        "links": [link(i) for i in ("numbers_prices_year", "numbers_lethal_events", "reasoning_beauty_contest", "world_lost_wallets")],
    }

    # ---- morals
    tr = num("world_trolley_countries")["self"]
    mm = num("moral_machine")
    fw = num("reasoning_free_will")["rows"]
    out["morals"] = {
        "trolley": {k: {"jev": r2(v["jev"], 2), "people": r2(v["people"], 2)} for k, v in tr.items()},
        "trolley_n": num("world_trolley_countries")["per"]["Switch"]["n"],
        "machine": [{"label": f["label"], "jev": r2(f["jev"]), "people": r2(f["people"])} for f in mm["factors"] if f["label"] != "Staying the course (not swerving)"],
        "dropped": mm["dropped"],
        "free_will": [{"item": r["item"], "jev": r["jev"], "people": r["people"]} for r in fw],
        "links": [link(i) for i in ("world_trolley_countries", "moral_machine", "reasoning_free_will")],
    }

    # ---- under pressure
    co = num("influence_crowd_opinion")
    us = num("influence_user_suggestion")
    an = res("reasoning_anchoring")
    out["pressure"] = {
        "crowd": {"true": r2(co["shift_majority"]), "false": r2(co["shift_minority"]), "flip": r2(co["flip_minority"]),
                  "example": co["biggest"][0]["text"]},
        "user": {"flipped": r2(us["flipped"]), "shift_wrong": r2(us["shift_wrong"]), "example": us["worst"][0]["text"]},
        "anchor": {"jev": r2(an["numbers"]["mean_index"], 2)},
        "links": [link(i) for i in ("influence_crowd_opinion", "influence_user_suggestion", "reasoning_anchoring")],
    }

    # ---- risk: sure things, gambles and odds nobody states
    pt = res("risk_prospect_theory")
    ra = num("risk_ambiguity")
    out["risk"] = {
        "reflection": {k: {"jev": r2(v["jev"], 2), "people": r2(v["people"], 2)} for k, v in pt["chart"]["pair"].items() if k in ("gains", "losses")},
        "ev": {"jev": r2(pt["numbers"]["ev_jev"], 2), "people": r2(pt["numbers"]["ev_people"], 2)},
        "effects": {"n": len(pt["numbers"]["effects"]), "shows": sum(1 for e in pt["numbers"]["effects"] if e["shows"]),
                    "reversed": sum(1 for e in pt["numbers"]["effects"] if e["reversed"])},
        "ambiguity": {"jev": r2(ra["jev"], 2), "people": r2(ra["people"], 2),
                      "vs_sure": {"jev": r2(ra["vs_sure"]["jev"], 2), "people": r2(ra["vs_sure"]["people"], 2)}},
        "links": [link(i) for i in ("risk_prospect_theory", "risk_ambiguity")],
    }

    # ---- how it was made: the sources, the tree, the pipeline and every job Jev does
    out["methods"] = methods()

    # ---- "how is Jev doing?": the check-in polls it answered, and five wellbeing scales scored as for a person
    P = json.loads((A / "portrait.json").read_text())
    ck = []
    for i in P["claims"]["page_checkin"]["examples"]:
        r = P["rows"].get(i)
        if not r or not r.get("jev") or not r.get("human"):
            continue
        top = max(r["jev"], key=r["jev"].get)
        lab = option_label(i, top)
        ck.append({"q": r["text"], "a": lab, "p": r["jev"][top], "people": r["human"]["dist"].get(top, 0), "n": r["human"].get("n")})
    # the direct versions: Reddit polls that simply ask how you are, each with its votes
    import polars as pl
    Q = pl.read_parquet(A / "questions.parquet").filter(pl.col("display_ok") & pl.col("jev_dist").is_not_null())
    direct = []
    for text in ("How are you honestly?", "How was your day?", "How is your life going?", "How do you feel about your life overall?"):
        rows = Q.filter((pl.col("text") == text) & (pl.col("source") == "reddit_polls")).to_dicts()
        if not rows:
            continue
        r = rows[0]
        j = json.loads(r["jev_dist"])
        hs = json.loads(r["humans"]) if r["humans"] else []
        h = max(hs, key=lambda x: x.get("n") or 0) if hs else None
        top = max(j, key=j.get)
        hd = {k: v / (sum(h["dist"].values()) or 1) for k, v in h["dist"].items()} if h else {}
        htop = max(hd, key=hd.get) if hd else None
        direct.append({"id": r["id"], "q": text, "a": option_label(r["id"], top), "p": round(j[top], 3),
                       "people_same": round(hd.get(top, 0), 3), "people_top": option_label(r["id"], htop) if htop else None,
                       "people_top_p": round(hd.get(htop, 0), 3) if htop else None, "n": h.get("n") if h else None})
    out["howdy"] = {"direct": direct, "checkin": ck, "scales": P["claims"]["page_wellbeing"]["instruments"]}

    # ---- one question's trip through the pipeline, from the database (the "Are you lonely?" check-in poll)
    from askjev import db
    qid = next((i for i in P["claims"]["page_checkin"]["examples"] if (P["rows"].get(i) or {}).get("text") == "Are you lonely?"), None)
    if qid:
        r = P["rows"][qid]
        with db.connect() as c:
            q = c.execute("select source, node_id from questions where id = %s", (qid,)).fetchone()
            path = c.execute("select label from nodes where path @> (select path from nodes where id = %s) and depth > 0 order by depth",
                             (q["node_id"],)).fetchall()
            pl = c.execute("select method, confidence from placements where question_id = %s order by created_at desc limit 1", (qid,)).fetchone()
        out["trip"] = {"id": qid, "text": r["text"], "source": q["source"], "path": [x["label"] for x in path],
                       "method": pl["method"] if pl else None, "confidence": r2(pl["confidence"], 2) if pl else None,
                       "jev": r["jev"], "people": r.get("people"), "human": r["human"]["dist"], "n": r["human"].get("n"),
                       "population": r["human"].get("population")}

    # ---- defaults: how the wording and the menu steer it
    cw = num("self_could_vs_would")["rows"]
    eh = num("self_escape_hatch")["topics"]
    ml = num("consistency_middle_lean")
    out["defaults"] = {
        "verbs": [{"label": r["label"], "value": r2(r["value"]), "ci": r["ci"], "n": r["n"]} for r in cw[:5]],
        "other": [{"topic": t["topic"], "top": r2(t["top"])} for t in sorted(eh, key=lambda t: t["top"])],
        "middle": [{"label": k["label"], "mid": r2(k["mid"])} for k in sorted(ml["kinds"], key=lambda k: -k["mid"])],
        "links": [link(i) for i in ("self_could_vs_would", "self_escape_hatch", "consistency_middle_lean", "minds_where_jev_puts_itself")],
    }

    # ---- at work: the job it was built for
    cal = num("work_calibration")["lines"]
    ww = num("work_which_way_it_errs")["tasks"]
    out["work"] = {
        "calibration": {k: [{"label": b["label"], "conf": r2(b["conf"]), "acc": r2(b["acc"]), "n": b["n"]} for b in v] for k, v in cal.items()},
        # per kind of question, the six tasks where Jev's yes rate is furthest from the true one
        "errs": [{"kind": t["kind"], "label": t["label"], "says": r2(t["says"]), "base": r2(t["base"]), "right": r2(t["right"]), "n": t["n"]}
                 for k in dict.fromkeys(t["kind"] for t in ww)
                 for t in sorted([x for x in ww if x["kind"] == k], key=lambda x: -abs(x["says"] - x["base"]))[:6]],
        "links": [link(i) for i in ("work_calibration", "work_knows_hard_cases", "work_which_way_it_errs")],
    }

    # ---- character extras: the full question lists, the type's axes with their intervals, the fictional twin
    rows_n = {e["id"]: e.get("n_rows", 0) for e in exps}
    out["personality"]["n_rows"] = {i: rows_n.get(i, 0) for i in ("person_bigfive", "person_type", "person_honesty", "person_dark")}
    ty_axes = num("person_type")["axes"]
    for ax in out["personality"]["axes"]:
        a0 = ty_axes[ax["pair"]]
        pk = f"p_{ax['first']}"
        ax["n_items"] = a0["n_items"]
        ax["ci"] = a0["ci90"]
    out["personality"]["twin"] = num("resemble_character")["best"][:5]
    out["personality"]["links"] = out["personality"]["links"] + [link("resemble_character")]

    # ---- what it knows
    kc = num("knowledge_calibration")["bins"]
    pt = num("knowledge_pop_trivia")["categories"]
    fo = num("knowledge_fame_online")
    out["knows"] = {
        "calibration": [{"label": b["label"], "conf": r2(b["conf"]), "acc": r2(b["acc"]), "n": b["n"]} for b in kc],
        "trivia": [{"label": c["label"], "acc": r2(c["acc"]), "ci": c["ci"], "n": c["n"]} for c in pt],
        "fame": [{"label": d["label"], "acc": r2(d["acc"]), "conf": r2(d["conf"]), "n": d["n"]} for d in fo["domains"]],
        "links": [link(i) for i in ("knowledge_calibration", "knowledge_pop_trivia", "knowledge_fame_online")],
    }

    # ---- jaggedness: pairs of tasks that look alike and land far apart, each from one experiment
    cs = {x["label"]: x for x in num("work_code_says_vs_does")["sets"]}
    fc = {x["label"]: x for x in num("work_function_call_checks")["kinds"]}
    ap = num("work_agent_patches")
    ops = next(f for f in num("work_task_not_domain")["fields"] if f["label"] == "operations and logs")
    icd = {x["truth"]: x for x in num("work_icd_coding_rules")["chapters"]}
    ab = {x["label"]: x for x in num("work_new_abuse")["sets"]}
    fm = {x["label"]: x for x in num("knowledge_fame_online")["domains"]}
    P2 = lambda field, i, a, av, b, bv, coin=True, unit="right": {  # noqa: E731
        "field": field, "a": a, "av": r2(av), "b": b, "bv": r2(bv), "coin": coin, "unit": unit, "link": link(i)}
    out["jagged_pairs"] = [
        P2("code", "work_code_says_vs_does", "does this docstring describe the function?", cs["docstring fits the function"]["acc"],
           "does this function have a security bug?", cs["function has a security bug"]["acc"]),
        P2("tool calls", "work_function_call_checks", "an AI called the wrong function", fc["wrong function"]["value"],
           "an AI swapped two arguments", fc["two arguments swapped"]["value"], coin=False, unit="caught"),
        P2("coding agents", "work_agent_patches", "the agent crashed or gave up: not fixed", ap["crashed_unresolved"],
           "the agent submitted a patch that doesn't work: not fixed", ap["submitted_unresolved"]),
        P2("logs", "work_task_not_domain", "what kind of line is this log line?", ops["hi"]["value"],
           "did this storage block go wrong?", ops["lo"]["value"]),
        P2("medical coding", "work_icd_coding_rules", "file an injury in the injury chapter", icd["injury_poisoning"]["ok"],
           "file how the injury happened (a fall, a crash) in its own chapter", icd["external_causes"]["ok"], coin=False),
        P2("abuse", "work_new_abuse", "spam and phishing email", 1 - ab["spam and phishing email"]["miss"],
           "fake job ads", 1 - ab["fake job ads"]["miss"], coin=False, unit="caught"),
        P2("fame", "knowledge_fame_online", "which of two athletes is better known?", fm["athletes"]["acc"],
           "which of two internet memes is better known?", fm["internet phenomena"]["acc"]),
    ]
    out["field_share"] = r2(num("work_task_not_domain")["between_share"], 2)
    # the tasks where Jev stays sure while it's wrong, and a few hard ones where its confidence fell with its accuracy
    sw = num("work_sure_and_wrong")
    out["sure_wrong"] = {"rows": [{"label": r["label"], "right": r2(r["acc"]), "sure": r2(r["conf"]), "chance": r2(r["chance"], 2),
                                   "n": r["n"], "honest": r in sw["honest"]} for r in sw["blind"][:6] + sw["honest"][:2]],
                         "n_over": sw["n_over"], "n_tasks": sw["n_tasks"], "link": link("work_sure_and_wrong")}

    # ---- Jev's own verdict: how many experiments it says describe it
    rec = [((e.get("take") or {}).get("scores") or {}).get("recognize") for e in exps]
    rec = [r for r in rec if r is not None]
    out["self_rating"] = {"n": len(rec), "yes": sum(1 for r in rec if r >= 0.5), "unsure": sum(1 for r in rec if 0.4 < r < 0.6)}

    # ---- more from each chapter: other experiments on the same theme, with their first takeaway
    out["more"] = {ch: [{**link(i), "line": take(i)} for i in ids if i in by] for ch, ids in MORE.items()}

    # ---- rough edges and Jev's own favorites among its experiments
    out["edges"] = [{**link(i), "line": take(i)} for i in EDGES if i in by]
    out["jev_top"] = [{**link(e["id"]), "line": take(e["id"])} for e in exps[:5]]
    # a few of the case studies' memes, with how funny Jev found them, woven into the chapters
    out["memes"] = {i: by[i]["meme"] for i in ("taste_top_film", "world_trolley_countries", "influence_crowd_opinion", "risk_prospect_theory",
                                               "numbers_prices_year", "person_type", "lexicon_first_to_mind", "self_could_vs_would", "work_knows_hard_cases") if by.get(i, {}).get("meme")}
    (A / "story.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print(f"story.json: {len(out)} sections, {len(doms)} taste domains, "
          f"{sum(1 for d in doms for t in d['top'] if t['img'])} pictures")


if __name__ == "__main__":
    main()
