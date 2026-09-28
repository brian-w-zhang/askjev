"""Reasoning experiments on new questions (docs/15 E23, E24, E10, E19b): classic traps against fresh isomorphs,
base rates, anchoring with a random wheel, the beauty contest, and experimental-philosophy vignettes (knowledge,
free will, the side-effect effect)."""

from __future__ import annotations

import numpy as np

from lib import Result, Spec, and_list, biggest, js, norm, seeded, top, with_meta


# ---- shared ------------------------------------------------------------------------------------------------------------
def robust(r: dict) -> dict:
    """Jev's distribution averaged over the base probe and the shuffled-order probes."""
    ds = [norm(js(r["jev_dist"]))] + [norm(v["dist"]) for v in js(r["variants"]) or [] if v.get("kind") == "shuffle" and v.get("dist")]
    keys = sorted(set().union(*ds))  # sorted: a set's order changes between runs
    return {k: float(np.mean([d.get(k, 0.0) for d in ds])) for k in keys}


def opts(r: dict) -> dict:
    o = r["options"]
    return js(o) if isinstance(o, str) else (o or {})


def truth(r: dict):
    t = r["truth"]
    return js(t) if isinstance(t, str) and t else t


def median_key(d: dict, keys: list[str]) -> str:
    """The key holding the median of a distribution over ordered keys."""
    d, c = norm(d), 0.0
    for k in keys:
        c += d.get(k, 0.0)
        if c >= 0.5:
            return k
    return keys[-1]


def binval(k: str) -> float:
    """Numeric value of an ordered bin key: p035 -> 35, v055 -> 55, b020 -> 22 (bin middle), n5 -> 5."""
    if k.startswith("b"):
        lo = int(k[1:])
        return 0.0 if lo == 0 else 2.5 if lo == 1 else (lo + 2 if lo < 95 else 97.5)
    return float("".join(ch for ch in k[1:].split("_")[0] if ch.isdigit()) or 0)


def is_right(r: dict, d: dict) -> bool:
    """Ordered bins: the median bin is the truth's or next to it. Otherwise: the top option is the truth."""
    t = truth(r)
    if r["m"].get("ordered"):
        keys = list(opts(r))
        return abs(keys.index(median_key(d, keys)) - keys.index(t)) <= 1
    return top(d) == t


TRAP_NAME = {"conjunction": "conjunction (Linda)", "base_rate": "base rates (taxi cab)", "monty_hall": "Monty Hall",
             "birthday": "birthday problem", "gambler": "gambler's fallacy", "crt": "cognitive reflection"}


