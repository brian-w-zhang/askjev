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

## Phase 2: Tree ✅
- `tree/world.yaml`, `tree/self.yaml`, `tree/machine.yaml` (authored by subagents, reviewed): **249 nodes**:
  root, 3 hemispheres, 28 L1, 200 L2, 17 L3 (Big Five traits, MBTI dichotomies, MFQ-2 foundations, NBA, soccer clubs).
  All hand nodes `locked`. `uv run askjev tree` loads them with choice cards + embeddings.
- Known-path taxonomy test (Shopify product taxonomy, leaf-name only): depth 1 74%, depth 4 58% (docs/taxonomy-eval.md).
- **Held-out routing eval ✅** (332 questions written for known nodes, never shown to Jev; 85 are boundary cases):
  **91.0% placed at exactly the intended node**, 0.9% wrong hemisphere; world 95.5%, self 90.0%, machine 87.4%;
  boundary cases 92.9%. Confusions are near-siblings (e.g. research.qualitative_coding ↔ support.intent_topic).
  Full report: docs/routing-eval.md.

## Phase 3: Pipeline + 10k slice ✅
**10,780 canonical questions**, all placed, 10,753 answered (27 failed on transient gateway errors and are retried
on the next run). Every question went through the screen request (filters + Jev self-assessment) and the answer
bundle (self + most-people frame + shuffles / reversed levels): **~40k probes answered**. 805 hidden by the content filter
(political / sensitive / duplicate), never deleted.

Sources (25 adapters + 4 authored banks + menus): IPIP (+ Open Psychometrics norms), OEJTS, MFQ-2/30, Scruples,
WYR (either.io votes), Jester, ProtoQA, GlobalOpinionQA (per-country), TruthfulQA, OpenTDB, Manifold (resolved),
Lancaster norms, Wikidata NBA pairs + facts, TypeSafe docs seeds (exact cookbook requests decoded from playground
links), Banking77, SMS spam, in-the-wild jailbreaks, emotion, SciFact, UNFAIR-ToS, Financial PhraseBank, Amazon
reviews, MS MARCO relevance, Rosetta code language; G5 synthetic banks (Jev round-trip accept rates 74-90%) and
G2 menu templates. Human distributions on ~2,200 questions; ground truth on ~4,600.

Throughput: screen ≈ 24 questions/s, answer ≈ 15 questions/s at a 24-question request cap (larger gateway batches
intermittently 503). Pipeline pass over 3k new questions ≈ 6 min.

