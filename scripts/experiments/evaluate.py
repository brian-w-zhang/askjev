"""The Jev self-evaluator for experiments (docs/16-experiments-plan.md, pass 1; docs/experiments/evaluator.md).

Jev reads a short card about an experiment and answers three kinds of question:
  verdict   Choice over ten situations, from "wrong" to "headline"
  interest  Score, ten levels from "a reader skips it" to "a reader shares it tonight"
  checks    Noul: fair comparison, real human baseline, possible artifact, plain enough to read once
Code, not the words alone, turns those into keep / atlas / rework / cut (`decide`).

Modes:
  uv run python scripts/experiments/evaluate.py old        # the 372 old findings (baseline)
  uv run python scripts/experiments/evaluate.py gold       # the gold set, plus stability under reordering
  uv run python scripts/experiments/evaluate.py meta       # label-to-number mapping (the evaluator of the evaluator)
  uv run python scripts/experiments/evaluate.py new        # every experiment result in data/analysis/experiments/
Jev calls are cached by request hash; re-running re-reads the cache.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from askjev.jev import Request, answers, gateway_question as gq, run_sync

A = Path("data/analysis")
OUT = A / "experiments"
VERSION = "v3"  # bump when the card or options change; results keep the version they were made with

# The ten verdicts, each a situation (01-jev.md §7), with the value code uses. Order here is the order Jev sees.
VERDICTS = {
    "wrong": ("The result is wrong, or the numbers can't mean what the sentence says.", 0),
    "trivial": ("True, but anyone would have guessed it before seeing the data.", 1),
    "duplicate": ("It says the same thing as a more basic, better-known result.", 1),
    "noise": ("The effect is within noise, or the sample is too small to trust.", 2),
    "muddled": ("Something real is there, but the way it's framed hides it or confuses the reader.", 3),
    "needs_data": ("Promising, but it needs better or more data before it says anything.", 4),
    "solid_dull": ("Sound and accurate, but only a specialist would care.", 5),
    "atlas": ("Worth keeping in a reference collection for people who dig into details.", 6),
    "portrait": ("A curious person scrolling past would stop, read it, and learn something about the model.", 8),
    "headline": ("People would share it: a surprising, clear, well-supported revelation about the model.", 10),
}
INTEREST = [
    "A reader would skip past it without noticing it",
    "A reader would glance at it and forget it within a minute",
    "A specialist might note it; everyone else would skim it",
    "A reader would read it once and not remember it tomorrow",
    "A reader would find it mildly informative",
    "A reader would stop and read the details",
    "A reader would still remember it the next day",
    "A reader would bring it up in a conversation",
    "A reader would send it to a friend",
    "A reader would be talking about it tonight and sharing it widely",
]
CHECKS = {
    "baseline": "Does this experiment compare the model with real human answers or a real answer key, not only with the model's own guesses?",
    "surprise": "Does the result tell you something specific about the model that you could not have predicted before reading it?",
    "jargon": "Does the result depend on internal labels, codes or jargon that a general reader would not understand?",
    "plain": "Could a curious non-expert understand the result after reading it once?",
}
INTRO = ("The state describes one experiment about Jev, an AI model that answers questions with a probability for "
         "every option. An experiment gathers many questions into one result.")


def card(e: dict) -> dict:
    """The state Jev reads: only what a reader would see, no ids."""
    keys = ("title", "question", "result", "evidence", "compared_with", "sourcing", "chart")
    return {k: e[k] for k in keys if e.get(k)}


def questions(e: dict, order: list[str] | None = None) -> dict:
    opts = {k: VERDICTS[k][0] for k in (order or list(VERDICTS))}
    q = {
        "verdict": gq("choice", f"{INTRO} Which description fits this experiment best?", opts),
        "interest": gq("score", f"{INTRO} How interesting is this experiment's result to a curious general reader?", INTEREST),
    }
    for k, text in CHECKS.items():
        q[k] = gq("noul", f"{INTRO} {text}")
    return q


def decide(v: dict) -> dict:
    """keep / atlas / rework / cut from Jev's answers (distributions, not just the top pick). Thresholds were set on the
    gold set (docs/experiments/evaluator.md): interest and verdict value rank experiments; a missing human baseline or
    unreadable jargon pushes a dull result out."""
    dist = v["verdict"]
    value = sum(p * VERDICTS[k][1] for k, p in dist.items() if k in VERDICTS)
    top = max(dist, key=dist.get)
    interest = 1 + sum(int(k) * p for k, p in v["interest"].items())  # levels 0-9 → 1-10
    base, surprise, jargon, plain = (v[k] for k in ("baseline", "surprise", "jargon", "plain"))
    if top in ("wrong", "duplicate") or value < 3.5 or (jargon >= 0.5 and interest < 5.5):
        outcome = "cut"
    elif top in ("muddled", "needs_data"):
        outcome = "rework"
    elif interest >= 5.5 and value >= 6 and jargon < 0.5:
        outcome = "keep"
    elif base < 0.35 and interest < 5:
        outcome = "cut"
    else:
        outcome = "atlas"
    return {"top": top, "value": round(value, 2), "interest": round(interest, 2), "baseline": round(base, 2),
            "surprise": round(surprise, 2), "jargon": round(jargon, 2), "plain": round(plain, 2), "outcome": outcome}


def evaluate(items: list[dict], order: list[str] | None = None) -> dict[str, dict]:
    reqs = {e["id"]: Request(card(e), questions(e, order)) for e in items}
    res = run_sync(list(reqs.values()))
    out = {}
    for eid, r in reqs.items():
        resp = res.get(r.hash, {})
        if "error" in resp or "answers" not in resp:
            out[eid] = {"error": resp.get("error", "no answers")}
            continue
        a = answers(resp)
        v = {"verdict": a["verdict"].dist, "interest": a["interest"].dist, **{k: a[k].p_yes for k in CHECKS}}
        out[eid] = {"raw": v, **decide(v)}
    return out


# ---- the old findings, as cards -----------------------------------------------------------------------------------
TIER_SOURCE = {"1": "published tests, real crowds or answer keys", "2": "questions written for this project, audited",
               "3": "themes gathered by embedding similarity", "discovery": "an automatic scan of topic-level averages",
               "corpus": "counts over the question corpus", "pipeline": "logs of how the corpus was built"}


def old_cards() -> list[dict]:
    L = json.loads((A / "findings.json").read_text())["claims"]
    cards = []
    for c in L:
        if c.get("section") == "page":
            continue
        ci = c.get("ci90")
        human = bool(c.get("people") or c.get("rho_people") or c["section"] in ("agreement", "scales") or c["id"].startswith(("bigfive", "humor", "risk", "mm_", "task_", "knowledge", "calibration")))
        cards.append({
            "id": c["id"],
            "title": c["section"].replace("_", " "),
            "result": c["sentence"],
            "evidence": f"{c['n']:,} questions" + (f"; 90% interval {ci[0]:.3g} to {ci[1]:.3g}" if ci else ""),
            "compared_with": "real people or an answer key" if human else "nothing outside the model, or only its own guess about people",
            "sourcing": TIER_SOURCE.get(str(c["tier"]), str(c["tier"])),
        })
    return cards


PAIR_Q = ("Each option is one experiment about Jev, an AI model. Which one teaches a curious general reader something more "
          "surprising and specific about how the model behaves, clearly stated and backed by a real comparison?")


def pairwise(items: list[dict], pairs_per_item: int | None = None, seed: int = 11) -> dict[str, float]:
    """Head-to-head interest: 'which of the two would a curious reader find more interesting?', each pair asked in
    both orders (position bias cancels). Bradley-Terry strengths on a log scale; higher is more interesting.
    All pairs for small sets; otherwise a random regular design with `pairs_per_item` opponents each."""
    ids = [e["id"] for e in items]
    byid = {e["id"]: e for e in items}
    rng = random.Random(seed)
    if pairs_per_item is None or len(ids) <= 2 * pairs_per_item:
        pairs = [(a, b) for i, a in enumerate(ids) for b in ids[i + 1:]]
    else:
        pairs = set()
        for _ in range(pairs_per_item // 2 + 1):
            order = ids[:]
            rng.shuffle(order)
            for a, b in zip(order, order[1:] + order[:1]):
                if a != b:
                    pairs.add(tuple(sorted((a, b))))
        pairs = sorted(pairs)
    q = gq("choice", PAIR_Q, {"first": "the first experiment", "second": "the second experiment"})
    reqs = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            reqs.append((x, y, Request({"first": card(byid[x]), "second": card(byid[y])}, {"pick": q})))
    res = run_sync([r for *_, r in reqs])
    wins: dict[tuple, float] = {}
    for x, y, r in reqs:
        resp = res.get(r.hash, {})
        if "answers" not in resp:
            continue
        d = answers(resp)["pick"].dist
        wins[(x, y)] = wins.get((x, y), 0) + d.get("first", 0)
        wins[(y, x)] = wins.get((y, x), 0) + d.get("second", 0)
    # Bradley-Terry by minorization-maximization on soft wins
    s = {i: 1.0 for i in ids}
    for _ in range(200):
        new = {}
        for i in ids:
            w = sum(v for (a, _), v in wins.items() if a == i)
            den = sum((wins.get((i, j), 0) + wins.get((j, i), 0)) / (s[i] + s[j]) for j in ids if j != i and ((i, j) in wins or (j, i) in wins))
            new[i] = (w + 0.1) / (den + 0.2 / s[i]) if den else s[i]
        g = sum(new.values()) / len(new)
        s = {i: v / g for i, v in new.items()}
    import math
    return {i: round(math.log(v), 3) for i, v in s.items()}


KEEP_AT, CUT_BELOW = 0.0, -3.0  # on the gold scale (docs/experiments/evaluator.md)


def evaluate_pool(items: list[dict], pairs_per_item: int = 12) -> dict[str, dict]:
    """The full evaluator: Jev's absolute answers (verdict, interest, checks) for the record, and the head-to-head
    ranking against the gold anchors, which decides. Strengths are shifted so the anchors sit where they sat in the
    gold tournament, so the cut-offs mean the same thing in every pool."""
    gold = json.loads((OUT / "_gold.json").read_text())["items"]
    gold_bt = json.loads((OUT / "_eval_gold_pairs.json").read_text())
    absolute = evaluate(items)
    anchors = [dict(g) for g in gold if g["id"] not in {e["id"] for e in items}]
    bt = pairwise(items + anchors, pairs_per_item=pairs_per_item)
    shift = sum(gold_bt[a["id"]] - bt[a["id"]] for a in anchors) / max(len(anchors), 1)
    out = {}
    for e in items:
        r = absolute.get(e["id"], {})
        strength = round(bt[e["id"]] + shift, 3)
        if r.get("top") in ("wrong", "duplicate"):
            outcome = "cut"
        elif r.get("top") in ("muddled", "needs_data") and strength < KEEP_AT:
            outcome = "rework"
        elif strength >= KEEP_AT:
            outcome = "keep"
        elif strength < CUT_BELOW:
            outcome = "cut"
        else:
            outcome = "atlas"
        out[e["id"]] = {**r, "absolute_outcome": r.get("outcome"), "strength": strength, "outcome": outcome}
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "old"
    OUT.mkdir(parents=True, exist_ok=True)
    if mode == "old":
        cards = old_cards()
        res = evaluate_pool(cards)
        (OUT / "_eval_old.json").write_text(json.dumps({"version": VERSION, "cards": {c["id"]: c for c in cards}, "eval": res}, indent=1))
        from collections import Counter
        print(len(res), "old findings:", Counter(r.get("outcome", "error") for r in res.values()))
    elif mode == "gold":
        gold = json.loads((OUT / "_gold.json").read_text())
        items = gold["items"]
        a = evaluate(items)
        order = list(VERDICTS)
        random.Random(7).shuffle(order)
        b = evaluate(items, order)
        (OUT / "_eval_gold.json").write_text(json.dumps({"version": VERSION, "base": a, "shuffled": b, "order": order}, indent=1))
        print(summarize_gold(items, a, b))
    elif mode == "gold_pairs":
        gold = json.loads((OUT / "_gold.json").read_text())
        bt = pairwise(gold["items"])
        (OUT / "_eval_gold_pairs.json").write_text(json.dumps(bt, indent=1))
        rank = {"cut": 0, "rework": 1, "atlas": 2, "keep": 3}
        import statistics as st
        for g in ("keep", "atlas", "rework", "cut"):
            xs = [bt[i["id"]] for i in gold["items"] if i["gold"] == g]
            print(g, len(xs), round(st.mean(xs), 2), round(min(xs), 2), round(max(xs), 2))
        from scipy.stats import spearmanr
        r = spearmanr([rank[i["gold"]] for i in gold["items"]], [bt[i["id"]] for i in gold["items"]])
        print("spearman with gold", round(r.statistic, 3))
    elif mode == "meta":
        print(json.dumps(meta(), indent=1))
    elif mode == "new":
        items = [json.loads(p.read_text())["card"] for p in sorted(OUT.glob("*.json")) if not p.name.startswith("_")]
        res = evaluate_pool(items)
        for it in items:
            p = OUT / f"{it['id']}.json"
            d = json.loads(p.read_text())
            d.setdefault("evaluations", []).append({"version": VERSION, **res[it["id"]]})
            d["evaluation"] = {"version": VERSION, **res[it["id"]]}
            p.write_text(json.dumps(d, indent=1, default=str))
        from collections import Counter
        print(len(res), "experiments:", Counter(r.get("outcome", "error") for r in res.values()))


def summarize_gold(items, a, b) -> str:
    """Agreement of Jev's outcome with the gold outcome, and stability under reordered options."""
    rank = {"cut": 0, "rework": 1, "atlas": 2, "keep": 3}
    n = exact = near = stable = 0
    rows = []
    for it in items:
        ra, rb = a.get(it["id"], {}), b.get(it["id"], {})
        if "outcome" not in ra:
            continue
        n += 1
        g, j = it["gold"], ra["outcome"]
        exact += g == j
        near += abs(rank[g] - rank[j]) <= 1
        stable += rb.get("outcome") == j
        rows.append((it["id"], g, j, ra["top"], ra["value"], ra["interest"]))
    lines = [f"gold n={n}: exact {exact}/{n}, within one step {near}/{n}, same outcome after reordering {stable}/{n}"]
    lines += [f"  {i:44s} gold={g:6s} jev={j:6s} top={t:11s} value={v:5.2f} interest={s:5.2f}" for i, g, j, t, v, s in rows if g != j]
    return "\n".join(lines)