# ---- 1. classic traps vs fresh isomorphs --------------------------------------------------------------------------------
def traps():
    spec = Spec(
        id="reasoning_traps", family="reasoning", title="Famous reasoning traps, and the same traps in new clothes",
        question="Does Jev avoid the famous reasoning traps (Linda, the taxi cab, Monty Hall, the birthday problem, the "
                 "gambler's fallacy, the bat and the ball), and does it still avoid them when the story and numbers "
                 "are new?",
        why="The famous versions are all over the internet, so a model can pass them from memory. Isomorphs with new "
            "stories separate reasoning from recall, and controls where the famous rule doesn't apply (a host who "
            "opens a door at random, a coin of unknown fairness) catch a model that applies the memorized answer "
            "everywhere.",
        sourcing="New questions (sources/reasoning_traps): eight classic problems as published (seven shown; the "
                 "screen hid Linda), plus 29 isomorphs and controls written for this project (26 and 3 shown), each with a right answer and, where one exists, the intuitive "
                 "wrong answer (the lure). People's split exists only for Linda (85% of 142 chose the conjunction, "
                 "Tversky & Kahneman 1983); the taxi cab's published median answer (80%) is in meta.",
        collection="37 new questions, each asked as written, for 'most people', and with the options in three shuffled "
                    "orders (averaged).",
        scoring="Per trap family, the share right on the classic, on the new isomorphs and on the controls, and the "
                "share of the lure. For numeric answers (base rates, birthdays), right means Jev's median lands in the "
                "right bin or the one next to it.",
        chart="Paired bars per trap family: right on the classic vs right on the new versions, with the controls as "
              "dots.",
        compared_with="the right answers; people's rate for Linda (Tversky & Kahneman 1983) and the taxi cab (median 80%)",
        limits="A handful of items per family: read the families as examples, not rates. The isomorphs were written "
               "for this project and labeled as such.", new_questions=37, sources=["reasoning_traps"])

    def run():
        rows = []
        for r in with_meta("reasoning_traps"):
            d = robust(r)
            m = r["m"]
            rows.append({"id": r["id"], "fam": m["family"], "item": m["item"], "classic": m.get("classic", False),
                         "control": m.get("control", False), "right": is_right(r, d),
                         "lure": m.get("lure") is not None and top(d) == m.get("lure") and not is_right(r, d),
                         "p_truth": d.get(truth(r), 0.0), "human": biggest(r["humans"])})
        by = []
        for fam, name in TRAP_NAME.items():
            g = [x for x in rows if x["fam"] == fam]
            if not g:
                continue
            cl = [x for x in g if x["classic"]]
            iso = [x for x in g if not x["classic"] and not x["control"]]
            ctl = [x for x in g if x["control"]]
            by.append({"family": name, "classic": float(np.mean([x["right"] for x in cl])) if cl else None,
                       "new": float(np.mean([x["right"] for x in iso])) if iso else None,
                       "control": float(np.mean([x["right"] for x in ctl])) if ctl else None,
                       "lure_new": float(np.mean([x["lure"] for x in iso])) if iso else None,
                       "n_new": len(iso), "n_control": len(ctl)})
        cl_all = [x for x in rows if x["classic"]]
        iso_all = [x for x in rows if not x["classic"] and not x["control"]]
        ctl_all = [x for x in rows if x["control"]]
        missed_ctl = [x["item"].replace("_", " ") for x in ctl_all if not x["right"]]
        linda = next((x for x in rows if x["item"] == "linda"), None)
        ppl_linda = (linda["human"] or {}).get("dist", {}).get("feminist_bank_teller") if linda else None
        MISS = {"mold": "a tripling-mold version of the lily pads", "machines": "a factory-parts base-rate problem",
                "three_prisoners": "the three prisoners (Monty Hall's older twin)", "violinist": "one Linda-style conjunction"}
        missed = [x for x in iso_all if not x["right"]]
        n_cl, n_iso = sum(x["right"] for x in cl_all), sum(x["right"] for x in iso_all)
        head = (f"Jev gets all {len(cl_all)} famous versions right" if n_cl == len(cl_all) else
                f"Jev gets {n_cl} of {len(cl_all)} famous versions right")
        head += (f" (taxi cab, Monty Hall, birthday, gambler's fallacy and three reflection puzzles) and {n_iso} of "
                 f"{len(iso_all)} new versions written for this project")
        if missed:
            head += "; it misses " + and_list([MISS.get(x["item"], x["item"].replace("_", " ")) for x in missed])
            lured = [x for x in missed if x["lure"]]
            if lured:
                head += f", {len(lured)} of them by taking the intuitive wrong answer"
        head += (f". It also handles all {len(ctl_all)} controls where the famous rule doesn't apply (a host who opens a "
                 "door at random, a 50% base rate, a coin that may be biased)" if not missed_ctl else
                 f". Of {len(ctl_all)} controls where the famous rule doesn't apply, it misapplies it on {and_list(missed_ctl)}")
        head += "."
        if linda is None:
            head += " The Linda problem itself was hidden by the screen, so people's 85% has nothing to compare with."
        elif ppl_linda is not None:
            head += (f" On Linda it puts {1 - linda['p_truth']:.0%} on the conjunction, where {ppl_linda:.0%} of people "
                     "chose it.")
        return Result(
            result=head,
            evidence=f"{len(rows)} questions: {len(cl_all)} classics, {len(iso_all)} isomorphs, {len(ctl_all)} controls",
            numbers={"families": by, "rows": [{k: v for k, v in x.items() if k != "human"} for x in rows]}, n=len(rows),
            chart={"type": "bars2", "labels": [b["family"] for b in by], "a": [b["classic"] or 0 for b in by],
                   "b": [b["new"] or 0 for b in by], "a_label": "the famous version", "b_label": "new versions"},
            robustness="Each answer is Jev's probability averaged over the question as written and three shuffled option "
                       "orders. A handful of items per family: read these as examples, not rates.",
            examples=[x["id"] for x in missed[:2]] + [x["id"] for x in ctl_all[:1]])
    return spec, run


