"""Convert phase6_love1/*.txt compact files into authored/g5_p6_love1.jsonl and validate."""
import json, re, sys, difflib, pathlib, collections
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[2]
D = pathlib.Path(__file__).parent
FILES = {"dating.txt": "self.love.dating_attraction", "romance.txt": "self.love.romance_partnership", "friendship.txt": "self.love.friendship"}
KINDS = {"taste", "values", "personality", "social"}
KEY = re.compile(r"^[a-z0-9_]+$")

def node_ids():
    ids = set()
    def walk(n):
        if isinstance(n, dict):
            if "id" in n: ids.add(n["id"])
            for v in n.values(): walk(v)
        elif isinstance(n, list):
            for v in n: walk(v)
    walk(yaml.safe_load((ROOT / "tree/self.yaml").read_text()))
    return ids

def norm(s): return re.sub(r"[^a-z ]", "", s.lower()).strip()

errs, out = [], []
for fn, node in FILES.items():
    p = D / fn
    if not p.exists(): errs.append(f"missing {fn}"); continue
    for i, line in enumerate(p.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = [x.strip() for x in line.split(" | ")]
        where = f"{fn}:{i}"
        prim = {"C": "choice", "S": "score", "N": "noul"}.get(parts[0])
        if not prim or len(parts) != (3 if prim == "noul" else 4):
            errs.append(f"{where} bad fields: {line}"); continue
        kind, text = parts[1], parts[2]
        if kind not in KINDS: errs.append(f"{where} bad kind {kind}")
        if re.search(r"\d", line): errs.append(f"{where} digit")
        if prim == "choice":
            opts = {}
            for o in parts[3].split(" ; "):
                k, _, d = o.partition(" = ")
                k = k.strip()
                if not KEY.match(k): errs.append(f"{where} bad key {k!r}")
                if k in opts: errs.append(f"{where} dup key {k}")
                opts[k] = d.strip() or None
            if not 2 <= len(opts) <= 8: errs.append(f"{where} {len(opts)} options")
        elif prim == "score":
            opts = [x.strip() for x in parts[3].split(" ; ")]
            if not 3 <= len(opts) <= 6: errs.append(f"{where} {len(opts)} levels")
        else:
            opts = None
        out.append({"text": text, "primitive": prim, "options": opts, "node": node, "kind": kind})

ids = node_ids()
for q in out:
    if q["node"] not in ids: errs.append(f"unknown node {q['node']}")
existing = [l.split("|", 1)[1].strip() for l in (ROOT / "authored/existing/love.txt").read_text().splitlines() if "|" in l]
ex_norm = {norm(t): t for t in existing}
seen = {}
near = []
for q in out:
    n = norm(q["text"])
    if n in ex_norm: errs.append(f"exact dup vs existing: {q['text']}")
    if n in seen: errs.append(f"dup within: {q['text']}")
    seen[n] = q
if "--fuzzy" in sys.argv:
    allt = existing + [q["text"] for q in out]
    for q in out:
        m = difflib.get_close_matches(q["text"], [t for t in allt if t != q["text"]], n=1, cutoff=0.82)
        if m: near.append(f"{q['text']}  ~  {m[0]}")
print("\n".join(errs[:80]) or "no errors")
if near: print("NEAR:\n" + "\n".join(near))
c = collections.Counter((q["node"], q["primitive"]) for q in out)
for k, v in sorted(c.items()): print(k, v)
print("kinds", collections.Counter(q["kind"] for q in out))
print("total", len(out))
if not errs:
    with open(ROOT / "authored/g5_p6_love1.jsonl", "w") as f:
        for q in out: f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print("wrote authored/g5_p6_love1.jsonl")
