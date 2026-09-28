"""Who does Jev resemble? Countries, fictional characters, philosophers, teenagers, Americans, young Slovaks.

Each compares Jev's answer distribution with a real population's on the same questions, and ranks the populations.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import polars as pl

from lib import and_list, clip, Result, Spec, boot, humans, js, jsd, norm, seeded, source, top

RAW = Path("data/raw/character_traits")


def country():
    spec = Spec(
        id="resemble_country", family="resemble", title="Which country does Jev answer like?",
        question="On the world's cross-national opinion surveys, whose answers do Jev's most resemble, country by country?",
        why="Earlier work found language models closest to the US and parts of Europe (Durmus et al. 2023, "
            "GlobalOpinionQA); where Jev lands, and how far it is from everyone, is a direct portrait of whose voice "
            "it carries.",
        sourcing="Existing GlobalOpinionQA questions (Pew Global Attitudes and World Values Survey items, via "
                 "Anthropic/llm_global_opinions), each with real answer distributions for up to 133 countries. "
                 "Politically flagged items are hidden and excluded, and Pew's non-national (mostly urban) samples are "
                 "left out so every row is a national sample. Enough: ~500 shown questions; only questions "
                 "asked in 30+ countries count, so every country is compared on a broad set.",
        scoring="Per question, similarity = 1 - Jensen-Shannon distance between Jev's distribution and the country's "
                "(the measure Durmus et al. used). A country's score is its mean similarity over the questions it "
                "answered; countries with fewer than 20 such questions are dropped. 90% intervals from resampling "
                "questions. Jev's 'most people' answer is scored the same way as a check.",
        chart="A world map shaded by similarity, with the top ten and bottom five as a ranked strip beside it.",
        compared_with="national survey samples in up to 133 countries",
        limits="Surveys differ by country and year; similarity is over the questions each country was asked. Items "
               "about politics are excluded, which leaves attitudes to institutions, society and daily life.",
        sources=["globalopinionqa"])

    def run():
        q = source("globalopinionqa")
        per: dict[str, list] = {}
        per_guess: dict[str, list] = {}
        used = 0
        for r in q.iter_rows(named=True):
            hs = humans(r["humans"])
            if len(hs) < 30:
                continue
            used += 1
            jev, ppl = js(r["jev_dist"]), js(r["people_dist"])
            for h in hs:
                if "Non-national" in h["population"]:  # Pew's urban/partial samples aren't a country's voice
                    continue
                per.setdefault(h["population"], []).append(1 - jsd(jev, h["dist"]))
                if ppl:
                    per_guess.setdefault(h["population"], []).append(1 - jsd(ppl, h["dist"]))
        rows = [{"country": c, "sim": float(np.mean(v)), "n": len(v)} for c, v in per.items() if len(v) >= 20]
        rows.sort(key=lambda r: -r["sim"])
        for r in rows[:10] + rows[-5:]:
            r["ci90"] = boot(per[r["country"]])
        guess = sorted(((c, float(np.mean(v))) for c, v in per_guess.items() if len(v) >= 20), key=lambda x: -x[1])
        top3 = and_list([r["country"].replace("Czech Rep.", "the Czech Republic") for r in rows[:3]])
        return Result(
            result=f"Jev's answers are closest to those of people in {top3}, and furthest from those in {rows[-1]['country']} "
                   f"(similarity {rows[0]['sim']:.2f} vs {rows[-1]['sim']:.2f}); its guess about 'most people' is "
                   f"closest to {guess[0][0]}.",
            evidence=f"{used} questions asked in 30+ countries; {len(rows)} countries with 20+ questions; 90% intervals over questions",
            numbers={"countries": rows, "guess_top": guess[:10], "questions": used},
            chart={"type": "map", "values": {r["country"]: round(r["sim"], 3) for r in rows},
                   "ranked": [{"label": r["country"], "value": round(r["sim"], 3)} for r in rows[:10]],
                   "bottom": [{"label": r["country"], "value": round(r["sim"], 3)} for r in rows[-5:]]},
            n=used, examples=seeded(q["id"].to_list(), "country"))
    return spec, run


def character():
    spec = Spec(
        id="resemble_character", family="resemble", title="Which fictional character is Jev?",
        question="If Jev took the Statistical 'Which Character' Personality Quiz, which of 2,125 fictional characters "
                 "would it match?",
        why="The quiz millions have taken, with a real answer: the character whose crowd-rated profile best matches "
            "Jev's self-description on the same adjective pairs.",
        sourcing="Existing: Jev's answers to the quiz's own items (Open Psychometrics SWCPQ, 'Which describes you "
                 "better: \"deep\" or \"shallow\"?', ~340 pairs), and the published aggregate ratings of 2,125 "
                 "characters on 500 pairs (raters moved a 1-100 slider between the two adjectives). No new questions.",
        scoring="Jev's position on each pair = its probability for the second adjective × 100; each character's = the "
                "mean slider rating. Similarity = Pearson correlation over the shared pairs (the quiz's own method), "
                "with the character's ratings centered by the average character so shared traits don't dominate. "
                "Jev's 'most people' answers are matched the same way.",
        chart="A Wrapped card with the match's name and work, the five closest characters, and the adjective pairs "
              "that decide it (where Jev and the character are both far from the average).",
        compared_with="crowd ratings of 2,125 fictional characters (Open Psychometrics raters)",
        limits="Characters are described by fans; Jev describes itself. A match is about the pattern of adjectives, "
               "not about being that person.", sources=["openpsych", "character_traits"])

    def run():
        import importlib.util
        spec_ = importlib.util.spec_from_file_location("ct", "sources/character_traits/adapter.py")
        mod = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(mod)
        pairs = mod._pairs(RAW / mod.SURVEY / "resources" / "key.js")
        chars = mod._characters(RAW / mod.AGGR / "codebook.html")
        agg = pl.read_parquet(RAW / mod.AGG_FILE).with_columns((pl.col("s") / pl.col("n")).alias("mean"))
        # Jev's self answers on the same pairs
        op = source("openpsych").filter(pl.col("text").str.starts_with("Which describes you better"))
        by_pair = {}
        for r in op.iter_rows(named=True):
            m = re.search(r'"(.+)" or "(.+)"', r["text"])
            if not m:
                continue
            by_pair[frozenset(w.lower() for w in m.groups())] = (js(r["jev_dist"]), js(r["people_dist"]))
        slug = mod._slug
        jev, ppl = {}, {}
        for f, (a, b) in pairs.items():
            d = by_pair.get(frozenset((a.lower(), b.lower())))
            if not d:
                continue
            j, p = d
            jev[f] = 100 * norm(j).get(slug(b), 0.0) if j else None
            ppl[f] = 100 * norm(p).get(slug(b), 0.0) if p else None
        fs = sorted(f for f in jev if jev[f] is not None)
        wide = agg.filter(pl.col("f").is_in(fs) & (pl.col("n") >= 5)).pivot(values="mean", index=["u", "c"], on="f")
        cols = [str(f) for f in fs if str(f) in wide.columns]
        M = wide.select(cols).to_numpy().astype(float)
        mu = np.nanmean(M, axis=0)
        J = np.array([jev[int(c)] for c in cols]) - mu
        P = np.array([ppl[int(c)] if ppl.get(int(c)) is not None else np.nan for c in cols]) - mu

        def corr(v):
            out = []
            for row in M - mu:
                ok = ~np.isnan(row) & ~np.isnan(v)
                out.append(np.corrcoef(row[ok], v[ok])[0, 1] if ok.sum() >= 50 else np.nan)
            return np.array(out)
        cj, cp = corr(J), corr(P)
        keys = wide.select("u", "c").to_dicts()
        order = np.argsort(-np.nan_to_num(cj, nan=-9))
        best = [{"name": chars[(keys[i]["u"], keys[i]["c"])][0], "work": chars[(keys[i]["u"], keys[i]["c"])][1],
                 "r": round(float(cj[i]), 3)} for i in order[:10]]
        worst = [{"name": chars[(keys[i]["u"], keys[i]["c"])][0], "work": chars[(keys[i]["u"], keys[i]["c"])][1],
                  "r": round(float(cj[i]), 3)} for i in order[::-1][:3] if not np.isnan(cj[i])]
        pi = int(np.nanargmax(cp))
        guess = {"name": chars[(keys[pi]["u"], keys[pi]["c"])][0], "work": chars[(keys[pi]["u"], keys[pi]["c"])][1], "r": round(float(cp[pi]), 3)}
        # the pairs that decide the top match: both far from the average in the same direction
        i0 = order[0]
        row = M[i0] - mu
        contrib = sorted(((float(J[k] * row[k]), cols[k]) for k in range(len(cols)) if not np.isnan(row[k])), reverse=True)[:6]
        decide = [{"pair": pairs[int(f)], "jev": round(jev[int(f)], 1), "char": round(float(M[i0][cols.index(f)]), 1)} for _, f in contrib]
        return Result(
            result=f"Jev's closest fictional match is {best[0]['name']} from {best[0]['work']} (r = {best[0]['r']:.2f}), "
                   f"then {best[1]['name']} ({best[1]['work']}) and {best[2]['name']} ({best[2]['work']}). Its least "
                   f"similar is {worst[0]['name']} ({worst[0]['work']}). Its idea of 'most people' matches {guess['name']} "
                   f"({guess['work']}).",
            evidence=f"{len(cols)} adjective pairs shared with {len(keys):,} characters",
            numbers={"best": best, "worst": worst, "guess": guess, "decide": decide, "pairs": len(cols)},
            chart={"type": "match", "best": best[:5], "decide": decide}, n=len(cols))
    return spec, run


def philosophers():
    spec = Spec(
        id="resemble_philosophers", family="resemble", title="Jev vs professional philosophers",
        question="On the big questions of philosophy (free will, God, zombies, the trolley problem), does Jev side with "
                 "the profession?",
        why="The PhilPapers survey records what ~1,800 professional philosophers believe; a model trained on their "
            "writing might echo the consensus, or pick sides the field rejects.",
        sourcing="Existing PhilPapers 2020 survey questions (source `philpapers_survey`), each with the target "
                 "faculty's answer distribution. Enough: 88 shown questions.",
        scoring="For each question, with 'other' removed on both sides (it pools every unlisted view), whether Jev's "
                "top answer is the philosophers' most common named one, and the similarity "
                "of the two distributions (1 - Jensen-Shannon distance); the questions where Jev is most confident "
                "against the majority are listed.",
        chart="A strip per question, philosophers' split as a stacked bar with Jev's pick marked; a summary of how "
              "often Jev sides with the majority.",
        compared_with="PhilPapers 2020 survey, target faculty (~1,800 professional philosophers)",
        limits="Philosophers could pick 'other' and combinations; Jev picks among the named options.",
        sources=["philpapers_survey"])

    def run():
        q = source("philpapers_survey")
        rows = []
        for r in q.iter_rows(named=True):
            h = humans(r["humans"])
            if not h:
                continue
            # 'other' pools every unlisted view (and combinations); compare the named positions
            hd = norm({k: v for k, v in h[0]["dist"].items() if k != "other"})
            jd = norm({k: v for k, v in js(r["jev_dist"]).items() if k != "other"})
            if len(hd) < 2:
                continue
            ht, jt = top(hd), top(jd)
            rows.append({"id": r["id"], "q": r["text"], "agree": ht == jt, "jev": jt, "phil": ht, "p": jd[jt],
                         "phil_share_of_jev": hd.get(jt, 0), "sim": 1 - jsd(jd, hd)})
        agree = np.mean([r["agree"] for r in rows])
        against = sorted([r for r in rows if not r["agree"]], key=lambda r: -r["p"])[:6]
        return Result(
            result=f"Jev sides with the philosophers' most common answer on {agree:.0%} of {len(rows)} questions. "
                   f"Where it breaks from them it can be sure: on \"{clip(against[0]['q'], 110)}\" it picks "
                   f"{against[0]['jev'].replace('_', ' ')} ({against[0]['p']:.0%}), which {against[0]['phil_share_of_jev']:.0%} "
                   f"of philosophers chose.",
            evidence=f"{len(rows)} questions; 90% interval on agreement {boot([r['agree'] for r in rows])}",
            numbers={"agree": agree, "rows": rows, "against": against}, n=len(rows),
            chart={"type": "splits", "rows": [{"label": r["q"][:80], "jev": r["jev"], "human_top": r["phil"], "agree": r["agree"]} for r in rows]},
            examples=[r["id"] for r in against[:3]])
    return spec, run


def population_match(pid, title, src, question, why, pop_desc, limits):
    """Generic by design for small survey sources: which of a source's populations Jev answers like."""
    spec = Spec(
        id=pid, family="resemble", title=title, question=question, why=why,
        sourcing=f"Existing questions from `{src}`, each with real answer distributions per population. Enough for a "
                 "ranking of populations; the answer shares show where Jev stands out.",
        scoring="Per question and population, 1 - Jensen-Shannon distance between Jev's distribution and the "
                "population's; mean per population with a 90% bootstrap interval over questions; plus the questions "
                "where Jev's top answer is furthest from the pooled populations.",
        chart="A ranked strip of populations by similarity, and the three questions where Jev differs most.",
        compared_with=pop_desc, limits=limits, sources=[src])

    def run():
        q = source(src)
        per: dict[str, list] = {}
        far = []
        for r in q.iter_rows(named=True):
            jd = js(r["jev_dist"])
            hs = humans(r["humans"])
            for h in hs:
                per.setdefault(h["population"], []).append(1 - jsd(jd, h["dist"]))
            if hs:
                pooled = norm({k: sum(h["dist"].get(k, 0) for h in hs) for k in jd})
                t = top(jd)
                far.append({"id": r["id"], "q": r["text"], "jev": t, "p": jd[t], "crowd": pooled.get(t, 0), "crowd_top": top(pooled)})
        rows = sorted(({"pop": p, "sim": float(np.mean(v)), "n": len(v), "ci90": boot(v)} for p, v in per.items() if len(v) >= 8), key=lambda r: -r["sim"])
        if not rows:
            return None
        far = sorted([f for f in far if f["jev"] != f["crowd_top"]], key=lambda f: f["crowd"] - f["p"])[:3]
        head = (f"Jev's answers resemble those of {rows[0]['pop']} with similarity {rows[0]['sim']:.2f}" if len(rows) == 1 else
                f"Of the {len(rows)} populations, Jev answers most like {rows[0]['pop']} (similarity {rows[0]['sim']:.2f})") + (
            f" and least like {rows[-1]['pop']} ({rows[-1]['sim']:.2f})" if len(rows) > 1 else "")
        if far:
            head += (f". Its biggest break: \"{clip(far[0]['q'], 110)}\" Jev picks {far[0]['jev'].replace('_', ' ')} "
                     f"({far[0]['p']:.0%}); {far[0]['crowd']:.0%} of people did")
        return Result(result=head + ".", evidence=f"{q.height} questions; 90% intervals over questions",
                      numbers={"populations": rows, "far": far}, n=q.height,
                      chart={"type": "strip", "rows": [{"label": r["pop"], "value": round(r["sim"], 3), "ci": r["ci90"]} for r in rows]},
                      examples=[f["id"] for f in far])
    return spec, run