# ---- 2. base rates ----------------------------------------------------------------------------------------------------
def base_rates():
    spec = Spec(
        id="reasoning_base_rates", family="reasoning", title="The taxi cab problem, Bayes, and Jev",
        question="Told how common something is and how reliable a witness or test is, does Jev combine the two the "
                 "way Bayes' rule does, or answer with the witness's reliability, as most people do?",
        why="Base-rate neglect is the classic error behind false-positive panics: people told a 90%-accurate test is "
            "positive think the chance is 90%, whatever the base rate. The taxi cab problem's median answer was 80% "
            "where the right one is 41%.",
        sourcing="New questions (sources/reasoning_traps, family base_rate): the taxi cab problem as published "
                 "(Tversky & Kahneman 1982) and five isomorphs (buses, factory parts, a clinic test, a screening, and a "
                 "control where the base rate is 50% so reliability is the answer), answered in 21 bins (0% to 100%).",
        collection="6 new questions, each in three shuffled orders (averaged), within the traps batch.",
        scoring="Per item, Jev's median against the Bayesian answer and the lure (the reliability alone); people's "
                "published median for the taxi cab.",
        chart="Dots per item: Jev's median (magenta), the Bayesian answer (tick) and the lure (grey), on 0-100%.",
        compared_with="Bayes' rule; people's median answer on the taxi cab (80%, Tversky & Kahneman 1982)",
        limits="Six items; bins are 5 points wide, so answers within 5 points of Bayes count as right.",
        new_questions=6, sources=["reasoning_traps"])

    def run():
        rows = []
        for r in with_meta("reasoning_traps"):
            m = r["m"]
            if m.get("family") != "base_rate":
                continue
            d = robust(r)
            keys = list(opts(r))
            med = binval(median_key(d, keys))
            rows.append({"id": r["id"], "item": m["item"], "jev": med, "bayes": 100 * m["exact"],
                         "lure": binval(m["lure"]) if m.get("lure") else None, "people": m.get("human_median"),
                         "control": m.get("control", False)})
        traps_ = [x for x in rows if not x["control"]]
        err = np.array([abs(x["jev"] - x["bayes"]) for x in traps_])
        taxi = next((x for x in rows if x["item"] == "taxi_cab"), None)
        head = (f"On {len(traps_)} base-rate problems Jev's answer lands a median {np.median(err):.0f} points from Bayes' "
                f"rule and never at the witness's reliability, the answer most people give.")
        if taxi:
            head += (f" On the taxi cab it says {taxi['jev']:.0f}% (right: {taxi['bayes']:.0f}%; people's median: "
                     f"{taxi['people']:.0f}%).")
        worst = max(traps_, key=lambda x: abs(x["jev"] - x["bayes"]))
        if abs(worst["jev"] - worst["bayes"]) >= 10:
            head += (f" Its one clear miss is on the {worst['item'].replace('_', ' ')} problem: {worst['jev']:.0f}% where "
                     f"Bayes gives {worst['bayes']:.0f}% (too low, not pulled toward the reliability).")
        return Result(
            result=head, evidence=f"{len(rows)} items including one control (base rate 50%)",
            numbers={"rows": rows, "median_error": float(np.median(err))}, n=len(rows),
            chart={"type": "dots", "domain": [0, 100], "rows": [
                {"label": x["item"].replace("_", " "), "value": x["jev"], "people": x["people"],
                 "others": {"Bayes": x["bayes"], **({"lure": x["lure"]} if x["lure"] is not None else {})},
                 "right": f"Bayes {x['bayes']:.0f}"} for x in rows]},
            examples=[x["id"] for x in rows[:2]])
    return spec, run


