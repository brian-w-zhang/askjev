"""Merge parts/*.jsonl into authored/g5_p6_personality2.jsonl and validate."""
import collections, glob, json, re, sys
from pathlib import Path

ROOT = Path("/Users/junzhang/Projects/askjev")
D = ROOT / "scratchpad/phase6_personality2"
OUT = ROOT / "authored/g5_p6_personality2.jsonl"

# valid node ids from tree
tree = (ROOT / "tree/self.yaml").read_text()
nodes = set(re.findall(r"id: (self\.personality[\w.]*)", tree))


def norm(t):
    return re.sub(r"[^a-z ]", "", t.lower()).strip()


existing = set()
for f in glob.glob(str(ROOT / "authored/*.jsonl")):
    if f == str(OUT):
        continue
    for line in open(f):
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("text") or d.get("query")
        if t:
            existing.add(norm(t))

drop = {norm(l) for l in open(D / "drop.txt") if l.strip()}
rows, errs, seen = [], [], set()
dropped = collections.Counter()
for f in sorted(glob.glob(str(D / "parts/*.jsonl"))):
    for i, line in enumerate(open(f)):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception as e:
            errs.append(f"{f}:{i} parse {e}")
            continue
        p, o, n, t = d.get("primitive"), d.get("options"), d.get("node"), d.get("text", "")
        bad = None
        if set(d) != {"text", "primitive", "options", "node", "kind"} or d["kind"] != "personality":
            bad = "keys"
        elif n not in nodes:
            bad = "node"
        elif re.search(r"\d", json.dumps([t, o], ensure_ascii=False)):
            bad = "digit"
        elif p == "choice" and not (isinstance(o, dict) and 2 <= len(o) <= 255 and "other" in o
                                    and all(re.fullmatch(r"[a-z][a-z0-9_]*", k) for k in o)):
            bad = "choice"
        elif p == "score" and not (isinstance(o, list) and 2 <= len(o) <= 10 and all(isinstance(x, str) and x for x in o)
                                   and len(set(o)) == len(o)):
            bad = "score"
        elif p == "noul" and o is not None and not (isinstance(o, dict) and set(o) == {"true", "false"}):
            bad = "noul"
        elif p not in ("choice", "score", "noul"):
            bad = "primitive"
        if bad:
            errs.append(f"{Path(f).name}:{i} {bad}: {t[:70]}")
            continue
        k = norm(t)
        if k in drop:
            dropped["near_dup"] += 1
            continue
        if k in existing:
            dropped["dup_existing"] += 1
            continue
        if k in seen:
            dropped["dup_internal"] += 1
            continue
        seen.add(k)
        rows.append(d)

print("errors", len(errs))
for e in errs[:40]:
    print(" ", e)
print("dropped", dict(dropped))
if "--write" in sys.argv:
    with open(OUT, "w") as fh:
        for d in rows:
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
print("total", len(rows))
print(collections.Counter(d["primitive"] for d in rows))
for n, c in sorted(collections.Counter(d["node"] for d in rows).items()):
    print(f"  {n} {c}")
