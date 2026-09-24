"""Coverage test (docs/02-tree.md §9): place ~1,000 real questions from a source never used to build the tree
(Quora question pairs) and measure how often Jev finds a specific home (depth ≥ L2 with confidence ≥ 0.5)."""
import asyncio
import collections
import random

import polars as pl

from askjev.config import RAW, ROOT
from askjev.jev import sha
from askjev.place import place_many

d = pl.read_parquet(RAW / "quora" / "pair-class.parquet")
texts = list(dict.fromkeys(d["sentence1"].to_list()))
random.Random(11).shuffle(texts)
texts = [t for t in texts if 20 < len(t) < 200][:1000]
qs = [{"id": sha(t)[:16], "text": t, "options": None, "state": None} for t in texts]
res = asyncio.run(place_many(qs))
depth = collections.Counter()
hemi = collections.Counter()
l1 = collections.Counter()
conf_ok = 0
homed = 0
low = []
for q in qs:
    r = res.get(q["id"], {})
    node = r.get("node", "root")
    dpt = 0 if node == "root" else node.count(".") + 1
    depth[dpt] += 1
    hemi[node.split(".")[0]] += 1
    if dpt >= 2:
        l1[".".join(node.split(".")[:2])] += 1
    c = r.get("confidence", 0)
    conf_ok += c >= 0.5
    if dpt >= 3 and c >= 0.5:
        homed += 1
    elif len(low) < 15:
        low.append((q["text"], node, round(c, 2)))
n = len(qs)
out = [f"# Coverage test: {n} Quora questions (never used to build the tree)", "",
       "Each question was placed from the root by Jev beam search. *Homed* = placed at depth ≥ 3 (an L2 or deeper) with",
       "path confidence ≥ 0.5. Quora includes many open how-to questions; only topical placement is measured here.", "",
       f"**Homed: {100*homed/n:.1f}%** (target: < 5% orphans at L2 → ≥ 95% homed)  ",
       f"Confidence ≥ 0.5: {100*conf_ok/n:.1f}%", "",
       "Final depth: " + ", ".join(f"L{k-1 if k else 0}={v}" for k, v in sorted(depth.items())),
       "Hemisphere: " + ", ".join(f"{k}={v}" for k, v in hemi.most_common()),
       "", "Top L1s: " + ", ".join(f"{k}={v}" for k, v in l1.most_common(12)),
       "", "## Examples not homed"] + [f"- {t!r} → {nd} ({c})" for t, nd, c in low]
(ROOT / "docs" / "coverage-test.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