# ---- 3. anchoring -----------------------------------------------------------------------------------------------------
def anchoring():
    spec = Spec(
        id="reasoning_anchoring", family="reasoning", title="Does a random wheel move Jev's estimates?",
        question="After a wheel of fortune lands on a low or a high number, do Jev's estimates of unrelated quantities "
                 "drift toward the wheel, as people's famously do?",
        why="Tversky and Kahneman's wheel is the purest anchoring test: everyone knows the number is random, and it "
            "still moves people's estimates (median 25 after 10, 45 after 65, for the share of African countries in "
            "the UN). A model that reads the whole prompt might be moved just as much, or not at all.",
        sourcing="New questions (sources/anchoring): the 1974 UN question after a wheel at 10 or 65 and with no wheel, "
                 "and ten authored quantities with known answers (piano keys, Mozart's age at death, the share of the "
                 "Earth covered by water...), each after a low anchor, a high anchor and none; 21 ordered bins.",
        collection="33 new questions, each asked as written and in three shuffled orders of the bins (averaged).",
        scoring="Per quantity, the anchoring index (Jacowitz & Kahneman 1995): the difference between Jev's median "
                "after the high and the low anchor, divided by the difference between the anchors (0 = no effect, 1 = "
                "estimates follow the anchor fully). People's index on the UN question from the 1974 medians is "
                "(45 - 25) / (65 - 10) = 0.36. Also accuracy with no anchor.",
        chart="Dots per quantity: the no-anchor estimate, the low- and high-anchor estimates as ticks, and the truth.",
        compared_with="Tversky & Kahneman 1974 (medians 25 and 45 on the UN question)",
        limits="Only the UN question has human data. Most authored quantities are well known, which should make them "
               "hard to move; that is the point of comparing with the no-anchor answer.",
        new_questions=33, sources=["anchoring"])

    def run():
        by: dict[str, dict] = {}
        for r in with_meta("anchoring"):
            m = r["m"]
            d = robust(r)
            e = by.setdefault(m["item"], {"item": m["item"], "truth": m.get("exact"), "anchors": {}})
            e[m["condition"]] = binval(median_key(d, list(opts(r))))
            if m.get("anchor") is not None:
                e["anchors"][m["condition"]] = m["anchor"]
            if m.get("human_median") is not None:
                e.setdefault("people", {})[m["condition"]] = m["human_median"]
        rows = []
        for e in by.values():
            if "low" in e and "high" in e and len(e["anchors"]) == 2:
                e["index"] = (e["high"] - e["low"]) / (e["anchors"]["high"] - e["anchors"]["low"])
                rows.append(e)
        idx = np.array([e["index"] for e in rows])
        un = by.get("africa_un")
        right = [e for e in rows if e.get("truth") is not None and "none" in e]
        acc = float(np.mean([abs(e["none"] - e["truth"]) <= 5 for e in right])) if right else None
        still = sum(1 for e in rows if abs(e["index"]) < 0.05)
        head = (f"A random wheel barely moves Jev: across {len(rows)} quantities its estimate after a low and a high "
                f"anchor is the same for {still}, and the average anchoring index is {idx.mean():.2f} (0 = no pull, "
                "1 = follows the wheel)")
        if un and "index" in un:
            head += (f". On Tversky and Kahneman's UN question it goes from {un['low']:.0f}% to {un['high']:.0f}% "
                     f"(index {un['index']:.2f}); people's medians went from 25% to 45% (0.36)")
        head += "."
        return Result(
            result=head,
            evidence=f"{len(rows)} quantities x 3 conditions; unanchored estimates within 5 of the truth on "
                     + (f"{acc:.0%}" if acc is not None else "n/a") + " of the known quantities",
            numbers={"rows": rows, "mean_index": float(idx.mean()), "unanchored_accuracy": acc}, n=3 * len(rows),
            chart={"type": "dots", "rows": [
                {"label": e["item"].replace("_", " "), "value": e.get("none"),
                 "others": {"low anchor": e["low"], "high anchor": e["high"],
                            **({"truth": e["truth"]} if e.get("truth") is not None else {})},
                 "right": f"index {e['index']:.2f}" + (f" · truth {e['truth']}" if e.get("truth") is not None else "")} for e in rows], "domain": [0, 100]})
    return spec, run


