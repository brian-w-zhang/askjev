# MVP build plan (the /goal spec)

The overnight autonomous build follows this plan, in phase order. `CLAUDE.md` and `docs/00-08` are the
source of truth; this file only sequences the work. Stay inside this repo.

## Hard rules
- Jev (`typesafe-ai/jev` via Vercel AI Gateway, `AI_GATEWAY_API_KEY`) is the **only** gateway model. No
  other gateway LLM or embedding model, ever. Authoring (node descriptions, synthetic questions, Score-level
  wording, split/group proposals) is done by Claude Code or its subagents, writing into `authored/`.
  Embeddings come from local `BAAI/bge-small-en-v1.5` (fastembed in Python, transformers.js in Next.js;
  parity test cosine > 0.99).
- Only the `base` universe for now.
- Cache every Jev call by request hash in the append-only log; never re-send identical requests; log the
  served version.
- Not a benchmark: indicators only. Contested politics is flagged and hidden, never deleted. Score answers
  are shown as bands.
- Never commit secrets, `data/`, `.env`, or the gitignored personal folders. Commit logical checkpoints and
  push to `origin main` (authorized).
- Use subagents in parallel for authoring (tree nodes, synthetic banks, adapters), and verify their output before
  ingesting it.
- Public downloads only; skip anything that needs a login.
- Treat "Proposed, awaiting Brian" entries in `08-roadmap.md` as approved (mark them decided). When the docs
  are silent, decide, then record the decision in the docs and the decisions log. Never stop to ask.

## Phase 1: Foundation
1. Postgres 17 is running (`DATABASE_URL` in `.env`; ltree/vector/pg_trgm enabled). Write and apply
   `db/migrations` from `06-pipeline.md` §5, seeding only the `base` universe. Set up the Python project with uv.
2. Spikes, with the results written into `01-jev.md`: the request/response shape for `typesafe-ai/jev` through the
   gateway (probabilities, confidence, served version); the determinism noise floor (20 repeats); batch
   invariance. Build the Jev client around what you find: async, ~8 workers, token bucket, backoff, 32k request budget.

## Phase 2: The tree (`02-tree.md`)
3. Author root → 3 hemispheres → 28 L1 → ~200 L2 in `tree/*.yaml`. Each node gets a standalone description,
   `not_for`, and 2-3 examples; L0-L2 are locked. Add L3 only where sources need it (Big Five facets, MFQ
   foundations, sports → NBA, Machine use-case templates). Build the choice cards.
4. Validate routing: a known-path taxonomy sample (Shopify / MeSH / SIC) + ~300 questions with known
   intended nodes. Fix descriptions until routing is clean, and record the results.

## Phase 3: Pipeline + the 10k slice (`03`, `04`, `06`)
5. Implement every stage (fetch → normalize → screen → dedupe → place → expand → plan → ask → explode → measure
   → rollup), plus the restructure job (split/group/grow, accept rules, locked nodes) and the mix report.
6. Ingest ~10k canonical questions to hit the target mix: IPIP (+ Open Psychometrics norms),
   would-you-rather (HF public), GlobalOpinionQA, Scruples dilemmas, MFQ, TruthfulQA, OpenTriviaDB, Wikidata
   NBA pairwise + categorical facts, the TypeSafe docs seed questions (`typesafe-docs-digest.md` §B), 2-3 public
   labeled machine datasets (e.g. Banking77), and G2 templates on L2 nodes. Fill the remaining gaps with G5 synthetic
   questions written by subagents, using the round-trip filter. Everything goes through the screen request and the answer
   bundle, then `question_meta` and `node_stats`.

## Phase 4: Frontend (`07-ui.md`)
7. A Next.js (App Router, TS) app in `web/` that queries Postgres:
   - A sleek 3D tree (react-three-fiber + custom shaders, bloom/glow): smooth zoom, walking any path, and light
     pulses that travel along paths. 60 fps, with lazy-loaded rings.
   - Instant search: local embedding + pgvector + trigram (~50 ms); a human-paced camera and light animation
     along the result's path; one background Jev request that reranks the top 20; an optional "Jev's path"
     second light that forks where Jev disagrees with the embeddings.
   - A question-card side panel: distributions, Score bands, frame toggle, stability, Jev self-assessment,
     human overlay/truth, follow-up thread, a raw-call link.
   - Filters (kind/shape/primitive/origin/indicator) and color-by-indicator.
   - A private ask box: Jev linter → dedupe → fast placement → merged screen+answer request → card.
8. Verify with **headless Playwright** (not the Chrome extension): search, animation, panel, and ask. Save screenshots to
   `docs/screenshots/` and notes to `docs/mvp-status.md`.

## Phase 5: Harden before scaling
9. Run the coverage test, one restructure round, the search recall test (reworded questions → is the original found?),
   dedupe quality, and performance (pipeline throughput, UI latency). Fix what's weak. Move on only when phases 1-5 are solid.

## Phase 6: Scale (only after everything above works)
10. Grow toward 100k, then as far toward 1M as is practical while keeping the mix balanced: Vital Articles L3-L5,
    Wikidata leaves, more pairwise GOAT categories, the remaining public datasets in `04`, more machine datasets, and
    subagent-written G5 banks. Run restructure rounds as nodes fill up. If 1M isn't realistic, stop at a solid,
    balanced number and explain why.

## Phase 7: Expansion to 1M (`10-expansion.md`)
11. Grow in waves of ~100k with a gate after each (all answered, measured, split, reported in
    `docs/expansion-log.md`, committed). Sourcing overlaps with Jev answering; the mix rules and the rules
    for working next to the frontend agent are in `10-expansion.md`.

## Throughout
Keep `docs/mvp-status.md` current: what's done, counts by hemisphere/kind/source vs targets, known issues, and
decisions. Keep the docs consistent with the code. Finish with a final summary and next steps (experiments,
findings, universes).
