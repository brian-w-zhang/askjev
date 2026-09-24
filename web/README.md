# askjev web

The private map: a 3D constellation of the topic tree, instant search, Jev's own walk, question cards and
the ask box. Next.js 16 (App Router, TypeScript, Tailwind 4) + react-three-fiber. It queries Postgres
directly and reads `DATABASE_URL` / `AI_GATEWAY_API_KEY` from the repo-root `.env`, server-side only.

## Run
```bash
cd web
npm install
PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install chromium   # browsers go in web/node_modules
npm run dev                          # http://localhost:3000
npm run build && npm start           # production
node scripts/verify.mjs --base http://localhost:3000 [--no-ask]   # e2e check, writes ../docs/screenshots
```
`/api/walk` and `/api/ask` spawn `uv run askjev walk|ask --json ...` at the repo root.

## Model rules
- Jev (`typesafe-ai/jev`) is the only gateway model called. The app calls it directly only for the
  search rerank (`src/lib/server/jev.ts`): one Choice over up to 20 candidates (`c0..c19`). The request
  hash matches the Python client, so a request already in `calls` is never re-sent. New calls are indexed
  in `calls` and appended to `data/calls/<date>/web-<pid>.jsonl`.
- Query embeddings are local: `Xenova/bge-small-en-v1.5`, fp32, **CLS pooling + L2 normalize**.

## Embedding parity (fastembed vs transformers.js)
`uv run python scripts/embed_parity.py` (repo root) writes `web/parity.json`, then run
`node scripts/embed_parity.mjs cls` here. Result, 2026-09-24:

| pooling | cosine, 5 texts | result |
|---|---|---|
| cls | 0.999999 on each | pass (> 0.99) |
| mean | 0.931 to 0.968 | fail |

## API
| Route | What |
|---|---|
| `GET /api/tree?root=<id>&depth=2` / `?expand=a,b` | nodes + subtree `node_stats`, `n_children`, `n_desc`; with filters (`kind`, `primitive`, `origin`, `hidden=1`), `n_match` |
| `GET /api/node/<id>?scope=subtree\|direct&offset=` | node, stats, ancestors, children, a page of questions with `question_meta` |
| `GET /api/question/<id>` | question, meta, base-universe probes + answers, human dists, links, placements, request hashes |
| `GET /api/call/<hash>` | the `calls` row (cached response, log file) |
| `GET /api/search?q=` | local embedding → pgvector top 20 ∪ pg_trgm top 10 (queries of 4 words or fewer) + 5 nearest nodes, each with its root path |
| `POST /api/rerank` | `{q, candidates}` → one Jev Choice, reordered with probabilities |
| `GET /api/walk?q=` / `POST /api/ask` | the Python CLI |

## Files
- `src/lib/server/`: `env` (loads ../.env), `db` (pg pool), `embed`, `jev` (hash, cache, log), `cli`, `filters`
- `src/instrumentation.ts`: warms the embedder and the pool at server start
- `src/lib/`: `store` (zustand + tree loading), `layout` (radial layout, edge curves), `anim` (light pulses), `color`, `actions`
- `src/components/scene/`: `Scene`, `Edges` (GLSL pulse shader), `Nodes` (instanced), `Labels` (screen-space collision culling), `Comets`, `CameraRig`, `Hover`
- `src/components/`: `App`, `Search`, `Controls`, `panel/{Panel,NodeView,QuestionCard,AskBox}`
- `scripts/verify.mjs` (Playwright e2e), `scripts/embed_parity.mjs`

`reactStrictMode` is off because StrictMode's dev-only double mount destroys the WebGL context.