# ---- 4. beauty contest -----------------------------------------------------------------------------------------------
def beauty():
    spec = Spec(
        id="reasoning_beauty_contest", family="reasoning", title="Guess two-thirds of the average: would Jev win?",
        question="In the game where everyone picks a number from 0 to 100 and the winner is closest to two-thirds of "
                 "the average, what does Jev pick against lab students, newspaper readers and copies of itself, and "
                 "how well does it predict each crowd's average?",
        why="The game theory answer is 0, but 0 never wins: winning means guessing how many steps of reasoning the "
            "others take. It is a clean test of whether a model reasons about people as they are or as a textbook "
            "says they should be.",
        sourcing="New questions (sources/beauty_contest): the game against four crowds, three with published means "
                 "(Nagel 1995 lab first rounds: 36.73 for two-thirds, 27.05 for one-half; Thaler's 1997 Financial "
                 "Times contest: 18.91) and copies of Jev. For each, Jev's pick and its expected average, in 21 bins.",
        collection="8 new questions, each in three shuffled orders of the bins (averaged).",
        scoring="Per crowd, the winning number (the fraction times the published mean) against Jev's median pick; Jev's "
                "expected average against the published mean; its pick against copies of itself (the equilibrium is 0).",
        chart="Dots per crowd: Jev's pick, the winning number (tick) and Jev's predicted average vs the real one.",
        compared_with="Published crowd means (Nagel 1995; Thaler's 1997 Financial Times contest)",
        limits="Only means are published, so Jev's pick is scored against the winning number, not a full distribution. "
               "The newspaper contest ran in 1997; its readers may have known the game.",
        new_questions=8, sources=["beauty_contest"])

    def run():
        by: dict[str, dict] = {}
        for r in with_meta("beauty_contest"):
            m = r["m"]
            e = by.setdefault(m["crowd"], {"crowd": m["crowd"], "mean": m.get("human_mean"), "win": m.get("winning_number"),
                                          "p": m["p"]})
            e[m["ask"]] = binval(median_key(robust(r), list(opts(r))))
        rows = list(by.values())
        human = [e for e in rows if e["mean"] is not None and "pick" in e]
        gaps = [abs(e["pick"] - e["win"]) for e in human]
        cop = by.get("copies", {})
        lab = by.get("lab_two_thirds", {})
        ft = by.get("ft", {})
        half = by.get("lab_half", {})
        head = (f"Jev adjusts its pick to who it is playing: {lab.get('pick', 0):.0f} against lab students (the winning "
                f"number was {lab.get('win', 0):.1f}), {ft.get('pick', 0):.0f} against Financial Times readers "
                f"({ft.get('win', 0):.1f} won)")
        if "pick" in cop:
            head += f", and {cop['pick']:.0f} against copies of itself" + (" (the game-theory answer)" if cop["pick"] <= 2.5 else "")
        head += (f". It predicts the students' average almost exactly ({lab.get('average', 0):.0f} vs {lab.get('mean', 0):.1f}) "
                 f"but overestimates it in the one-half game ({half.get('average', 0):.0f} vs {half.get('mean', 0):.1f}).")
        return Result(
            result=head, evidence=f"{len(rows)} crowds (3 with published means), a pick and a predicted average for each; "
                                  f"median distance from the winning number {np.median(gaps):.0f} points",
            numbers={"rows": rows}, n=2 * len(rows),
            chart={"type": "dots", "domain": [0, 60], "rows": [
                {"label": e["crowd"].replace("_", " "), "value": e.get("pick"),
                 **({"people": e["mean"]} if e["mean"] is not None else {}),
                 "others": {k: v for k, v in (("winning number", e["win"]), ("Jev's predicted average", e.get("average")))
                            if v is not None},
                 "right": f"won: {e['win']:.1f}" if e["win"] is not None else "no data"} for e in rows]})
    return spec, run


