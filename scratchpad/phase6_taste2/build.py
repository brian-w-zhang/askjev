"""Convert phase6_taste2/<node_id>.txt compact files into authored/g5_p6_taste2.jsonl and validate.

Line formats (fields separated by ' | '):
  C | text | key ; key = description ; key
  S | text | level ; level ; level
  N | text
Usage: build.py [--check FILE...] [--fuzzy] [--write]
"""
import json, re, sys, difflib, pathlib, collections
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[2]
D = pathlib.Path(__file__).parent
KEY = re.compile(r"^[a-z0-9_]+$")

def node_ids():
    ids = set()
    def walk(n):
        ids.add(n["id"])
        for c in n.get("children") or []: walk(c)
    for f in ("self", "world"): walk(yaml.safe_load((ROOT / f"tree/{f}.yaml").read_text()))
    return ids

def norm(s): return re.sub(r"[^a-z ]", "", s.lower()).strip()

args = sys.argv[1:]
files = [pathlib.Path(a) for a in args if a.endswith(".txt")] or sorted(D.glob("*.txt"))
ids = node_ids()
errs, out = [], []
for p in files:
    p = p if p.is_absolute() else D / p.name
    node = p.stem
    if node not in ids: errs.append(f"unknown node file {p.name}"); continue
    for i, line in enumerate(p.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = [x.strip() for x in line.split(" | ")]
        where = f"{p.name}:{i}"
        prim = {"C": "choice", "S": "score", "N": "noul"}.get(parts[0])
        if not prim or len(parts) != (2 if prim == "noul" else 3):
            errs.append(f"{where} bad fields: {line}"); continue
        text = parts[1]
        if re.search(r"\d", line): errs.append(f"{where} digit")
        if not text.endswith("?"): errs.append(f"{where} no question mark")
        if prim == "choice":
            opts = {}
            for o in parts[2].split(" ; "):
                k, _, d = o.partition(" = ")
                k = k.strip()
                if not KEY.match(k): errs.append(f"{where} bad key {k!r}")
                if k in opts: errs.append(f"{where} dup key {k}")
                opts[k] = d.strip() or None
            if not 2 <= len(opts) <= 8: errs.append(f"{where} {len(opts)} options")
        elif prim == "score":
            opts = [x.strip() for x in parts[2].split(" ; ")]
            if not 3 <= len(opts) <= 6: errs.append(f"{where} {len(opts)} levels")
            if len(set(opts)) != len(opts) or any(not o for o in opts): errs.append(f"{where} bad levels")
        else:
            opts = None
        out.append({"text": text, "primitive": prim, "options": opts, "node": node, "kind": "taste"})

existing = []
for f in sorted((ROOT / "authored").glob("*.jsonl")):
    if f.name in ("g5_p6_taste2.jsonl",) or "routing" in f.name or "search" in f.name: continue
    for l in f.read_text().splitlines():
        if l.strip(): existing.append(json.loads(l)["text"])
ex_norm = set(map(norm, existing))
seen = set()
for q in out:
    n = norm(q["text"])
    if n in ex_norm: errs.append(f"dup vs existing: {q['text']}")
    if n in seen: errs.append(f"dup within: {q['text']}")
    seen.add(n)
near = []
if "--fuzzy" in args:
    pool = existing + [q["text"] for q in out]
    for q in out:
        m = difflib.get_close_matches(q["text"], [t for t in pool if t != q["text"]], n=1, cutoff=0.88)
        if m: near.append(f"{q['node']}: {q['text']}  ~  {m[0]}")
print("\n".join(errs[:200]) or "no errors")
if near: print(f"NEAR ({len(near)}):\n" + "\n".join(near))
c = collections.Counter(q["node"] for q in out)
pc = collections.Counter(q["primitive"] for q in out)
for k, v in sorted(c.items()): print(f"{k:45s} {v}")
print("primitives", dict(pc), {k: round(v / max(len(out), 1), 2) for k, v in pc.items()})
print("total", len(out))
if "--write" in args and not errs:
    with open(ROOT / "authored/g5_p6_taste2.jsonl", "w") as f:
        for q in out: f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print("wrote authored/g5_p6_taste2.jsonl")
