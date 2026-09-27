"""Portrait: "Jev at work", the pipeline section (docs/11-portrait.md). Jev built its own map: it walked the tree to
place questions, screened content, judged duplicates, filtered authored banks by a blind round trip, and answered
every question several ways. These claims come from the placements, question_links, calls tables and the round-trip
logs, and are appended to data/analysis/findings.json (replacing earlier pipeline claims). No Jev calls.

  uv run python scripts/portrait/pipeline.py      # after findings.py / landscape.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from askjev import db

A = Path("data/analysis")
LOGS = Path("data/logs")


def main():
    claims = []

    def add(cid, sentence, n, effect, **extra):
        claims.append({"id": cid, "section": "pipeline", "sentence": sentence, "tier": "pipeline", "n": int(n),
                       "effect": effect, "ci90": None, "examples": [], "script": "scripts/portrait/pipeline.py", **extra})

    with db.connect() as c:
        latest = c.execute("""select method, count(*) n from (select distinct on (question_id) question_id, method
                               from placements order by question_id, created_at desc) t group by 1 order by 2 desc""").fetchall()
        calls = c.execute("""select count(*) n, percentile_cont(0.5) within group (order by latency_ms) med,
                                    min(created_at) t0, max(created_at) t1 from calls""").fetchone()
        dups = c.execute("select count(*) n from question_links where type='duplicate'").fetchone()["n"]
        total = c.execute("select count(*) n from questions").fetchone()["n"]
        unflag = c.execute("select count(*) n from questions where meta ? 'unflagged'").fetchone()["n"]
        mm = c.execute("select count(*) n from questions where meta ? 'unflagged' and source='moral_machine'").fetchone()["n"]
    by = {r["method"]: r["n"] for r in latest}
    walked = by.get("jev", 0) + by.get("jev_fast", 0)
    add("pipeline_flow", "Jev screened every question, answered it several ways and checked it for duplicates; "
        f"{by.get('jev', 0) + by.get('jev_fast', 0):,} it also placed on the map itself by walking the topic tree.", total, None,
        steps=["place (walk the tree)", "screen (politics, sensitive content)", "answer (as asked, 'most people', reordered, reversed)",
               "dedupe (same question?)", "authored only: blind round trip back to the intended topic"])
    add("pipeline_placement", f"Jev walked the topic tree for {walked:,} questions itself (full walk {by.get('jev', 0):,}, fast walk "
        f"{by.get('jev_fast', 0):,}); the rest were filed by their source's own labels or when a crowded topic split.",
        sum(by.values()), walked, methods=by, routing_eval="91.6% to the right branch on a 332-question held-out set (docs/routing-eval.md)")
    banks = []
    for p in sorted(LOGS.glob("authored*.log")):
        bank = None  # the bank a result belongs to is the last "round trip: authored/<bank>.jsonl" line before it
        for line in p.read_text().splitlines():
            if (b := re.search(r"round trip: authored/(\S+)\.jsonl", line)):
                bank = b.group(1)
            elif (m := re.search(r"G5: (\d+) ingested, (\d+) rejected by round trip", line)):
                banks.append({"log": p.name, "bank": bank or p.stem, "kept": int(m.group(1)), "rejected": int(m.group(2))})
    agg: dict[str, dict] = {}  # a bank can be run more than once (resumed runs)
    for b in banks:
        a = agg.setdefault(b["bank"], {"bank": b["bank"], "log": b["log"], "kept": 0, "rejected": 0})
        a["kept"] += b["kept"]
        a["rejected"] += b["rejected"]
    banks = [{**a, "rate": round(100 * a["kept"] / max(a["kept"] + a["rejected"], 1))} for a in agg.values()]
    kept, rej = sum(b["kept"] for b in banks), sum(b["rejected"] for b in banks)
    add("pipeline_round_trip", f"Of {kept + rej:,} questions written for this project, Jev's blind round trip sent {kept:,} back to "
        f"their intended topic ({kept / (kept + rej):.0%}); banks ranged from 7% (memes, filed by subject) to 100%.",
        kept + rej, round(kept / (kept + rej), 3), banks=banks,
        lesson="Jev files by topic: personality items written as everyday situations (29%) and meme formats (7%) were "
               "rejected until trait and format banks kept their authored topic (docs/10-expansion.md §7).")
    add("pipeline_screen", f"Jev's first content screen hid {54855 + mm:,} questions for politics or sensitivity. Re-asked narrowly and shown "
        f"the content, it released {unflag - mm:,} of the 54,855 it could re-check; the {mm:,} Moral Machine dilemmas "
        f"were shown by rule.", 54855, unflag, first_hidden=54855 + mm, rechecked=54855, released=unflag - mm, by_rule=mm,
        examples_released=["Can the electric antigravity lifter be used to power spaceships?",
                           "Does high blood sugar damage the capillaries more than the arteries?"])
    add("pipeline_dedupe", f"Jev judged near-identical questions and linked {dups:,} duplicates, which are hidden and fold "
        f"into their original.", dups, dups)
    add("pipeline_bill", f"{calls['n']:,} Jev calls in all, every one cached by request hash and never re-sent; median latency "
        f"{int(calls['med'] or 0)} ms.", calls["n"], calls["n"], first=str(calls["t0"]), last=str(calls["t1"]),
        median_ms=int(calls["med"] or 0))
    L = json.loads((A / "findings.json").read_text())
    L["claims"] = [x for x in L["claims"] if x.get("section") != "pipeline"] + claims
    L["n_claims"] = len(L["claims"])
    (A / "findings.json").write_text(json.dumps(L, indent=1, default=str))
    for x in claims:
        print("-", x["sentence"])


if __name__ == "__main__":
    main()