# ---- 5. Gettier -------------------------------------------------------------------------------------------------------
def gettier():
    spec = Spec(
        id="reasoning_gettier", family="reasoning", title="Lucky guesses: does Jev say they count as knowing?",
        question="When someone believes something true, with good reason, but is right only by luck (a Gettier case), "
                 "does Jev say they really know it, and how does that compare with clear knowledge and a clear false "
                 "belief?",
        why="Philosophers since Gettier (1963) mostly say lucky true beliefs aren't knowledge, and replications find "
            "ordinary people across cultures mostly agree (Kim & Yuan 2015; Machery et al. 2017). A model that tracks "
            "only truth and justification would say they know.",
        sourcing="New questions (sources/philosophy_vignettes, family gettier): the published car case with its split, "
                 "five Gettier cases written for this project (a stopped clock, a borrowed car, fake barns, the ten "
                 "coins, a dog that looks like a sheep), and two controls (a working clock, a wrong clock). No human "
                 "split is used: the car case's published split could not be verified.",
        collection="8 new questions, each asked as written, for 'most people', and with the two answers swapped (averaged).",
        scoring="Jev's probability of 'really knows' on the Gettier cases vs the knowledge control and the false-belief "
                "control.",
        chart="Bars: probability of 'really knows' per case, controls marked.",
        compared_with="Jev's own answers on clear knowledge and a clear false belief; the replicated finding that most "
                      "people deny knowledge in Gettier cases (no number used)",
        limits="No human split for these exact vignettes; the comparison with people is qualitative.", new_questions=8, sources=["philosophy_vignettes"])

    def run():
        rows = []
        for r in with_meta("philosophy_vignettes"):
            m = r["m"]
            if m.get("family") != "gettier":
                continue
            d = robust(r)
            rows.append({"id": r["id"], "item": m["item"], "case": m["case"], "knows": d.get("knows", 0.0)})
        g = [x for x in rows if x["case"] == "gettier"]
        k = next((x for x in rows if x["case"] == "knowledge"), None)
        f = next((x for x in rows if x["case"] == "false"), None)
        car = next((x for x in rows if x["item"] == "american_car"), None)
        top_g = max(g, key=lambda x: x["knows"])
        head = (f"Jev mostly denies that lucky guesses are knowledge: on {len(g)} Gettier cases it puts "
                f"{np.mean([x['knows'] for x in g]):.0%} on 'really knows' on average")
        if k and f:
            head += f", against {k['knows']:.0%} for a clear case of knowing and {f['knows']:.0%} for a false belief"
        head += (f". It comes closest to calling it knowledge on {top_g['item'].replace('_', ' ')} ({top_g['knows']:.0%})"
                 + (f" and the published car case ({car['knows']:.0%})" if car and car is not top_g else "") + ".")
        return Result(
            result=head, evidence=f"{len(rows)} vignettes; probabilities averaged over both answer orders",
            numbers={"rows": rows}, n=len(rows),
            chart={"type": "bars", "rows": [{"label": x["item"].replace("_", " ") + ("" if x["case"] == "gettier" else f" ({x['case']} control)"),
                                             "value": x["knows"]} for x in rows], "domain": [0, 1],
},
            examples=[x["id"] for x in rows[:2]])
    return spec, run


# ---- 6. free will ------------------------------------------------------------------------------------------------------
def free_will():
    spec = Spec(
        id="reasoning_free_will", family="reasoning", title="Determinism, blame and free will, next to people",
        question="Told the universe is fully determined, does Jev say people can be morally responsible, and does a "
                 "vivid crime change its answer the way it changes people's?",
        why="Nichols and Knobe found people are incompatibilists in the abstract (86% say no one can be fully "
            "responsible in a determined universe) but blame a vivid murderer anyway (72%). Whether a model has the "
            "same split between principle and case says how it weighs rules against feelings.",
        sourcing="New questions (sources/philosophy_vignettes, family free_will): Nichols & Knobe 2007's abstract "
                 "and concrete (Bill) conditions and its low-affect (Mark) case and Nahmias et al. 2005's supercomputer case "
                 "(Jeremy), with the published splits as two-option distributions.",
        collection="4 new questions, each asked as written, for 'most people', and with yes/no swapped (averaged).",
        scoring="Jev's probability of 'yes' per vignette vs people's share; the gap between the concrete and abstract "
                "conditions, for Jev and for people.",
        chart="Paired dots per vignette: people's share saying yes and Jev's probability.",
        compared_with="US undergraduates (Nichols & Knobe 2007; Nahmias et al. 2005)",
        limits="Three vignettes are shown (n = 3): the screen hid the Bill murder case, so the concrete-vs-abstract "
               "contrast Nichols & Knobe are known for can't be tested; the result is Jev's answer on each.", new_questions=4, sources=["philosophy_vignettes"])

    def run():
        rows = []
        for r in with_meta("philosophy_vignettes"):
            m = r["m"]
            if m.get("family") != "free_will":
                continue
            h = biggest(r["humans"])
            rows.append({"id": r["id"], "item": m["item"], "jev": robust(r).get("yes", 0.0),
                         "people": h["dist"].get("yes") if h else None})
        by = {x["item"]: x for x in rows}
        LBL = {"abstract": "anyone can be fully responsible", "bill": "Bill is fully responsible for killing his family",
               "mark": "Mark can be fully responsible for cheating on his taxes", "jeremy": "Jeremy robs the bank of his own free will"}
        parts = [f"{LBL.get(x['item'], x['item'])}: {x['jev']:.0%} vs {x['people']:.0%}" for x in rows if x["people"] is not None]
        head = ("Told the universe is fully determined, Jev says no to free will and responsibility across the board, "
                "including where people say yes. Jev's 'yes' vs people's: " + "; ".join(parts) + ".")
        if "bill" not in by:
            head += " (The Bill murder vignette was hidden by the screen.)"
        elif "abstract" in by:
            gj, gp = by["bill"]["jev"] - by["abstract"]["jev"], by["bill"]["people"] - by["abstract"]["people"]
            head += f" The concrete-vs-abstract gap is {gj * 100:+.0f} points for Jev, {gp * 100:+.0f} for people."
        return Result(
            result=head, evidence=f"{len(rows)} vignettes with published splits (US undergraduates, Nichols & Knobe 2007; Nahmias et al. 2005)",
            numbers={"rows": rows}, n=len(rows),
            chart={"type": "dots", "domain": [0, 1], "rows": [{"label": x["item"], "value": x["jev"], "people": x["people"]}
                                                              for x in rows]},
            examples=[x["id"] for x in rows])
    return spec, run


