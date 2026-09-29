"""What Jev was asked to do, counted from the call logs (data/calls/**/*.jsonl, one line per gateway call).

Each call holds one or more questions; each question is sorted into a job by the words it sends Jev (the screen's
questions, a tree walk's "which topic area", an answer as asked or for "most people", the duplicate check, the
experiment evaluator...). Counts both calls (by the call's main job) and questions. Writes data/analysis/jev_jobs.json
(private), which story.py puts into the portrait's methods chapter. Reads only; no Jev calls.

  uv run python scripts/portrait/jev_jobs.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

LOGS = Path("data/calls")
OUT = Path("data/analysis/jev_jobs.json")

def job_of(key: str, q: dict) -> str:
    """A question's job, from its key suffix (screens and meta checks carry one) or the fixed words the pipeline sends;
    never from the question being judged, which sits in a separate field."""
    suf = key.rsplit("__", 1)[-1]
    ins = q.get("instructions")
    ask = ins.get("question", "") if isinstance(ins, dict) else str(ins or "")
    persp = ins.get("perspective", "") if isinstance(ins, dict) else ""
    if suf in ("f_political", "f_sensitive", "pol", "sens"):
        return "screen for politics and sensitive content"
    if suf == "f_weak":
        return "flag known weak spots"
    if suf.startswith("m_"):
        return "describe each question"
    if ask.startswith("How funny is this meme"):
        return "rate a meme"
    if ask.startswith("Each option is one experiment"):
        return "rank experiments head to head"
    if "experiment" in ask and ("Jev" in ask or "you" in ask or "reader" in ask or "caveat" in ask):
        return "judge an experiment"
    if "essentially the same question" in ask:
        return "check for duplicates"
    if "which topic area" in ask.lower():
        return "place a question on the tree"
    if "best matches the search" in ask:
        return "rerank search results"
    if "opinions about or are curious about" in ask:
        return "prune topics"
    if "most people" in persp or "most people" in ask[:0]:
        return "answer for most people"
    return "answer as asked"


def scan(path: str) -> tuple[Counter, Counter, Counter]:
    calls, qs, other = Counter(), Counter(), Counter()
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("repeat"):
                continue  # a cached re-read, not a new call
            qq = (d.get("request") or {}).get("questions") or {}
            jobs = Counter(job_of(k, v) for k, v in qq.items())
            if not jobs:
                continue
            calls[jobs.most_common(1)[0][0]] += 1
            qs.update(jobs)
            for k, v in qq.items():
                if job_of(k, v) == "answer as asked" and "__" in k:
                    other[k.rsplit("__", 1)[-1][:30]] += 1
    return calls, qs, other


def main():
    files = sorted(str(p) for p in LOGS.rglob("*.jsonl"))
    calls, qs, other = Counter(), Counter(), Counter()
    with ProcessPoolExecutor(max_workers=8) as ex:
        for c, q, o in ex.map(scan, files, chunksize=4):
            calls.update(c); qs.update(q); other.update(o)
    out = {"calls": dict(calls.most_common()), "questions": dict(qs.most_common()), "files": len(files),
           "n_calls": sum(calls.values()), "n_questions": sum(qs.values())}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print("key suffixes filed under 'answer as asked' (check these):", other.most_common(25))


if __name__ == "__main__":
    main()
