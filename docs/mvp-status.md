# MVP status

_Living status of the autonomous build (docs/09-mvp-plan.md). Newest first._

## Phase 1: Foundation ✅
- Postgres 17 (local) + migrations `db/migrations/001_init.sql`, `002_calls_response.sql` (`uv run askjev migrate`).
- Python project (uv), package `askjev` (src/askjev): config, db, Jev gateway client, local embeddings, CLI.
- **Jev via gateway** (`POST /v1/evaluate`, model `typesafe-ai/jev`, Noul = `boolean`): verified shape, no version
  exposed (logged as `typesafe-ai/jev@<date>` + generationId), cost $0, p50 383 ms / p95 727 ms end to end.
- **Noise floor** (20 repeats): Noul/Score std ≤ 0.011, Choice top-p std ≤ 0.027, near-tie Choices flip labels.
  Batch vs alone within noise. See docs/01-jev.md §1, §5 and `scripts/spike_jev.py`.
- Client: request-hash cache in `calls` + append-only `data/calls/*.jsonl`, token bucket (18 rps), 8 workers,
  backoff on 429/5xx, 24k-token request budget (under the 32k gateway context).
- Local embeddings: fastembed `BAAI/bge-small-en-v1.5` (384-d): 2 ms per query, ~900 texts/s.

## Phase 2: Tree (in progress)
- `tree/world.yaml`, `tree/self.yaml`, `tree/machine.yaml` (authored by subagents, reviewed): **249 nodes**:
  root, 3 hemispheres, 28 L1, 200 L2, 17 L3 (Big Five traits, MBTI dichotomies, MFQ-2 foundations, NBA, soccer clubs).
  All hand nodes `locked`. `uv run askjev tree` loads them with choice cards + embeddings.
- Known-path taxonomy test (Shopify product taxonomy, leaf-name only): depth 1 74%, depth 4 58% (docs/taxonomy-eval.md).
- Held-out routing eval: pending (authored/routing_eval.jsonl).

## Phase 3: Pipeline (in progress)
Stages implemented: source adapters → ingest (hints = deterministic placement) → place (Jev beam K=3) → screen
(filters + self-assessment) → answer bundle (self, human, 3 shuffles / reversed levels) → measure → rollup → mix
report; `walk`/`ask` single-question flows (ask ≈ 2 s: dedupe → fast placement → screen+answer → measure);
restructure (propose → authored labels → apply with accept rules). Adapters and authored banks are in progress.