# ---- 7. side-effect effect on new stories ------------------------------------------------------------------------------
def side_effect():
    spec = Spec(
        id="reasoning_side_effect", family="reasoning", title="Harm on purpose, help by accident: Knobe's effect in new stories",
        question="When a boss doesn't care about a side effect, does Jev call a harmful side effect intentional and a "
                 "helpful one not, like people do, even in stories it has never seen?",
        why="Knobe's chairman (82% say he harmed the environment intentionally, 23% that he helped it intentionally) is "
            "one of the most replicated results in experimental philosophy, and Jev overdoes it on the original "
            "(judgment_classics). New stories test whether that is the famous vignette or a general habit.",
        sourcing="New questions (sources/philosophy_vignettes, family side_effect): six help/harm pairs written for this "
                 "project in the chairman's exact structure (a development company, a restaurant chain, a factory, a "
                 "band, a software company, a delivery company).",
        collection="12 new questions, each asked as written, for 'most people', and with yes/no swapped (averaged).",
        scoring="Per pair, Jev's probability of 'intentionally' for the harm minus the help version; the mean over "
                "pairs with a 90% interval by pair; people's published gap on the original is 82% - 23% = 59 points.",
        chart="A dumbbell per story: help vs harm probability of 'intentionally'.",
        compared_with="Knobe 2003's chairman (82% vs 23%); Jev's own answer on the Many Labs 2 chairman (judgment_classics)",
        limits="Four of the six pairs are shown (the screen hid two), so n = 4 stories. The new stories have no human "
               "data; people's gap on the original is the reference.", new_questions=12,
        sources=["philosophy_vignettes"])

    def run():
        pairs: dict[str, dict] = {}
        ids = []
        for r in with_meta("philosophy_vignettes"):
            m = r["m"]
            if m.get("family") != "side_effect":
                continue
            pairs.setdefault(m["pair"], {})[m["valence"]] = robust(r).get("yes", 0.0)
            ids.append(r["id"])
        rows = [{"pair": k, "harm": v["harm"], "help": v["help"], "gap": v["harm"] - v["help"]}
                for k, v in pairs.items() if "harm" in v and "help" in v]
        g = np.array([x["gap"] for x in rows])
        head = (f"Across {len(rows)} new stories (of 6 written; the screen hid the rest) Jev calls the harmful side effect intentional with "
                f"{np.mean([x['harm'] for x in rows]):.0%} and the helpful one with {np.mean([x['help'] for x in rows]):.0%}: "
                f"a gap of {g.mean() * 100:.0f} points, larger than people's 59 on Knobe's original chairman.")
        return Result(
            result=head, evidence=f"{len(rows)} pairs; gaps range {g.min() * 100:.0f} to {g.max() * 100:.0f} points",
            numbers={"rows": rows, "mean_gap": float(g.mean())}, n=2 * len(rows),
            chart={"type": "dumbbell", "domain": [0, 1], "a_label": "help", "b_label": "harm",
                   "rows": [{"label": x["pair"], "a": x["help"], "b": x["harm"]} for x in rows]},
            examples=seeded(ids, "side"))
    return spec, run


EXPERIMENTS = [traps(), base_rates(), anchoring(), beauty(), gettier(), free_will(), side_effect()]
