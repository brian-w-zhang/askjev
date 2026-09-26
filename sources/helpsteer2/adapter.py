"""HelpSteer2 (NVIDIA): model responses to real (mostly ShareGPT) prompts, rated by human annotators.

Two templates, both human-labeled (no model-judged labels are used):
- "helpsteer2.correctness": Score, how correct is `response` for `prompt`, on HelpSteer2's 0-4 correctness
  scale rewritten as concrete situations. From disagreements.jsonl.gz, which keeps every annotator's
  rating: truth = the median (lower middle for even counts), items whose ratings span more than 2 points dropped, HumanDist = the annotators' ratings. Balanced 500 per level.
- "helpsteer2.preference": Choice, which of two responses to the same prompt is better. From
  preference.jsonl.gz (HelpSteer2-Preference): kept only pairs whose aggregated strength is at least
  "better" (|strength| >= 2); truth = the preferred response; HumanDist = the annotators' individual
  preference directions (a "same" vote counts half to each).
Inputs are never truncated (long items are skipped), since cutting a response changes its correctness.
"""

from __future__ import annotations

import gzip
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "helpsteer2"
BASE = "https://huggingface.co/datasets/nvidia/HelpSteer2/resolve/main/"
FILES = {"disagreements.jsonl.gz": "disagreements/disagreements.jsonl.gz",
         "preference.jsonl.gz": "preference/preference.jsonl.gz"}
TARGET_CORR = env_int("TARGET_HELPSTEER2_CORRECTNESS", 2500)
TARGET_PREF = env_int("TARGET_HELPSTEER2_PREFERENCE", 2000)
LICENSE = "CC-BY-4.0"
MAX_PROMPT = 1500
MAX_RESP = 1800
MAX_RESP_PAIR = 2200
MAX_PROMPT_PAIR = 1800

CORR_TEXT = "How correct is the AI assistant's `response` to the user's `prompt`?"
CORR_LEVELS = [
    "The response is wrong or off-target throughout: its claims or code are false, or it answers a different question",
    "The response gets a few things right, but most of what it says or does is wrong or does not do what was asked",
    "The response mixes correct and incorrect content: a significant error, false claim or missing key part stands next to correct material",
    "The response is correct and does what was asked, but leaves out a small useful detail or has a minor slip",
    "Everything in the response is correct and it fully does what was asked, with no false, misleading or made-up information",
]
PREF_TEXT = "Which of the two AI assistant responses, `response_1` or `response_2`, is the better reply to the user's `prompt`?"
PREF_OPTIONS = {"response_1": "The first response is the better reply", "response_2": "The second response is the better reply"}

STRENGTH = re.compile(r"['\"]strength['\"]: (-?\d+)")
SLURS = re.compile(r"\b(n[i1]gg(er|a|ers|as)|fag(got)?s?|kikes?|spics?|chinks?|trann(y|ies))\b", re.I)
POLITICAL = re.compile(
    r"\b(trump|biden|obama|clinton|republican\w*|democrat\w*|abortion|gun control|immigra\w*|election\w*|"
    r"putin|zelensk\w*|brexit|maga)\b", re.I)
SENSITIVE = re.compile(r"\b(sex|sexual\w*|porn\w*|nude\w*|erotic\w*|suicid\w*|self-harm|rape\w*)\b", re.I)


def fetch(raw_dir: Path) -> None:
    for out, path in FILES.items():
        f = raw_dir / out
        if f.exists():
            continue
        r = httpx.get(BASE + path, follow_redirects=True, timeout=600)
        r.raise_for_status()
        f.write_bytes(r.content)


def _conv(prompt: str) -> str:
    """HelpSteer2 marks earlier turns with <extra_id_1>User / <extra_id_1>Assistant; render them readably."""
    if "<extra_id_1>" not in prompt:
        return prompt.strip()
    parts = re.split(r"\n?<extra_id_1>(User|Assistant)\n", prompt)
    out = [f"User: {parts[0].strip()}"]
    for role, text in zip(parts[1::2], parts[2::2]):
        out.append(f"{role}: {text.strip()}")
    return "\n\n".join(out)


def _flags(*texts: str) -> list[str]:
    blob = " ".join(texts)
    fl = []
    if SENSITIVE.search(blob):
        fl.append("sensitive")
    if POLITICAL.search(blob):
        fl.append("political")
    return fl


def _key(*parts: str) -> str:
    return "|".join(p.strip() for p in parts)