Mix vs targets:
```
TOTAL canonical questions: 10780  placed: 10780  answered: 10753  hidden (flagged): 805

HEMISPHERE        actual   target
  world            39.5%   35.0%   (4256)
  self             32.7%   35.0%   (3524)
  machine          27.8%   30.0%   (3000)

KIND (world/self)  actual   target
  personality       8.3%    9.0%   (896)
  values           14.4%   10.0%   (1556)
  taste            14.2%   15.0%   (1535)
  evaluative        7.5%    9.0%   (805)
  social            8.2%    8.0%   (888)
  factual          15.1%   15.0%   (1624)
  forecast          1.6%    1.0%   (176)
  perception        2.8%    3.0%   (300)
  machine shapes: classify=736, detect=1127, extract=18, rank=201, route=423, score=247, verify=248

L1 ROOT               actual   target
  machine.ai_systems        4.7%    5.0%   (508)
  machine.code              2.0%    3.0%   (211)
  machine.commerce          1.9%    2.0%   (203)
  machine.documents         0.4%    1.0%   (40)
  machine.finance           2.0%    2.0%   (214)
  machine.legal             1.9%    2.0%   (200)
  machine.people            0.1%    2.0%   (16)
  machine.research          4.7%    3.0%   (507)
  machine.search            2.0%    3.0%   (217)
  machine.support           4.2%    3.0%   (455)
  machine.trust_safety      4.0%    4.0%   (429)
  self.lifestyle            9.2%    8.0%   (991)
  self.love                 3.9%    5.0%   (425)
  self.mind                 3.2%    5.0%   (340)
  self.personality          8.3%    8.0%   (898)
  self.values               8.1%    9.0%   (870)
  world.arts                4.1%    5.0%   (442)
  world.food                1.6%    3.0%   (177)
  world.future              1.6%    1.0%   (175)
  world.health              1.7%    2.0%   (185)
  world.history             1.8%    3.0%   (196)
  world.money               2.5%    2.0%   (269)
  world.nature              3.2%    3.0%   (348)
  world.places              1.3%    3.0%   (135)
  world.science             3.3%    3.0%   (356)
  world.society            10.1%    3.0%   (1093)
  world.sports              6.1%    4.0%   (658)
  world.tech                1.8%    3.0%   (198)

SOURCE                 n    truth  human
  truthfulqa              817    817      0
  globalopinionqa         815      0    815
  g5_self_lifestyle_traits    775      0      0
  g5_self_love_mind       725      0      0
  scruples                600      0    600
  ipip                    599      0     49
  g5_world_a              516    111      0
  opentdb                 500    500      0
  wyr                     500      0    500
  g5_world_b              455     96      0
  sms_spam                400    400      0
  banking77               400    400      0
  jailbreaks              400    400      0
  nba                     399    100      0
  g2_menus                310      0      0
  typesafe_seeds          300    236      0
  emotion                 300    300      0
  lancaster               300      0    300
  scifact                 200    200      0
  code_lang               200    200      0
  msmarco_relevance       200    200      0
  financial_phrasebank    200    200      0
  amazon_reviews          200    200      0
  unfair_tos              200    200      0
  protoqa                 150      0    150
  manifold                100    100    100
  jester                  100      0    100
  mfq                      66      0      0
  oejts                    51      0      0
  ask-box                   2      0      0
```
Known imbalances (addressed in phase 6): world.society is over target (survey + TruthfulQA items land there);
machine.people and machine.documents are thin (few public labeled datasets with short inputs).

## Phase 4: Frontend ✅
`web/` Next.js 16 app (react-three-fiber constellation tree, custom GLSL edge shader with traveling light pulses, bloom,
instanced stars, eased camera fly-to, lazy rings, labels with collision hiding). Instant search (local bge-small in
Node via transformers.js, **parity cosine 0.999999** with Python/fastembed using CLS pooling) + pgvector + trigram:
**p50 18 ms** in the browser; one background Jev rerank; "Jev's path" second light that forks where Jev and the
embeddings disagree. Question cards (distribution bars, Score bands, frame toggle, stability, Jev self-assessment,
human overlay, truth, thread, raw calls), node view, color-by-indicator, filters, private ask box (~2-7 s).
**Verified with headless Playwright** (web/scripts/verify.mjs): 0 errors, 60 fps idle / 59-60 fps during path
animation, 14 screenshots in docs/screenshots/. Run: `cd web && npm run build && npm start`.

## Phase 5: Hardening ✅
| Check | Result | Doc |
|---|---|---|
| Held-out routing | 91.0% exact node | docs/routing-eval.md |
| Known-path taxonomy (Shopify, name only) | 74% depth 1, 58% depth 4 | docs/taxonomy-eval.md |
| Coverage (1,000 Quora questions) | 89.5% homed at L2+ (was 83% before adding 6 gap nodes); **3% stuck at root/hemisphere**; 97.4% confident | docs/coverage-test.md |
| Restructure round | everyday_ethics split into Family Conflicts / Friends, Dating & Social Life: **accepted** (451 moved, median separation 13×, 0% sibling moves); gap growth added 6 nodes, 535 questions re-placed | tree_events |
| Search recall (200 reworded queries) | embeddings **76.5% @1 / 91% @5 / 95.5% @20**; **+ Jev rerank 90.5% @1**; 5 ms p50 (Python) / 18 ms (browser) | docs/search-recall.md |
| Dedupe (300 labeled Quora pairs) | Jev F1 0.66 (P 0.63 / R 0.69) vs embedding-only 0.59; contrastive-criteria variant measured worse (0.54) and was reverted | docs/dedupe-eval.md |
| Bulk dedupe | 2 cross-source duplicates linked + hidden | question_links |

Coverage note: the remaining non-homed questions are mostly general questions correctly held at an L1 via `here`
(e.g. "Why do we get hurt when we love?" → Love & Relationships) or noise/off-scope (sexual content has no node by design).
