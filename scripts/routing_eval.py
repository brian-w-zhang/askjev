"""Phase 2 routing validation: place held-out questions (authored/routing_eval.jsonl) from the root and compare
with the intended node. Reports exact / ancestor-or-descendant / same-L1 / same-hemisphere accuracy and the
most confused node pairs. Results → docs/routing-eval.md."""
import asyncio
import collections
import sys

import orjson

from askjev.config import AUTHORED, ROOT
from askjev.jev import sha
from askjev.place import place_many

path = AUTHORED / "routing_eval.jsonl"
rows = [orjson.loads(l) for l in path.read_bytes().splitlines() if l.strip()]
qs = [{"id": sha(r)[:16], "text": r["text"], "options": r.get("options"), "state": r.get("state"), "_r": r} for r in rows]
res = asyncio.run(place_many(qs))


def rel(intended, placed):
    if placed == intended:
        return "exact"
    if placed.startswith(intended + ".") or intended.startswith(placed + "."):
        return "lineage"
    if intended.split(".")[:2] == placed.split(".")[:2]:
        return "same_l1"
    if intended.split(".")[0] == placed.split(".")[0]:
        return "same_hemisphere"
    return "wrong_hemisphere"


stats = collections.Counter()
by_h = collections.defaultdict(collections.Counter)
by_diff = collections.defaultdict(collections.Counter)
confused = collections.Counter()
low_sep = 0
for q in qs:
    r = res.get(q["id"], {})
    placed = r.get("node", "root")
    k = rel(q["_r"]["intended"], placed)
    stats[k] += 1
    by_h[q["_r"]["intended"].split(".")[0]][k] += 1
    by_diff[q["_r"].get("difficulty", "easy")][k] += 1
    if k not in ("exact", "lineage"):
        confused[(q["_r"]["intended"], placed)] += 1
    if r.get("separation", 100) < 1.5:
        low_sep += 1
n = len(qs)
lines = [f"# Routing evaluation (held-out, {n} questions)", "",
         "Each question was written for a known node (authored/routing_eval.jsonl, not shown to Jev) and placed from the root",
         "by Jev beam search (K=3). *lineage* = placed at an ancestor or descendant of the intended node.", ""]
def fmt(c, tot):
    return " | ".join(f"{k} {100*c[k]/tot:.1f}%" for k in ["exact", "lineage", "same_l1", "same_hemisphere", "wrong_hemisphere"])
lines.append(f"**All:** {fmt(stats, n)}  ")
lines.append(f"**Correct branch (exact + lineage): {100*(stats['exact']+stats['lineage'])/n:.1f}%**; low separation (<1.5x): {low_sep}")
for h, c in sorted(by_h.items()):
    lines.append(f"- {h} ({sum(c.values())}): {fmt(c, sum(c.values()))}")
for d, c in sorted(by_diff.items()):
    lines.append(f"- difficulty={d} ({sum(c.values())}): {fmt(c, sum(c.values()))}")
lines.append("\n## Most confused (intended → placed)")
for (a, b), k in confused.most_common(25):
    lines.append(f"- {a} → {b} ({k})")
out = "\n".join(lines)
tag = sys.argv[1] if len(sys.argv) > 1 else ""
(ROOT / "docs" / f"routing-eval{tag}.md").write_text(out + "\n")
print(out)
