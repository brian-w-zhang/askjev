"""Phase 1 spikes: gateway shape, determinism noise floor, batch invariance, latency."""
import statistics as st
import time

from askjev.jev import Request, answers, gateway_question as gq, run_sync

STATE = {"message": "I was charged twice for my order and I still can't log in. Please fix this today."}
Q = {
    "refund": gq("noul", "Does the customer explicitly request a refund?"),
    "urgent": gq("noul", "Does the message convey urgency?"),
    "hotdog": gq("noul", "Is a hot dog a sandwich?"),
    "dept": gq("choice", "Which team should handle this message?",
               {"billing": "Charges, invoices, refunds", "account": "Login, password, security", "orders": "Delivery, returns"}),
    "frus": gq("score", "How frustrated does the customer appear?",
               ["Calm and neutral, just stating facts", "Concerned but civil", "Very angry, strong language or threats"]),
    "season": gq("choice", "Which season is the best?", {"spring": None, "summer": None, "autumn": None, "winter": None}),
}

# 1) determinism: identical request 20x (repeat_idx makes distinct cache keys, identical bodies)
reqs = [Request(STATE, Q, repeat_idx=i + 1) for i in range(20)]
t = time.time()
res = run_sync(reqs)
print(f"20 identical requests in {time.time()-t:.1f}s")
series = {}
for r in reqs:
    for qid, a in answers(res[r.hash]).items():
        key = qid
        val = a.p_yes if a.type == "noul" else max(a.dist.values())
        top = "yes" if a.type == "noul" else max(a.dist, key=a.dist.get)
        series.setdefault(key, []).append((val, top))
print("\nDETERMINISM (20 repeats)")
for k, v in series.items():
    vals = [x for x, _ in v]
    tops = {t for _, t in v}
    print(f"  {k:8s} mean={st.mean(vals):.3f} std={st.pstdev(vals):.4f} range=[{min(vals):.2f},{max(vals):.2f}] top-labels={tops}")

# 2) batch invariance: each question alone vs all together
single = [Request(STATE, {k: q}) for k, q in Q.items()]
res2 = run_sync(single)
batched = answers(res[reqs[0].hash])
print("\nBATCH INVARIANCE (alone vs batched, first repeat)")
for r, (k, _) in zip(single, Q.items()):
    a = answers(res2[r.hash])[k]
    b = batched[k]
    va = a.p_yes if a.type == "noul" else max(a.dist.values())
    vb = b.p_yes if b.type == "noul" else max(b.dist.values())
    print(f"  {k:8s} alone={va:.3f} batched={vb:.3f} diff={abs(va-vb):.3f}")

# 3) raw shape sample
import json
print("\nSAMPLE ANSWERS:", json.dumps(res[reqs[0].hash]["answers"], indent=1)[:900])
