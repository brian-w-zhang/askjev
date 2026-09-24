import json, re, glob, sys, os
D = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/junzhang/Projects/askjev"
NODES = {"fam": "self.love.family_parenting", "work": "self.love.workplace_community", "etq": "self.love.etiquette_social_norms"}
KINDS = {"v": "values", "t": "taste", "s": "social", "p": "personality"}
PRIM = {"C": "choice", "S": "score", "N": "noul"}
STOP = set("a an the to of in on at for is it be you your do should what how which when who much with and or if are that this their them they someone about".split())

def toks(t):
    return set(w for w in re.findall(r"[a-z']+", t.lower()) if w not in STOP)

out, errs = [], []
for f in sorted(glob.glob(os.path.join(D, "*_[csn]*.txt"))):
    base = os.path.basename(f)
    pre = base.split("_")[0]
    for i, line in enumerate(open(f), 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("|")
        p, k, text = parts[0], parts[1], parts[2]
        rec = {"text": text, "primitive": PRIM[p], "options": None, "node": NODES[pre], "kind": KINDS[k]}
        if p == "C":
            opts = {}
            for o in parts[3].split(";"):
                key, _, desc = o.partition("=")
                key = key.strip()
                if not re.fullmatch(r"[a-z0-9_]+", key):
                    errs.append(f"{base}:{i} bad key {key!r}")
                if key in opts:
                    errs.append(f"{base}:{i} dup key {key}")
                opts[key] = desc.strip() or None
            if not 2 <= len(opts) <= 8:
                errs.append(f"{base}:{i} {len(opts)} options")
            rec["options"] = opts
        elif p == "S":
            lv = [x.strip() for x in parts[3].split(";")]
            if not 3 <= len(lv) <= 6:
                errs.append(f"{base}:{i} {len(lv)} levels")
            if len(set(lv)) != len(lv):
                errs.append(f"{base}:{i} dup level")
            rec["options"] = lv
        else:
            if len(parts) != 3:
                errs.append(f"{base}:{i} noul extra fields")
        if re.search(r"\d", json.dumps(rec)):
            errs.append(f"{base}:{i} digit")
        if not text.endswith("?"):
            errs.append(f"{base}:{i} no ?")
        out.append(rec)

existing = []
for l in open(f"{ROOT}/authored/existing/love.txt"):
    n, _, t = l.strip().partition(" | ")
    existing.append(t)
for l in open(f"{ROOT}/authored/g5_self_love_mind.jsonl"):
    existing.append(json.loads(l)["text"])
norm = lambda t: re.sub(r"[^a-z ]", "", t.lower()).strip()
exn = {norm(t) for t in existing}
ext = [(t, toks(t)) for t in set(existing)]
seen = {}
flags = []
for r in out:
    n = norm(r["text"])
    if n in exn:
        errs.append(f"EXACT dup existing: {r['text']}")
    if n in seen:
        errs.append(f"EXACT dup internal: {r['text']}")
    seen[n] = 1
    a = toks(r["text"])
    for t, b in ext:
        if a and b:
            j = len(a & b) / len(a | b)
            if j >= 0.5:
                flags.append(f"{j:.2f} EXT | {r['text']} || {t}")
toklist = [(r["text"], toks(r["text"])) for r in out]
for x in range(len(toklist)):
    for y in range(x + 1, len(toklist)):
        a, b = toklist[x][1], toklist[y][1]
        if a and b and len(a & b) / len(a | b) >= 0.55:
            flags.append(f"{len(a & b)/len(a | b):.2f} INT | {toklist[x][0]} || {toklist[y][0]}")
print("\n".join(errs))
print("---flags")
print("\n".join(sorted(flags, reverse=True)))
from collections import Counter
print(Counter((r["node"][10:], r["primitive"]) for r in out))
print(Counter(r["primitive"] for r in out), len(out))
print(Counter(r["kind"] for r in out))
if "--write" in sys.argv and not errs:
    with open(f"{ROOT}/authored/g5_p6_love2.jsonl", "w") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("WROTE", len(out))
