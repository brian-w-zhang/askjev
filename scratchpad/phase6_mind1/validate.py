import json, re, sys, collections, difflib
D='/Users/junzhang/Projects/askjev/'
nodes=['big_questions','thought_experiments','consciousness_ai','epistemics']
def norm(t): return re.sub(r'[^a-z ]','',t.lower()).strip()
ex=set()
for l in open(D+'authored/existing/mind.txt'):
    ex.add(norm(l.split('|',1)[1]))
for f in ['g5_self_love_mind.jsonl','g5_self_lifestyle_traits.jsonl']:
    for l in open(D+'authored/'+f): ex.add(norm(json.loads(l)['text']))
exl=list(ex)
rows=[];errs=[];seen={}
for n in nodes:
    for i,l in enumerate(open(D+f'scratchpad/phase6_mind1/{n}.jsonl')):
        d=json.loads(l); rows.append(d)
        t=d['text']; p=d['primitive']; o=d['options']
        e=[]
        if set(d)!={'text','primitive','options','node','kind'}: e.append('fields')
        if d['node']!='self.mind.'+n: e.append('node')
        if d['kind'] not in ('values','evaluative','personality','social'): e.append('kind')
        if re.search(r'\d',json.dumps(d)): e.append('digit')
        if p=='choice':
            if not isinstance(o,dict) or not 2<=len(o)<=8 or any(not re.fullmatch(r'[a-z0-9_]+',k) for k in o) or any(v is not None and not isinstance(v,str) for v in o.values()): e.append('choice')
        elif p=='score':
            if not isinstance(o,list) or not 3<=len(o)<=6 or len(set(o))!=len(o) or any(not isinstance(x,str) or not x for x in o): e.append('score')
        elif p=='noul':
            if o is not None: e.append('noul')
        else: e.append('prim')
        k=norm(t)
        if k in ex: e.append('dup_existing')
        if k in seen: e.append('dup_internal:'+seen[k])
        seen[k]=n
        if e: errs.append((n,i,e,t))
print('errors',len(errs))
for x in errs: print(x)
c=collections.Counter((d['node'].split('.')[-1],d['primitive']) for d in rows)
for n in nodes: print(n, sum(v for (a,b),v in c.items() if a==n), {b:v for (a,b),v in c.items() if a==n})
print('total',len(rows), collections.Counter(d['primitive'] for d in rows), collections.Counter(d['kind'] for d in rows))
# near dups
if '--near' in sys.argv:
    texts=[norm(d['text']) for d in rows]
    for i,t in enumerate(texts):
        m=difflib.get_close_matches(t,exl,1,0.85)
        if m: print('NEAR_EX',rows[i]['text'],'||',m[0])
    for i in range(len(texts)):
        for j in range(i+1,len(texts)):
            if difflib.SequenceMatcher(None,texts[i],texts[j]).quick_ratio()>0.88 and difflib.SequenceMatcher(None,texts[i],texts[j]).ratio()>0.88:
                print('NEAR_IN',rows[i]['text'],'||',rows[j]['text'])
if '--write' in sys.argv and not errs:
    with open(D+'authored/g5_p6_mind1.jsonl','w') as f:
        for d in rows: f.write(json.dumps(d,ensure_ascii=False)+'\n')
    print('written')
