"""Jev's head-to-heads between experiments, on the whole case study (docs/17, "Ranking").

Jev reads two case studies side by side (title, question, result, takeaways, why ask this, what the data shows, what
it means, caveats) and picks the one that teaches a curious reader more; every pair is asked in both orders so the
position lean cancels, and Bradley-Terry turns the soft wins into one strength per experiment. Each experiment meets
about 14 others. Writes data/analysis/experiments/_rank.json (private). Jev calls are cached.

  ASKJEV_RPS=16 uv run python scripts/experiments/rank.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cases  # noqa: E402
import evaluate  # noqa: E402

OUT = cases.OUT / "_rank.json"


def card(c: dict) -> dict:
    s = c["sections"]
    x = {"title": c["title"], "question": c["question"], "result": c["result"]}
    if c.get("takeaways"):
        x["in short"] = c["takeaways"]
    x.update({"why ask this": s.get("why"), "what the data shows": s.get("found"),
              "what it means, and what it doesn't": s.get("means"),
              "caveats": [f"{v['label']}: {v['text']}" for v in c.get("caveats") or []]})
    return {k: v for k, v in x.items() if v}


def main():
    items = []
    for p in sorted(cases.OUT.glob("*.case.md")):
        i = p.name[:-8]
        c = cases.load(i)
        e = json.loads((cases.OUT / f"{i}.json").read_text())
        if not c:
            continue
        items.append({"id": i, "title": e["spec"]["title"], "question": e["spec"]["question"],
                      "result": (c.get("result") or e["result"]["result"]).strip(), "takeaways": c.get("takeaways"),
                      "sections": c["sections"], "caveats": c.get("caveats")})
    bt = evaluate.pairwise(items, pairs_per_item=12, card_fn=card)
    OUT.write_text(json.dumps(dict(sorted(bt.items(), key=lambda kv: -kv[1])), indent=1))
    top = sorted(bt, key=bt.get, reverse=True)
    print(f"{len(bt)} experiments; top: {', '.join(top[:5])}; bottom: {', '.join(top[-3:])}")


if __name__ == "__main__":
    main()