def meta() -> dict:
    """Ask Jev what interest level each verdict label corresponds to, and compare with how they co-occur in its
    evaluations of the old findings and the gold set."""
    reqs = {k: Request({"verdict": desc},
                       {"m": gq("score", f"{INTRO} If an experiment fits the description in the state, how interesting is it "
                                          "to a curious general reader?", INTEREST)}) for k, (desc, _) in VERDICTS.items()}
    res = run_sync(list(reqs.values()))
    mapping = {}
    for k, r in reqs.items():
        a = answers(res[r.hash])["m"]
        mapping[k] = round(1 + sum(int(x) * p for x, p in a.dist.items()), 2)
    seen: dict[str, list] = {}
    for f in ("_eval_old.json", "_eval_gold.json"):
        p = OUT / f
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        ev = d.get("eval") or d.get("base") or {}
        for r in ev.values():
            if "top" in r:
                seen.setdefault(r["top"], []).append(r["interest"])
    observed = {k: round(sum(v) / len(v), 2) for k, v in seen.items() if v}
    out = {"stated": mapping, "observed_mean_interest_by_top_verdict": observed,
           "observed_n": {k: len(v) for k, v in seen.items()},
           "verdict_values": {k: v for k, (_, v) in VERDICTS.items()}}
    (OUT / "_eval_meta.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
