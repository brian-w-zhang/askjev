# Search recall (200 reworded queries → original question)

| path | recall@1 | recall@5 | recall@20 |
|---|---|---|---|
| local embedding (bge-small) + pgvector | 76.5% | 91.0% | 95.5% |
| + one Jev rerank over the top 20 | 90.5% | – | – |

Instant-path latency (embed + pgvector, Python, warm): p50 5.0 ms, p95 10.0 ms. Jev rerank: one request per query.
Corpus size at test time: 10780 questions.