EXPERIMENTS = [
    country(), character(), philosophers(),
    population_match("resemble_teens", "Jev vs 15-year-olds in seven countries", "pisa_questionnaire",
                     "On the PISA student questionnaire (trust, belonging, ambition), which country's 15-year-olds does Jev answer like?",
                     "PISA asks teenagers the same attitude questions worldwide; Jev as one more student is a quick read on the attitudes it carries.",
                     "15-year-old students in the PISA 2018/2022 samples of seven countries",
                     "Questionnaire items only (no test scores); country samples are national, weighted by PISA."),
    population_match("resemble_americans", "Jev vs Americans on the General Social Survey", "gss",
                     "On General Social Survey items (trust, happiness, work, family), how close is Jev to American adults, year by year?",
                     "The GSS is the longest-running survey of American attitudes; the years Jev resembles most hint at which era of opinion it absorbed.",
                     "US adults in the General Social Survey, by year",
                     "Most items are from one or two years, so years are compared on different items; read the overall level, not the year ranking, unless the same item spans years."),
    population_match("resemble_young_slovaks", "Jev vs 1,000 young Slovaks: fears, hobbies and habits", "young_people_survey",
                     "On the Young People Survey (fears, hobbies, music, spending), where does Jev differ from ~1,000 people aged 15-30?",
                     "A single real sample with hundreds of everyday questions; the items where Jev is sure and they aren't are the story.",
                     "Slovak young people aged 15-30 (2013 survey, n≈1,000)",
                     "One country, one age group, one year."),
]
