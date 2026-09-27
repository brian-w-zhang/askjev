"""Portrait tier 3 (docs/11-portrait.md §2): cross-cutting themes the tree does not capture, gathered by local
embeddings (bge-small) from shown questions anywhere in the corpus. Each theme's candidates are the union of the
nearest questions to its seed phrases above a similarity floor; a random 200 per theme go to an audit file for a
subagent to label on-topic / off-topic, and the page states the measured precision. No Jev calls.

  uv run python scripts/portrait/tier3_themes.py            # gather + write audit samples
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from askjev import db
from askjev.embed import embed, to_pg

OUT = Path("data/analysis/themes")
SIM_FLOOR = 0.66
PER_SEED = 1500
THEMES = {
    "attitudes_to_ai": ["Should AI systems have rights?", "Can a machine be conscious?", "Would you trust an AI to make this decision?",
                        "Will AI take people's jobs?", "Is it okay to fall in love with a chatbot?", "Do robots deserve moral consideration?"],
    "risk_and_caution": ["Would you take a risky bet for a bigger payoff?", "Would you try a dangerous extreme sport?",
                         "Do you play it safe or take chances?", "Would you invest your savings in a risky startup?",
                         "Would you move abroad without a job lined up?"],
    "animals_and_nature": ["Is it wrong to eat meat?", "Should zoos exist?", "Would you rescue an injured wild animal?",
                           "Do animals have feelings like people?", "Should we protect endangered species at a cost to jobs?"],
    "death_and_meaning": ["Would you want to know the date of your death?", "What gives life meaning?", "Would you want to live forever?",
                          "Is there life after death?", "How should someone be remembered after they die?"],
    "honesty_and_lies": ["Is it okay to tell a white lie?", "Would you return extra change a cashier gave you by mistake?",
                         "Should you tell a friend a hard truth?", "Is lying ever the right thing to do?"],
    "money_and_status": ["Would you take a higher salary for a job you dislike?", "Does money buy happiness?",
                         "Would you rather be rich or famous?", "Is it wrong to show off wealth?", "Would you spend money on luxury brands?"],
    "tradition_vs_novelty": ["Do you prefer the classic version or the new remake?", "Should old traditions be kept?",
                             "Would you try a brand new food you have never heard of?", "Are things better now than in the past?"],
    "humor": ["How funny is this joke?", "Which joke is funnier?", "Would you laugh at a pun?", "Is dark humor okay?"],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    with db.connect() as c:
        c.execute("set hnsw.ef_search = 400")
        for theme, seeds in THEMES.items():
            best: dict[str, tuple[float, str, str]] = {}
            for s, v in zip(seeds, embed(seeds)):
                rows = c.execute("""select id, node_id, text, 1 - (embedding <=> %s::vector) sim from questions
                                    where display_ok and not ('harmful' = any(flags))
                                    order by embedding <=> %s::vector limit %s""", (to_pg(v), to_pg(v), PER_SEED)).fetchall()
                for r in rows:
                    if r["sim"] >= SIM_FLOOR and r["sim"] > best.get(r["id"], (0,))[0]:
                        best[r["id"]] = (float(r["sim"]), r["node_id"], r["text"])
            items = [{"id": k, "sim": round(s, 3), "node": n, "text": t} for k, (s, n, t) in best.items()]
            (OUT / f"{theme}.json").write_text(json.dumps(items, ensure_ascii=False))
            sample = random.Random(theme).sample(items, min(200, len(items)))
            (OUT / f"{theme}.audit_sample.json").write_text(json.dumps(sample, ensure_ascii=False, indent=0))
            summary[theme] = len(items)
            print(f"{theme:22s} {len(items):6d} candidates")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
