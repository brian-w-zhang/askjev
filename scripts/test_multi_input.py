"""Does packing several Machine inputs into one request change Jev's answers? (docs/10-expansion.md §7 throughput work)

Takes N already-answered Machine questions with ground truth, re-asks their base probe with K inputs packed into one state
({"item_1": state_a, "item_2": state_b, ...}; each question's backticked keys rewritten to `item_i.key`), and compares with
the stored single-input answers: accuracy, top-label agreement, and mean absolute probability shift. Nothing is written
to answers; the calls are cached and logged as usual.

  uv run python scripts/test_multi_input.py --n 400 --k 4
"""

import argparse
import asyncio
import re
import statistics

from askjev import db
from askjev.answer import answer_probes
from askjev.jev import JevClient, Request, answers


def rewrite(obj, keys, item):
    if isinstance(obj, str):
        for k in keys:
            obj = re.sub(rf"`{re.escape(k)}(?=[`.\[])", f"`{item}.{k}", obj)
        return obj
    if isinstance(obj, dict):
        return {k: rewrite(v, keys, item) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rewrite(v, keys, item) for v in obj]
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--k", type=int, default=4)
    a = ap.parse_args()
    with db.connect() as c:
        rows = c.execute(
            """select q.id, q.text, q.options, q.state, q.hemisphere, q.primitive, q.meta, q.truth, q.template_id,
                      a.distribution single
               from questions q join probes p on p.question_id=q.id and p.variant_kind='base'
               join answers a on a.probe_id=p.id
               where q.hemisphere='machine' and q.truth is not null and q.state is not null
                 and length(q.state::text) < 1400 and q.primitive in ('noul','choice')
               order by md5(q.id) limit %s""", (a.n,)).fetchall()
    groups = [rows[i:i + a.k] for i in range(0, len(rows), a.k)]
    reqs, meta = [], []
    for g in groups:
        state, qs = {}, {}
        for i, q in enumerate(g, 1):
            item = f"item_{i}"
            state[item] = q["state"]
            base = [p for p in answer_probes(q) if p["variant_kind"] == "base"][0]
            qs[f"q{i}"] = rewrite(base["gw"], list(q["state"].keys()), item)
            meta.append((q, f"q{i}"))
        reqs.append(Request(state, qs))

    async def go():
        cl = JevClient(workers=8, rps=4)
        try:
            return await cl.run(reqs)
        finally:
            await cl.close()

    res = asyncio.run(go())
    by_q = {}
    for r, g in zip(reqs, groups):
        resp = res.get(r.hash, {})
        if "error" in resp:
            continue
        ans = answers(resp)
        for i, q in enumerate(g, 1):
            if f"q{i}" in ans:
                by_q[q["id"]] = (q, ans[f"q{i}"].dist)

    def top(d):
        return max(d, key=d.get) if d else None

    def correct(q, d):
        t = q["truth"]
        if q["primitive"] == "noul":
            return (d.get("true", 0) >= 0.5) == bool(t)
        return top(d) == t

    single_ok = [correct(q, q["single"]) for q, _ in by_q.values()]
    packed_ok = [correct(q, d) for q, d in by_q.values()]
    agree = [top(q["single"]) == top(d) for q, d in by_q.values()]
    shift = [statistics.mean(abs(q["single"].get(k, 0) - d.get(k, 0)) for k in set(d) | set(q["single"])) for q, d in by_q.values()]
    n = len(by_q)
    print(f"compared {n} questions, K={a.k} inputs per request ({len(reqs)} requests; {sum('error' in res.get(r.hash, {}) for r in reqs)} failed)")
    print(f"accuracy  single {sum(single_ok)/n:.3f}   packed {sum(packed_ok)/n:.3f}")
    print(f"top-label agreement {sum(agree)/n:.3f}   mean |Δp| {statistics.mean(shift):.3f}")


if __name__ == "__main__":
    main()
