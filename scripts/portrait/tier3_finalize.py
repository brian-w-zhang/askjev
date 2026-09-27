"""Portrait tier 3, final (docs/11-portrait.md §2): apply per-theme filters suggested by the precision audit, then
measure each theme's precision on the audited items that survive the same filters (audit_labels.jsonl). Themes still
below 70% are dropped. Writes data/analysis/themes/final.json with members, measured precision and the rule used.

  uv run python scripts/portrait/tier3_finalize.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

D = Path("data/analysis/themes")
KEEP_BAR = 0.70
RULES = {
    "humor": {"floor": 0.66},
    "death_and_meaning": {"floor": 0.70, "exclude_text": r"\b(cell|cells|planet|solar system|organism|bacteria|hemorrhage)\b"},
    "risk_and_caution": {"floor": 0.75, "exclude_node": r"moving_abroad|\.sports\b|world\.sports"},
    "honesty_and_lies": {"floor": 0.75},
    "attitudes_to_ai": {"floor": 0.66, "exclude_node": r"^machine\.", "require_text": r"\b(ai|a\.i\.|artificial|robots?|machines?|chatbots?|algorithms?|automat\w*|computers?|androids?|llms?)\b"},
    "money_and_status": {"floor": 0.66, "require_text": r"\b(money|rich|wealth\w*|fame|famous|price\w*|salar\w*|income|expensive|cheap|luxur\w*|status|million\w*|billion\w*|dollars?|\$)"},
    "animals_and_nature": {"floor": 0.66, "exclude_node": r"food|nutrition|meat|gross",
                           "exclude_text": r"would most adults have heard of|`context`"},
    "tradition_vs_novelty": {"floor": 0.70, "exclude_node": r"ratings|matchups|video_games|leisure_hobbies|food",
                             "require_text": r"\b(tradition\w*|old|new|modern|classic|past|change\w*|nostalgi\w*|remake|original|future)\b"},
}


def keep(item: dict, rule: dict) -> bool:
    if item["sim"] < rule.get("floor", 0):
        return False
    node, text = item.get("node") or "", item["text"].lower()
    if "exclude_node" in rule and re.search(rule["exclude_node"], node):
        return False
    if "exclude_text" in rule and re.search(rule["exclude_text"], text, re.I):
        return False
    if "require_text" in rule and not re.search(rule["require_text"], text, re.I):
        return False
    return True


def main():
    labels = {}
    for line in (D / "audit_labels.jsonl").read_text().splitlines():
        a = json.loads(line)
        labels[(a["theme"], a["id"])] = a["label"] == "on"
    final = {}
    for theme, rule in RULES.items():
        items = json.loads((D / f"{theme}.json").read_text())
        kept = [i for i in items if keep(i, rule)]
        audited = [labels[(theme, i["id"])] for i in json.loads((D / f"{theme}.audit_sample.json").read_text())
                   if (theme, i["id"]) in labels and keep(i, rule)]
        prec = sum(audited) / len(audited) if audited else 0.0
        status = "kept" if prec >= KEEP_BAR and len(audited) >= 30 else "dropped"
        final[theme] = {"rule": rule, "n": len(kept), "audited": len(audited), "precision": round(prec, 3), "status": status,
                        "members": [i["id"] for i in kept] if status == "kept" else []}
        print(f"{theme:22s} {status:8s} n={len(kept):5d} precision {prec:.0%} on {len(audited)} audited")
    (D / "final.json").write_text(json.dumps(final))


if __name__ == "__main__":
    main()
