import json, sys
OUT = []
NODE = None
def node(n):
    global NODE; NODE = "self.mind." + n
def C(text, opts, kind="values"):
    # opts: list of keys or (key, desc) tuples
    o = {}
    for x in opts:
        if isinstance(x, tuple): o[x[0]] = x[1]
        else: o[x] = None
    OUT.append({"text": text, "primitive": "choice", "options": o, "node": NODE, "kind": kind})
def S(text, levels, kind="values"):
    OUT.append({"text": text, "primitive": "score", "options": list(levels), "node": NODE, "kind": kind})
def N(text, kind="values"):
    OUT.append({"text": text, "primitive": "noul", "options": None, "node": NODE, "kind": kind})
def dump(path):
    with open(path, "w") as f:
        for d in OUT: f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(path, len(OUT))
