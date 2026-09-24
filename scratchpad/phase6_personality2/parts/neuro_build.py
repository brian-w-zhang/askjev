import json
C=[];S=[];N=[]
def c(t,*o): C.append((t,list(o)))
def s(t,*l): S.append((t,list(l)))
for f in ['neuro_a.py','neuro_b.py','neuro_c.py','neuro_d.py']:
    exec(open(f).read())
drop=["friend is five minutes late","friend who is always late","friend cancels because they're tired","someone snaps at you for no reason",
"standing in a long line","footsteps outside your door","snack you like is in the cupboard","a sale on something you love",
"promotional email offers","trying to save money and see","stranger makes a sarcastic","teases you about a habit","teases you about a past",
"not liked or commented","unexpected meeting to your calendar","nothing feels right to wear","see a doctor about something minor",
"feel slightly unwell in the morning","days get shorter and darker","long to-do list first thing","many small hassles","holiday season ends",
"quiet evening with nothing to do","free time during a slow week","cliffhanger late at night","new bag of chips","healthy eating plan",
"friendly board game","break a glass","neighbor's dog barks","rearranged by someone else","usual café is closed","new desk location"]
C=[x for x in C if not any(d in x[0] for d in drop)]
S=[x for x in S if not any(d in x[0] for d in drop)]
node="self.personality.big_five.neuroticism"
out=[]
for t,o in C: out.append({"text":t,"primitive":"choice","options":{k:v for k,v in o},"node":node,"kind":"personality"})
for t,l in S: out.append({"text":t,"primitive":"score","options":l,"node":node,"kind":"personality"})
for t in N: out.append({"text":t,"primitive":"noul","options":None,"node":node,"kind":"personality"})
import re,collections
texts=[d["text"] for d in out]
assert len(texts)==len(set(texts))
ex=set(open('../existing/big_five.neuroticism.txt').read().splitlines())
assert not ex & set(texts)
for d in out: assert not re.search(r'\d',json.dumps(d,ensure_ascii=False)), d
for d in out:
    if d["primitive"]=="choice": assert list(d["options"])[-1]=="other" and len(d["options"])>=3
print(collections.Counter(d["primitive"] for d in out), len(out))
with open('neuroticism.jsonl','w') as f:
    for d in out: f.write(json.dumps(d,ensure_ascii=False)+"\n")
