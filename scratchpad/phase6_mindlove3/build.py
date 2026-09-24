import json,re,sys,collections,glob
D='/Users/junzhang/Projects/askjev/scratchpad/phase6_mindlove3/'
OUT='/Users/junzhang/Projects/askjev/authored/g5_p6_mindlove3.jsonl'
MIND=['big_questions','thought_experiments','consciousness_ai','epistemics','luck_fate','time_mortality','happiness_wellbeing','memories_life_story']
LOVE=['dating_attraction','romance_partnership','friendship','family_parenting','workplace_community','etiquette_social_norms']
KINDS={'values','personality','evaluative','social','taste'}
def norm(t): return re.sub(r'[^a-z ]','',t.lower().replace('-',' ')).strip()
STOP={'you','your','do','the','a','an','of','to','is','how','what','which','would','are','in','for','it','or','be','have','much','most','that','about','should','think','does','with','on','when','who','can','there','any','its','best','this','at','as','people','someone','person','their','they','them'}
def toks(t): return frozenset(norm(t).split())-STOP
exist={};extoks=[]
for f in glob.glob('/Users/junzhang/Projects/askjev/authored/*.jsonl'):
    if 'mindlove3' in f: continue
    for l in open(f):
        try: t=json.loads(l)['text']
        except Exception: continue
        exist[norm(t)]=t; extoks.append((toks(t),t))
for f in glob.glob('/Users/junzhang/Projects/askjev/authored/existing/*.txt'):
    for l in open(f):
        if ' | ' in l:
            t=l.split(' | ',1)[1].strip(); exist[norm(t)]=t; extoks.append((toks(t),t))
out=[];seen=set();errs=[];cnt=collections.Counter();near=[]
files=[(n,'self.mind.'+n) for n in MIND]+[(n,'self.love.'+n) for n in LOVE]
for n,node in files:
    try: lines=open(D+n+'.txt').read().splitlines()
    except FileNotFoundError: continue
    for i,l in enumerate(lines):
        if not l.strip(): continue
        f=[x.strip() for x in l.split('|')]
        e=lambda m: errs.append(f'{n}:{i+1}: {m}: {l[:100]}')
        if len(f)<3: e('fields'); continue
        t,kind,text=f[0],f[1],f[2]
        if kind not in KINDS: e('kind')
        if re.search(r'\d',l): e('digit')
        if norm(text) in exist: e('dup-existing'); continue
        if norm(text) in seen: e('dup-self'); continue
        seen.add(norm(text))
        if kind=='social' and not re.search(r'\bmost people\b|\bmost couples\b|\bmost parents\b|\bmost friends\b|\bmost coworkers\b|\bmost families\b|\bmost hosts\b|\bmost guests\b|\bmost adults\b|\bmost workers\b|\bmost employees\b|\bmost neighbors\b|\bmost grandparents\b|\bmost children\b|\bmost teenagers\b|\bmost singles\b|\bmost interns\b|\bmost travellers\b|\bmost managers\b|\bmost bosses\b|\bmost roommates\b|\bmost siblings\b',text): e('social-wording')
        if t=='C':
            if len(f)!=4: e('fields'); continue
            opts={}
            for o in f[3].split(';'):
                o=o.strip(); k,_,d=o.partition('=')
                k=k.strip().lower()
                if not re.fullmatch(r'[a-z_]+',k): e('key '+k)
                if k in opts: e('dupkey '+k)
                opts[k]=d.strip() or None
            if not 2<=len(opts)<=9: e(f'nopts {len(opts)}')
            prim='choice'
        elif t=='S':
            if len(f)!=4: e('fields'); continue
            opts=[x.strip() for x in f[3].split(' ; ')]
            if not 3<=len(opts)<=7 or any(not x or ';' in x for x in opts): e(f'levels {len(opts)}')
            if len(set(opts))!=len(opts): e('duplevel')
            prim='score'
        elif t=='N':
            if len(f)!=3: e('fields'); continue
            opts=None; prim='noul'
        else: e('type'); continue
        if not text.endswith('?'): e('noq')
        tk=toks(text)
        for et,etx in extoks:
            if tk and et and len(tk&et)/len(tk|et)>=0.75:
                near.append(f'{n}: {text}  ~~  {etx}'); break
        out.append({'text':text,'primitive':prim,'options':opts,'node':node,'kind':kind})
        cnt[node]+=1
print('\n'.join(errs)); print(len(errs),'errors')
print('\n'.join(near)); print(len(near),'near-dups')
for k,v in sorted(cnt.items()): print(k,v)
print('total',len(out), collections.Counter(o['primitive'] for o in out), collections.Counter(o['kind'] for o in out))
if '--write' in sys.argv:
    with open(OUT,'w') as w:
        for o in out: w.write(json.dumps(o,ensure_ascii=False)+'\n')
    print('wrote',OUT)
