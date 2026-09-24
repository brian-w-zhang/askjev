# Jaccard near-dup scan: new questions vs all authored banks (and within new). Run from repo root.
import json,re,pathlib,collections
R=pathlib.Path('.')
STOP=set("a an the do you your is are of to in on at for with or and what which how most best more than when would it be as this that there usually prefer like much often kind type way does rather".split())
def toks(t):
    w=re.findall(r"[a-z]+",t.lower()); w=[x[:-1] if x.endswith('s') and len(x)>3 else x for x in w]
    return frozenset(x for x in w if x not in STOP)
ex=[]
for f in R.glob('authored/*.jsonl'):
    if f.name=='g5_p6_taste2.jsonl' or 'routing' in f.name or 'search' in f.name: continue
    for l in f.read_text().splitlines():
        if l.strip(): ex.append(('EX',json.loads(l)['text']))
new=[]
for p in sorted(R.glob('scratchpad/phase6_taste2/*.txt')):
    for i,l in enumerate(p.read_text().splitlines(),1):
        if l.strip() and not l.startswith('#'):
            parts=l.split(' | '); t=parts[1]
            if 'would_you_rather' in p.stem and len(parts)>2: t+=' '+parts[2]
            new.append((f"{p.stem}:{i}", t))
idx=collections.defaultdict(set); allq=ex+new; T=[toks(t) for _,t in allq]
for j,s in enumerate(T):
    for w in s: idx[w].add(j)
off=len(ex)
for k,(w,t) in enumerate(new):
    j0=off+k; s=T[j0]
    if not s: continue
    cand=collections.Counter()
    for x in s:
        for j in idx[x]: cand[j]+=1
    for j,c in cand.items():
        if j==j0 or (j>=off and j<j0): continue
        u=len(s|T[j])
        if c/u>=0.6 and c>=2: print(f"{w}\t{t}\t~\t{allq[j][0]}\t{allq[j][1]}")
