"""Convert phase6_personality/*.txt compact files into authored/g5_p6_personality.jsonl and validate.

File format (one question per line; '#' comments; blank lines ignored):
  @node self.personality.big_five.openness      <- sets node for following lines
  C | question text | key = optional description ; key2 ; key3 = desc
  S | question text | level low ; level ; level high
  N | question text
Usage: uv run python build.py [file.txt ...] [--fuzzy] [--write]
"""
import json, re, sys, pathlib, collections
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[2]
D = pathlib.Path(__file__).parent
KEY = re.compile(r"^[a-z][a-z0-9_]*$")
BANNED = re.compile(r"\b(sex\w*|nude|naked|porn\w*|politic\w*|democrat\w*|republican\w*|liberal|conservative|election|vote|voting|diagnos\w*|disorder|adhd|autis\w*|bipolar|ocd|ptsd|depression|depressed|suicid\w*|self-harm|medication|psychiatr\w*|trump|biden)\b", re.I)

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
def toks(s): return set(norm(s).split()) - {"you","do","your","a","the","to","of","is","are","how","what","when","or","in","at","it","would","which","if","on","for","most","usually","and"}

args = [a for a in sys.argv[1:] if not a.startswith("--")]
files = [D / a for a in args] if args else sorted(D.glob("*.txt"))
ids = node_ids()
errs, out = [], []
for p in files:
    node = None
    for i, line in enumerate(p.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        where = f"{p.name}:{i}"
        if line.startswith("@node"):
            node = line.split()[1]
            if node not in ids: errs.append(f"{where} unknown node {node}")
            continue
        parts = [x.strip() for x in line.split(" | ")]
        prim = {"C": "choice", "S": "score", "N": "noul"}.get(parts[0])
        if not prim or len(parts) != (2 if prim == "noul" else 3):
            errs.append(f"{where} bad fields: {line}"); continue
        if node is None: errs.append(f"{where} no @node"); continue
        text = parts[1]
        if not text.endswith("?"): errs.append(f"{where} no question mark")
        if re.search(r"\d", line): errs.append(f"{where} digit")
        if BANNED.search(line): errs.append(f"{where} banned word {BANNED.search(line).group(0)}")
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
            if len(set(opts)) != len(opts) or any(not x for x in opts): errs.append(f"{where} bad levels")
        else:
            opts = None
        out.append({"text": text, "primitive": prim, "options": opts, "node": node, "kind": "personality", "_w": where})

existing = []
for f in ROOT.glob("authored/*.jsonl"):
    if f.name == "g5_p6_personality.jsonl": continue
    for l in f.read_text().splitlines():
        try: existing.append(json.loads(l)["text"])
        except Exception: pass
for f in ROOT.glob("authored/existing/*.txt"):
    existing += [l.split("|", 1)[1].strip() for l in f.read_text().splitlines() if "|" in l]
ex_norm = {norm(t) for t in existing}
seen = {}
for q in out:
    n = norm(q["text"])
    if n in ex_norm: errs.append(f"{q['_w']} exact dup vs existing: {q['text']}")
    if n in seen: errs.append(f"{q['_w']} dup within ({seen[n]['_w']}): {q['text']}")
    seen[n] = q
near = []
if "--fuzzy" in sys.argv:
    # also compare against the other personality txt files so forks see each other's work
    others = []
    for f in D.glob("*.txt"):
        if f in files: continue
        others += [l.split(" | ")[1] for l in f.read_text().splitlines() if l[:4] in ("C | ", "S | ", "N | ")]
    pool = [(t, toks(t)) for t in existing + others] + [(q["text"], toks(q["text"])) for q in out]
    for q in out:
        a = toks(q["text"])
        if len(a) < 3: continue
        for t, b in pool:
            if t == q["text"] or not b: continue
            j = len(a & b) / len(a | b)
            if j >= 0.7: near.append(f"{q['_w']} {q['text']}  ~  {t}"); break
print("\n".join(errs[:200]) or "no errors")
if near: print("NEAR (%d):\n" % len(near) + "\n".join(near))
c = collections.Counter(q["node"] for q in out)
cp = collections.Counter((q["node"], q["primitive"]) for q in out)
for k in sorted(c): print(k, c[k], {p: cp[(k, p)] for p in ("choice", "score", "noul")})
print("primitives", collections.Counter(q["primitive"] for q in out))
print("total", len(out))
if "--write" in sys.argv:
    if errs: print("NOT WRITTEN: errors"); sys.exit(1)
    with open(ROOT / "authored/g5_p6_personality.jsonl", "w") as f:
        for q in out:
            q.pop("_w"); f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print("wrote authored/g5_p6_personality.jsonl")