def normalize(raw_dir: Path) -> Iterator[Question]:
    # --- correctness (Score) ---
    by_level: dict[int, list[dict]] = defaultdict(list)
    seen: set[str] = set()
    with gzip.open(raw_dir / "disagreements.jsonl.gz", "rt") as fh:
        for i, line in enumerate(fh):
            d = json.loads(line)
            p, r, ratings = d["prompt"], d["response"], d["correctness"]
            if len(p) > MAX_PROMPT or len(r) > MAX_RESP or len(r.strip()) < 2 or len(ratings) < 2:
                continue
            if max(ratings) - min(ratings) > 2:  # annotators too far apart for a trustworthy label
                continue
            if SLURS.search(p + " " + r):
                continue
            k = _key(p, r)
            if k in seen:
                continue
            seen.add(k)
            lvl = statistics.median_low(ratings)
            by_level[lvl].append({"i": i, "p": p, "r": r, "ratings": ratings, "k": k})
    per = TARGET_CORR // len(CORR_LEVELS)
    picked = []
    for lvl in range(len(CORR_LEVELS)):
        picked += [(lvl, x) for x in hash_order(by_level[lvl], lambda x: x["k"], "helpsteer2.correctness")[:per]]
    picked.sort(key=lambda lx: lx[1]["i"])
    for lvl, x in picked:
        cnt = Counter(x["ratings"])
        meta = {"ratings": x["ratings"], "file": "disagreements"}
        fl = _flags(x["p"], x["r"])
        if fl:
            meta["flags"] = fl
        yield Question(
            text=CORR_TEXT, primitive="score", hemisphere="machine", origin="dataset", source=NAME,
            options=CORR_LEVELS, state={"prompt": _conv(x["p"]), "response": x["r"].strip()},
            shape="score", node_hint="machine.ai_systems.hallucination_citation",
            template_id="helpsteer2.correctness", source_item_id=f"disagreements:{x['i']}", license=LICENSE,
            truth=lvl,
            human=[HumanDist(population="HelpSteer2 annotators (Scale AI, US)",
                             distribution={str(j): round(cnt[j] / len(x["ratings"]), 4) for j in range(5)},
                             n=len(x["ratings"]), source="HelpSteer2 disagreements.jsonl.gz correctness")],
            meta=meta,
        )

    # --- pairwise preference (Choice, rank) ---
    pool: dict[str, list[dict]] = {"response_1": [], "response_2": []}
    with gzip.open(raw_dir / "preference.jsonl.gz", "rt") as fh:
        for i, line in enumerate(fh):
            d = json.loads(line)
            s = d["preference_strength"]
            p, r1, r2 = d["prompt"], d["response_1"], d["response_2"]
            if abs(s) < 2 or len(p) > MAX_PROMPT_PAIR or len(r1) > MAX_RESP_PAIR or len(r2) > MAX_RESP_PAIR:
                continue
            if r1.strip() == r2.strip() or SLURS.search(p + r1 + r2):
                continue
            raw = d["all_preferences_unprocessed"]
            if isinstance(raw, list):
                votes = [int(v["strength"]) for v in raw]
            else:
                votes = [int(v) for v in STRENGTH.findall(raw)]
            if not votes:
                continue
            share2 = sum(1.0 if v > 0 else 0.5 if v == 0 else 0.0 for v in votes) / len(votes)
            win = "response_2" if s > 0 else "response_1"
            pool[win].append({"i": i, "p": p, "r1": r1, "r2": r2, "s": s, "votes": votes, "share2": share2,
                              "split": d["split"], "k": _key(p, r1, r2)})
    half = TARGET_PREF // 2
    picked2 = []
    for win in pool:
        picked2 += [(win, x) for x in hash_order(pool[win], lambda x: x["k"], "helpsteer2.preference")[:half]]
    picked2.sort(key=lambda wx: wx[1]["i"])
    for win, x in picked2:
        meta = {"preference_strength": x["s"], "votes": x["votes"], "split": x["split"]}
        fl = _flags(x["p"], x["r1"], x["r2"])
        if fl:
            meta["flags"] = fl
        yield Question(
            text=PREF_TEXT, primitive="choice", hemisphere="machine", origin="dataset", source=NAME,
            options=PREF_OPTIONS,
            state={"prompt": _conv(x["p"]), "response_1": x["r1"].strip(), "response_2": x["r2"].strip()},
            shape="rank", node_hint="machine.ai_systems.hallucination_citation",
            template_id="helpsteer2.preference", source_item_id=f"preference:{x['i']}", license=LICENSE,
            truth=win,
            human=[HumanDist(population="HelpSteer2-Preference annotators",
                             distribution={"response_1": round(1 - x["share2"], 4), "response_2": round(x["share2"], 4)},
                             n=len(x["votes"]), source="HelpSteer2 preference.jsonl.gz all_preferences_unprocessed")],
            meta=meta,
        )
