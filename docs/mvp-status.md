# MVP status

_Living status of the autonomous build (docs/09-mvp-plan.md). Newest first._

## Expansion (after the MVP)
The corpus is growing toward 1M in gated waves (`docs/10-expansion.md`); per-wave numbers are in `docs/expansion-log.md`.
**2026-09-25, wave 1 gated: 239,319 questions** (World 37.3% / Self 35.3% / Machine 27.3%), 1,365 nodes, 89% of new
questions anchored. **Wave 2 gated: 299,863** (World 36.5 / Self 32.9 / Machine 30.6). **Wave 3 gated: 372,590** (World 37.3 / Self 33.3 / Machine 29.4). **Wave 4 gated: 478,407** (World 40.0 / Self 30.7 / Machine 29.3). **Waves 5-6 gated: 612,246** (World 36.8 / Self 28.2 / Machine 35.0; 71% anchored). **Waves 7-9 gated: 937,967** (World 35.1 / Self 31.9 / Machine 33.0; 87% anchored). The last synthetic banks are in the round-trip queue (projected ~1.01M).

## Final summary (2026-09-24)

**Phases 1-5 complete and verified; phase 6 grew the corpus to 99,458 canonical questions (99,457 answered by Jev).**

| | |
|---|---|
| Questions | **99,458** (World 41.7% / Self 31.8% / Machine 26.6%; targets 35/35/30) |
| Tree | **1,319 active nodes**: 3 hemispheres, 28 L1, 206 L2 (hand, locked), 965 Vital topic nodes, 99 grown by restructure |
| Jev work | 312k probes answered, 211k cached calls (every call hashed, logged, never re-sent), cost $0 on the gateway |
| Human data | 38,673 human distributions (surveys × country, instrument norms, votes, market prices); ~36k questions with ground truth |
| Routing (held-out 332) | 91.6% correct branch on the final tree (exact 64% + deeper child 28%) |
| Search | 76.5% recall@1 from local embeddings → **90.5% @1 with one Jev rerank**; 30-65 ms in the browser |
| UI | 60 fps constellation, human-paced path animations, Jev-path fork, cards, ask box; Playwright-verified |
| Indicators (preview) | ECE 0.058 over 36k ground-truth items; no position bias; Machine research/search/commerce overconfident (ECE ≈ 0.23-0.27); see docs/findings-preview.md |

