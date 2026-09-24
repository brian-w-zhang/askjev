import json,re,sys,collections
D='/Users/junzhang/Projects/askjev/scratchpad/phase6_mind2/'
nodes=['luck_fate','time_mortality','happiness_wellbeing','memories_life_story']
KINDS={'values','personality','evaluative','social','taste'}
def norm(t): return re.sub(r'[^a-z ]','',t.lower()).strip()
exist={norm(l.split(' | ',1)[1]) for l in open('/Users/junzhang/Projects/askjev/authored/existing/mind.txt') if ' | ' in l}
import glob
for f in glob.glob('/Users/junzhang/Projects/askjev/authored/*.jsonl'):
    if 'g5_p6_mind2' in f: continue
    for l in open(f):
        try: exist.add(norm(json.loads(l)['text']))
        except Exception: pass
out=[];seen=set();errs=[];cnt=collections.Counter()
for n in nodes:
    try: lines=open(D+n+'.txt').read().splitlines()
    except FileNotFoundError: print('missing',n); continue
    for i,l in enumerate(lines):
        if not l.strip(): continue
        f=[x.strip() for x in l.split(' | ')]
        t,kind,text=f[0],f[1],f[2]
        e=lambda m: errs.append(f'{n}:{i+1}: {m}: {l[:90]}')
        if kind not in KINDS: e('kind')
        if re.search(r'\d',l): e('digit')
        if norm(text) in exist: e('dup-existing'); continue
        if norm(text) in seen: e('dup-self'); continue
        seen.add(norm(text))
        if t=='C':
            if len(f)!=4: e('fields'); continue
            opts={}
            for o in f[3].split(';'):
                o=o.strip(); k,_,d=o.partition('=')
                k=k.strip().lower()
                if not re.fullmatch(r'[a-z0-9_]+',k): e('key '+k)
                if k in opts: e('dupkey '+k)
                opts[k]=d.strip() or None
            if not 2<=len(opts)<=8: e(f'nopts {len(opts)}')
            prim='choice'
        elif t=='S':
            if len(f)!=4: e('fields'); continue
            opts=[x.strip() for x in f[3].split(' ; ')]
            if not 3<=len(opts)<=6 or any(not x or ';' in x for x in opts): e(f'levels {len(opts)}')
            prim='score'
        elif t=='N':
            if len(f)!=3: e('fields'); continue
            opts=None; prim='noul'
        else: e('type'); continue
        if not text.endswith('?'): e('noq')
        out.append({'text':text,'primitive':prim,'options':opts,'node':'self.mind.'+n,'kind':kind})
        cnt[(n,prim)]+=1
print('\n'.join(errs[:60])); print(len(errs),'errors')
for k,v in sorted(cnt.items()): print(k,v)
print('total',len(out), collections.Counter(o['primitive'] for o in out), collections.Counter(o['kind'] for o in out))
if '--write' in sys.argv:
    with open('/Users/junzhang/Projects/askjev/authored/g5_p6_mind2.jsonl','w') as w:
        for o in out: w.write(json.dumps(o,ensure_ascii=False)+'\n')

def toks(t): return set(norm(t).split())-{'you','your','do','the','a','of','to','is','how','what','which','would','are','in','for','it','or','be','have','much','most','that','about'}
ex=[l.split(' | ',1)[1].strip() for l in open('/Users/junzhang/Projects/askjev/authored/existing/mind.txt') if ' | ' in l]
for f in glob.glob('/Users/junzhang/Projects/askjev/authored/*.jsonl'):
    if 'g5_p6_mind2' in f: continue
    for l in open(f):
        try: ex.append(json.loads(l)['text'])
        except Exception: pass
et=[(x,toks(x)) for x in ex]
if '--fuzzy' in sys.argv:
    for o in out:
        a=toks(o['text'])
        for x,b in et:
            if a and b and len(a&b)/len(a|b)>=0.6: print('NEAR:',o['text'],'||',x)
