"""Search recall test (docs/09 phase 5): reworded user queries → is the original question found?
Instant path = local embedding + pgvector (+ trigram); refined path = one Jev rerank over the top 20."""
import asyncio
import statistics
import time

import orjson

from askjev import db
from askjev.config import AUTHORED, ROOT
from askjev.embed import embed, to_pg
from askjev.jev import JevClient, Request, answers, gateway_question

qs = [orjson.loads(l) for l in (AUTHORED / "search_recall_queries.jsonl").read_bytes().splitlines() if l.strip()]
embed(["warmup"])
hits1 = hits5 = hits20 = 0
lat = []
cands = {}
with db.connect() as conn:
    for q in qs:
        t = time.perf_counter()
        v = to_pg(embed([q["query"]])[0])
        rows = conn.execute(
            "select id, text from questions where display_ok order by embedding <=> %s::vector limit 20", (v,)
        ).fetchall()
        lat.append((time.perf_counter() - t) * 1000)
        ids = [r["id"] for r in rows]
        cands[q["id"]] = rows
        hits1 += ids[:1] == [q["id"]]
        hits5 += q["id"] in ids[:5]
        hits20 += q["id"] in ids


async def rerank():
    c = JevClient()
    reqs = {}
    for q in qs:
        rows = cands[q["id"]]
        crit = {f"c{i}": r["text"] for i, r in enumerate(rows)}
        reqs[q["id"]] = Request({"query": q["query"]}, {"r": gateway_question(
            "choice", "Which of these questions best matches the search `query`?", crit)})
    res = await c.run(list(reqs.values()))
    await c.close()
    return {qid: answers(res[r.hash]).get("r") for qid, r in reqs.items()}


t0 = time.time()
rr = asyncio.run(rerank())
jev1 = 0
for q in qs:
    a = rr.get(q["id"])
    if a:
        best = max(a.dist, key=a.dist.get)
        rows = cands[q["id"]]
        jev1 += rows[int(best[1:])]["id"] == q["id"]
n = len(qs)
out = [f"# Search recall ({n} reworded queries → original question)", "",
       "| path | recall@1 | recall@5 | recall@20 |", "|---|---|---|---|",
       f"| local embedding (bge-small) + pgvector | {100*hits1/n:.1f}% | {100*hits5/n:.1f}% | {100*hits20/n:.1f}% |",
       f"| + one Jev rerank over the top 20 | {100*jev1/n:.1f}% | – | – |", "",
       f"Instant-path latency (embed + pgvector, Python, warm): p50 {statistics.median(lat):.1f} ms, "
       f"p95 {sorted(lat)[int(0.95*n)-1]:.1f} ms. Jev rerank: one request per query.",
       f"Corpus size at test time: {db.connect().execute('select count(*) c from questions').fetchone()['c']} questions."]
(ROOT / "docs" / "search-recall.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