**How to run:** `uv run askjev pipeline` (Python pipeline; Postgres 17 local) · `cd web && npm run build && npm start`
(UI at http://localhost:3000) · evals in `scripts/` · regenerate reports with `scripts/corpus_report.py` and
`scripts/findings_preview.py`.

**Known issues**
- Kind mix at 100k scale leans values/social (AITA, Social Chemistry, Vital "have most people heard of X?") and is short
  on personality (4.1% vs 9%) and factual (10% vs 15%). The next lever is more categorical-fact generators (Wikidata G4) and
  personality items with human norms.
- Round-trip acceptance for synthetic banks fell to 55-60% in dense Self areas (siblings like Values ↔ Love overlap);
  rejects are kept in authored/rejected/ for review.
- Fast placement (84.9%) is less accurate than the beam walk (90.1%), so bulk placement uses beam; the ask flow uses fast.
- The gateway doesn't expose Jev's version (logged as `typesafe-ai/jev@date`); gateway batches > ~24 questions intermittently 503.
- Dedupe precision is moderate (F1 0.66 on Quora pairs); only cross-source pairs in the same node are auto-linked.
- Some noisy sources: emotion labels (hashtag-derived), MS MARCO false negatives, synthetic FEBRL person records, and BoolQ
  facts as of 2018.
- The universe switcher UI and Jev-powered ask linter aren't built yet (only the base universe exists).
- Not yet ingested: Moral Machine (large OSF file), WVS/ESS/GSS microdata (login or heavy processing), MovieLens, PhilPapers.

**Next steps**
1. **Experiments → findings** (docs/05-experiments.md): run the rewording universes on a stratified 5k sample (terse,
   verbose, old-english, synonyms, typos, statement-form, french, negated), transitivity/Bradley-Terry on the 23 GOAT
   categories, decoy/IIA triples, repeats for noise, and the calibration-by-L1 and metacognition analyses at full scale.
   Then write the 3-5 findings.
2. **Rebalance kinds**: Wikidata categorical facts (G4) and personality items with norms.
3. **Universe UI** (switcher + drift coloring), and the ask-box linter.
4. **Outreach**: send the findings privately to TypeSafe (docs/08-roadmap.md M5).

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

## Phase 6: Scale ✅ (≈ 99,458 questions; 1M not attempted, see below)
What was added (all public downloads or subagent-authored; Jev is the only model called):
- **World:** Vital Articles (1,001 Level-3 articles → **965 topic nodes**; 9,509 Level-4 articles → 19,018 entity
  questions: "Would most adults have heard of X?" + "How important is X to its field?"), BoolQ (6,000 real
  Google yes/no queries with truth), OpenTDB full sweep (2,805), Lancaster norms (2,000), Manifold (600 resolved,
  midlife market price as the human distribution), **22 GOAT pairwise categories** (6,600: films, TV series, games,
  books, albums, bands, singers, painters, paintings, soccer players/clubs, tennis, F1, cities, countries,
  cuisines, dishes, board games, car brands, scientists, programming languages, mammals).
- **Self:** Open Psychometrics (29 instruments, 1,018 new items + human data for 216 IPIP items; 1,353 human
  distributions), AITA anecdotes (8,000 with verdict distributions), Social Chemistry (6,000 pooled agreement),
  ETHICS (4,000 with truth), and authored banks (love, mind, taste, personality, values) through the round-trip filter
  (60-75% accept at this density).
- **Machine:** all 11 labeled datasets scaled (banking77 3k + 2 extra templates, SMS 3k, UNFAIR-ToS 4k + clause types,
  Amazon 4k + topic, MS MARCO 4k + relevance levels, emotion, SciFact, FPB, code, jailbreaks) + new
  entity-resolution / person-matching / occupation data (people_docs).
- **Tree:** gap growth (6 nodes), Vital L3 topics (965), restructure round 2 (**39 accepted**: 5 groupings incl.
  continents / solar system / engineering domains, 34 splits; 1 rejected by the sibling-move rule). Tree: 1,319 active
  nodes. `askjev repair-paths` verifies ltree integrity (0 violations).
- **Performance at scale:** answer stage ≈ 12 questions/s (machine questions need one request per input), screen ≈ 35/s;
  a full pass over ~45k new questions ≈ 75 min. Web search 30-45 ms at ~95k (trigram via GiST KNN).

Why not 1M: (1) **throughput**: at the public rate limit (1,200 req/min) and ~12 answered questions/s,
1M questions × ~5 probes ≈ 24 hours of Jev calls, before screening; (2) **quality**: the remaining public sources with
human data are exhausted or login-gated (WVS/ESS/GSS microdata), and more volume would come from templates/synthetic
text, which would dilute the human-anchored and ground-truth share that makes findings credible. Path to 1M:
enterprise rate limits + Vital Level 5 (50k entities) + full Wikidata leaf generation + more machine datasets, with the
pipeline unchanged (it is chunked, resumable, cached).

Final mix:
```
TOTAL canonical questions: 99458  placed: 99458  answered: 99457  hidden (flagged): 5117

HEMISPHERE        actual   target
  world            41.7%   35.0%   (41441)
  self             31.8%   35.0%   (31578)
  machine          26.6%   30.0%   (26439)

KIND (world/self)  actual   target
  personality       4.1%    9.0%   (4057)
  values           16.5%   10.0%   (16407)
  taste            12.4%   15.0%   (12367)
  evaluative       11.0%    9.0%   (10897)
  social           16.8%    8.0%   (16686)
  factual          10.0%   15.0%   (9929)
  forecast          0.7%    1.0%   (676)
  perception        2.0%    3.0%   (2000)
  machine shapes: classify=7896, detect=7614, extract=18, rank=3083, route=2002, score=3332, verify=2494

L1 ROOT               actual   target
  machine.ai_systems        1.3%    5.0%   (1308)
  machine.code              1.5%    3.0%   (1511)
  machine.commerce          3.1%    2.0%   (3098)
  machine.documents         1.2%    1.0%   (1240)
  machine.finance           2.1%    2.0%   (2040)
  machine.legal             3.1%    2.0%   (3090)
  machine.people            1.3%    2.0%   (1316)
  machine.research          2.7%    3.0%   (2653)
  machine.search            3.1%    3.0%   (3099)
  machine.support           4.1%    3.0%   (4055)
  machine.trust_safety      3.0%    4.0%   (3029)
  self.lifestyle            4.1%    8.0%   (4051)
  self.love                 6.1%    5.0%   (6055)
  self.mind                 1.9%    5.0%   (1891)
  self.personality          3.1%    8.0%   (3068)
  self.values              16.6%    9.0%   (16513)
  world.arts                7.5%    5.0%   (7467)
  world.food                2.3%    3.0%   (2259)
  world.future              0.7%    1.0%   (675)
  world.health              1.5%    2.0%   (1460)
  world.history             2.4%    3.0%   (2410)
  world.money               0.9%    2.0%   (938)
  world.nature              4.2%    3.0%   (4140)
  world.places              4.6%    3.0%   (4566)
  world.science             4.9%    3.0%   (4861)
  world.society             5.3%    3.0%   (5280)
  world.sports              4.4%    4.0%   (4386)
  world.tech                2.7%    3.0%   (2716)

SOURCE                 n    truth  human
  vital4                19018      0      0
  scruples_anecdotes     8000      0   8000
  goat_pairs             6600      0      0
  social_chem            6000      0   6000
  boolq                  6000   6000      0
  ethics_cs              4000   4000      0
  banking77              4000   1979      0
  amazon_reviews         3095   2267      0
  unfair_tos             3090   3051      0
  msmarco_relevance      3082   2273      0
  sms_spam               3000   2044      0
  opentdb                2805   2805      0
  people_docs            2500   2500      0
  g5_p6_taste            2174      0      0
  financial_phrasebank   2026   2026      0
  emotion                2000   2000      0
  lancaster              2000      0   2000
  g5_p6_taste2           1627      0      0
  code_lang              1500   1500      0
  jailbreaks             1200   1200      0
  openpsych              1018      0   1018
  wyr                    1000      0   1000
  g5_p6_love1             899      0      0
  g5_p6_mindlove3         875      0      0
  g5_p6_values2           872      0      0
  g5_p6_personality       819      0      0
  truthfulqa              817    817      0
  globalopinionqa         815      0    815
  g5_self_lifestyle_traits    775      0      0
  g5_self_love_mind       725      0      0
  g5_p6_love2             688      0      0
  scifact                 646    646      0
  manifold                600    600    600
  scruples                600      0    600
  ipip                    599      0    265
  g5_p6_mind1             566      0      0
  g5_p6_personality2      542      0      0
  g5_p6_mind2             536      0      0
  g5_world_a              516    111      0
  g5_world_b              455     96      0
  nba                     399    100      0
  g2_menus                310      0      0
  typesafe_seeds          300    236      0
  protoqa                 150      0    150
  jester                  100      0    100
  mfq                      66      0      0
  oejts                    51      0      0
  ask-box                   2      0      0
```
