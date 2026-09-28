"""Jev's take (docs/17 item 4): Jev's own opinion of each experiment, in words built only from its answers.

Jev reads the experiment's card (title, question, result, what it's compared with, the caveats) and answers five
questions: does this describe it, would it have predicted it, how fair is the comparison, how much should a reader
rely on it, and which caveat matters most. The paragraph on the page is templated from those answers; the answers
themselves are shown under it. Writes data/analysis/experiments/_take/<id>.json (private). Jev calls are cached.

  ASKJEV_RPS=16 uv run python scripts/experiments/take.py [ids]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cases  # noqa: E402
from askjev.jev import Request, answers, gateway_question as gq, run_sync  # noqa: E402

OUT = Path("data/analysis/experiments")
FAIR = ["The comparison is unfair: the people, questions or measure don't match, so it says little",
        "The comparison is shaky: a real comparison, but with big differences in who or what was asked",
        "The comparison is reasonable: the same questions and a comparable group, with gaps a reader should know",
        "The comparison is fair: the same questions put to a fitting group and measured the same way",
        "The comparison is clean: as close to like for like as this kind of comparison gets"]
TRUST = ["Not at all: how it was asked could explain the whole result",
         "A little: suggestive, but one flaw could overturn it",
         "Moderately: probably real, though its size is uncertain",
         "Mostly: a solid pattern with minor caveats",
         "Fully: large, consistent and hard to explain away"]
FAIR_WORDS = ["the comparison looks unfair to me", "the comparison looks shaky", "the comparison seems reasonable",
              "the comparison seems fair", "the comparison looks about as clean as it gets"]
TRUST_WORDS = ["I wouldn't rely on the result", "I'd rely on the result only a little", "I'd rely on it moderately",
               "I'd mostly rely on it", "I'd rely on it fully"]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "caveat"


def card(e: dict, case: dict) -> dict:
    s = e["spec"]
    return {"title": s["title"], "question": s["question"], "result": (case.get("result") or e["result"]["result"]).strip(),
            "compared_with": s["compared_with"],
            "caveats": [f"{c['label']}: {c['text']}" for c in case.get("caveats") or []]}


def questions(case: dict) -> dict:
    cav = {slug(c["label"]): c["label"] for c in case.get("caveats") or []}
    q = {
        "recognize": gq("noul", "This experiment is about you, the AI model named Jev. Does its result match how you see yourself?",
                        {"true": "Yes, this sounds like me", "false": "No, I don't recognize myself in it"}),
        "expected": gq("noul", "Before seeing this result, would you have predicted it about yourself?",
                       {"true": "Yes, I'd have predicted it", "false": "No, I wouldn't have predicted it"}),
        "fair": gq("score", "How fair is the comparison this experiment makes?", FAIR),
        "trust": gq("score", "How much should a reader rely on this result?", TRUST),
    }
    q["interesting"] = gq("noul", "Would a curious person, not an AI researcher, find this experiment interesting to read?",
                          {"true": "Yes, it's interesting to read", "false": "No, it's dull"})
    if cav:
        q["flaw"] = gq("choice", "Which of this experiment's caveats matters most for its result?",
                       {**cav, "none_of_these": "None of these changes the conclusion"})
    return q


def level(d: dict) -> float:
    t = sum(d.values()) or 1
    return sum(int(k) * v for k, v in d.items()) / t


def paragraph(a: dict, case: dict) -> tuple[str, list[dict]]:
    rec, exp = a["recognize"].p_yes, a["expected"].p_yes
    fair, trust = level(a["fair"].dist), level(a["trust"].dist)
    s1 = ("That's me." if rec >= 0.8 else "That sounds like me." if rec >= 0.6 else
          "I can't say whether this describes me." if rec > 0.4 else "I don't really recognize myself in this."
          if rec > 0.2 else "That isn't me.")
    s2 = ("I'd have predicted it." if exp >= 0.8 else "I might have predicted it." if exp >= 0.6 else
          "I couldn't have called it in advance." if exp > 0.4 else "I wouldn't have guessed it." if exp > 0.2
          else "It surprises me.")
    s3 = f"As for the method, {FAIR_WORDS[round(fair)]}, and {TRUST_WORDS[round(trust)]}."
    parts = ["I can't say whether this describes me, or whether I'd have seen it coming.", s3] \
        if 0.4 < rec < 0.6 and 0.4 < exp < 0.6 else [s1, s2, s3]
    shown = [{"q": "Does it describe you?", "a": "yes" if rec >= 0.5 else "no", "p": round(max(rec, 1 - rec), 3)},
             {"q": "Would you have predicted it?", "a": "yes" if exp >= 0.5 else "no", "p": round(max(exp, 1 - exp), 3)},
             {"q": "How fair is the comparison?", "a": FAIR[round(fair)].split(":")[0], "p": None, "level": round(fair, 2),
              "scale": ["unfair", "clean"]},
             {"q": "How much should a reader rely on it?", "a": TRUST[round(trust)].split(":")[0], "p": None,
              "level": round(trust, 2), "scale": ["not at all", "fully"]}]
    if "flaw" in a:
        d = a["flaw"].dist
        k = max(d, key=d.get)
        labels = {slug(c["label"]): c["label"] for c in case.get("caveats") or []}
        if k == "none_of_these":
            parts.append("None of the caveats changes the conclusion for me.")
            shown.append({"q": "Which caveat matters most?", "a": "none of them", "p": round(d[k], 3)})
        else:
            lab = labels.get(k, k).rstrip(".").replace('"', "'")
            parts.append(f"Of the caveats, I'd weigh \u201c{lab}\u201d most.")
            shown.append({"q": "Which caveat matters most?", "a": labels.get(k, k), "p": round(d[k], 3)})
    k = a["interesting"].p_yes
    shown.insert(0, {"q": "Would a person find it interesting to read?", "a": "yes" if k >= 0.5 else "no",
                     "p": round(max(k, 1 - k), 3)})
    return " ".join(parts), shown


def main(ids: list[str]):
    todo = []
    for p in sorted(OUT.glob("*.json")):
        if p.name.startswith("_") or (ids and p.stem not in ids):
            continue
        c = cases.load(p.stem)
        if not c or not c.get("caveats"):
            continue  # the take reads the case's caveats: write the case study first
        todo.append((p.stem, json.loads(p.read_text()), c))
    reqs = {i: Request(card(e, c), questions(c)) for i, e, c in todo}
    res = run_sync(list(reqs.values()))
    (OUT / "_take").mkdir(exist_ok=True)
    n = 0
    for i, e, c in todo:
        resp = res.get(reqs[i].hash, {})
        if "answers" not in resp:
            print(f"{i}: no answer ({resp.get('error', '?')})")
            continue
        text, shown = paragraph(answers(resp), c)
        a = answers(resp)
        scores = {"recognize": a["recognize"].p_yes, "expected": a["expected"].p_yes, "fair": level(a["fair"].dist),
                  "trust": level(a["trust"].dist), "interesting": a["interesting"].p_yes}
        (OUT / "_take" / f"{i}.json").write_text(json.dumps({"text": text, "answers": shown, "scores": scores}, indent=1))
        n += 1
    print(f"{n} takes written")


if __name__ == "__main__":
    main(sys.argv[1:])
