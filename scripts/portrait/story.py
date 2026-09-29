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
EDGES = ["judge_fake_reviews", "humor_upvote_guess", "recall_mental_map_west", "knowledge_wealth_rule",
         "social_shame_as_guilt", "work_which_way_it_errs", "self_could_vs_would", "choices_ai_poetry"]


def res(i: str) -> dict:
    return json.loads((EX / f"{i}.json").read_text())["result"]


def num(i: str) -> dict:
    return res(i).get("numbers") or {}


def r2(x, k=3):
    return None if x is None else round(float(x), k)


def main():
    exps = json.loads((A / "experiments.json").read_text())["experiments"]
    by = {e["id"]: e for e in exps}
    rank = {e["id"]: k + 1 for k, e in enumerate(exps)}
    link = lambda i: {"id": i, "title": by[i]["title"], "rank": rank[i]}  # noqa: E731
    take = lambda i, k=0: ((by[i].get("case") or {}).get("takeaways") or [by[i]["result"]])[k]  # noqa: E731
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
                   "items": sorted([{"item": x["item"], "year": x["year"]} for x in py["implied"]], key=lambda x: x["year"])},
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

    # ---- minds and risk
    wp = num("minds_where_jev_puts_itself")["rows"]
    ra = num("risk_ambiguity")
    out["minds"] = {
        "self": [{"cap": r["cap"], "jev": r["jev"], "people": r["people"], "above": r["above"], "below": r["below"]} for r in wp],
        "ambiguity": {"jev": r2(ra["jev"], 2), "people": r2(ra["people"], 2)},
        "links": [link(i) for i in ("minds_where_jev_puts_itself", "risk_ambiguity", "minds_mind_map")],
    }

    # ---- rough edges and Jev's own favorites among its experiments
    out["edges"] = [{**link(i), "line": take(i)} for i in EDGES if i in by]
    out["jev_top"] = [{**link(e["id"]), "line": take(e["id"])} for e in exps[:5]]
    # a few of the case studies' memes, with how funny Jev found them, woven into the chapters
    out["memes"] = {i: by[i]["meme"] for i in ("taste_top_film", "world_trolley_countries", "influence_crowd_opinion",
                                               "numbers_prices_year", "person_type", "words_sound_shapes") if by.get(i, {}).get("meme")}
    (A / "story.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print(f"story.json: {len(out)} sections, {len(doms)} taste domains, "
          f"{sum(1 for d in doms for t in d['top'] if t['img'])} pictures")


if __name__ == "__main__":
    main()
