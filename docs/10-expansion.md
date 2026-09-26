# Expansion: 100k → 1M in waves (the /goal spec)

The corpus grows from ~100k to 1M canonical questions in **waves of ~100k**. Each wave is sourced,
answered by Jev, measured, and committed before the next one starts. This file is the plan and the source
queue; `docs/expansion-log.md` is the running record (one section per wave). `CLAUDE.md` and
`docs/00-09` still hold; the hard rules in `09-mvp-plan.md` apply unchanged.

## 1. Starting point (audit, 2026-09-24)
99,458 questions, 1,319 active nodes, all answered. What the audit found:

- **Rows ≠ distinct questions.** 52k distinct question texts. Machine is **192 texts over 26k inputs**
  (one template per dataset, one dataset per node). Vital4 is 19k rows from **2** templates.
  Templated sources sit at >0.95 nearest-neighbour cosine; the synthetic banks are the most varied (0.80-0.84).
- **Provenance:** human-written question text 25%, real items in a template 36%, real machine inputs in a
  template 26%, synthetic (Claude-authored) 12%. 38% of the corpus has neither truth nor human data.
- **Human data is uneven.** Strong: IPIP / Open Psychometrics (n ≈ 48k-600k), WYR, Jester, Lancaster,
  Manifold, GlobalOpinionQA. Weak: Social Chemistry (8 annotators *estimating* agreement), AITA (~21
  comments), Scruples dilemmas (n=10).
- **Saturated** (Jev ≥ 96% correct, nothing new to learn from more rows): ETHICS commonsense, code_lang,
  SMS spam, synthetic factual (`g5_world_*`, 100%). **Most informative:** emotion (52%), Amazon (59%),
  Manifold (62%), MS MARCO (65%), and every Self bank (low confidence, frame gap 0.2-0.3).
- **Synthetic banks:** good variety and signal, but no anchor; the `other` option wins 26-35% of taste and
  personality Choices (a non-answer); ~260 items ask Jev about a biography it doesn't have
  ("your grandparents", "your childhood bedroom").
- **Overloaded:** `self.values.everyday_ethics` holds 11.1k (35% of Self); single-dataset machine nodes hold 2-4.5k each.
- **Thin:** `world.tech.ai` 13, health (mental health, nutrition, sleep < 60 each), money (careers,
  entrepreneurship, personal finance, real estate < 70), `self.mind` 1.9% vs 5%, `self.personality` 3.1% vs 8%,
  `self.lifestyle` 4.1% vs 8%, kind personality 4.1% vs 9%, factual 10% vs 15%.
- **Empty:** 45 Machine leaves have < 10 questions (hallucination_citation, model_routing, function_calling,
  toxicity_harassment, personal_data, paper_screening, reranking, issue_triage...). The 965 Vital L3
  nodes are single entities (Gandhi, the Yangtze), each holding its own 2 entity questions by design; they
  are leaves, not topic groupings, so Vital L4 entities correctly sit on the hand topic nodes.

## 2. How the MVP run worked, and what changes
The MVP ran **source a batch → ingest → `askjev pipeline`** (place → screen → answer → dedupe → measure →
rollup → mix), then the next batch. Every stage works on whatever is pending, is chunked and resumable,
and skips cached request hashes. That stays. What changes:

**Stream, don't stockpile.** We don't source 1M first and answer later. Jev is the bottleneck
(~12 answered questions/s under the 1,200 req/min limit, so ~2.5-4 h of Jev per 100k), and sourcing
(adapters, downloads, authoring) is CPU, network, and subagent work that overlaps with it. Two lanes run
at once:
- **Jev lane:** one process loops `askjev pipeline` over pending questions and never sits idle.
- **Sourcing lane:** subagents write and verify adapters and authored banks for the *next* batch and ingest
  them as they're ready. Keep at least one batch queued ahead of Jev.

Answering per wave also means each wave's measurements (saturation, confidence, frame gap) steer the next
wave's source choices, and stopping at any point leaves a complete, consistent corpus.

## 3. Waves and the gate
Wave *k* takes the corpus from ~*k*00k to ~(*k*+1)00k. A wave is done (the **gate**) when:
1. Every question in it is placed, screened, and answered (≤ 0.1% failed and retried).
2. `dedupe`, `measure`, `rollup` have run; `repair-paths` reports 0 violations.
3. A restructure pass split every node over the node cap (§4), within the allowed tree changes (§6).
4. `scripts/corpus_report.py` and `askjev mix` are regenerated, and a wave section is added to
   `docs/expansion-log.md`: counts vs targets, what was added, per-source accuracy/confidence, sources
   dropped or capped and why, known issues.
5. The star layout is regenerated (`uv run python scripts/star_layout.py`) so the map shows the new stars.
6. Committed and pushed (§6).

Only then does the next wave start. Stop when the corpus reaches 1M, or when the queue (§5) can't fill
another wave under the mix rules. In that case, write down why in the log.

## 4. Mix rules (every wave)
- **Hemispheres converge on 35 / 35 / 30.** Each wave overweights whatever is under target. World is 41.7%
  today, so the early waves lean Self and Machine.
- **Kinds converge on `03-questions.md` §2.** Priority shortfalls: personality, factual, taste. No new
  rows for values/social from the already-large sources.
- **Template cap: ≤ 5,000 rows per question text** across the corpus (≤ 3,000 for a Machine template).
  Sources already over the cap (Vital4's two templates, AITA, Social Chemistry, ETHICS commonsense) are
  frozen. More volume comes from *new* question texts, not more rows of old ones.
- **Anchored share ≥ 60% per wave**: the question has ground truth or a human distribution.
- **Synthetic ≈ 15-20% per wave (a guideline, not a hard cap; Brian, 2026-09-25)**, used where no real source covers a node; Self may go higher while real Self data is scarce. Rules for new banks:
  - No `other` option unless the list really can't be exhaustive.
  - No questions about a personal biography (childhood, family, body, hometown).
  - No synthetic factual questions (use a real source with truth).
  - Score levels are situations, per `01-jev.md` §7.
  - Everything goes through the round-trip filter.
- **Node cap: 1,500 direct displayable questions.** Above that, the restructure pass proposes splits
  into children (by cluster or by the dataset's own labels, e.g. machine label families).
- **Saturation rule:** if a source's first 1,000 answered questions show ≥ 95% correct and ≥ 60%
  decisive (p_top > 0.95), stop scaling it.
- **Content filter as before:** contested politics and sexual content flagged and hidden, never deleted.
  Excluded sources stay excluded (YouGov, Kalshi, either.io; decisions log).

## 5. Source queue
Pick from the top that fit the current wave's gaps; record each source in `04-datasets.md` with a verdict
when it's added. Public downloads only (HF datasets, OSF, GitHub, Wikidata SPARQL); skip anything behind
a login or click-through agreement. Yields are targets, subject to the caps.

**Wave 1 (→ ~200k): fill empty nodes, fix kinds, add real asked questions**

| Lane | Source | Yield | Anchor | Home |
|---|---|---|---|---|
| Machine | Civil Comments / Jigsaw toxicity | 3k × 2 templates | truth + annotator fraction | trust_safety.toxicity_harassment |
| Machine | CLINC150 (incl. out-of-scope), MASSIVE en | 3k each | truth | support.routing, support.commands |
| Machine | HaluEval (QA, dialogue, summarization) | 3k × 3 | truth | ai_systems.hallucination_citation, extraction_verification |
| Machine | ai4privacy PII masking | 3k | truth | trust_safety.personal_data |
| Machine | LEDGAR / CUAD clause types | 3k | truth | legal.policy_checks, legal clauses |
| Machine | AG News, DBpedia-14, Yahoo Answers topics | 3k each | truth | documents.taxonomy_classification, commerce.listing_categorization |
| Machine | GitHub issue reports (bug / feature / question) | 3k | truth | code.issue_triage, pr_classification |
| Machine | arXiv / paper-abstract classification | 3k | truth | research.paper_screening |
| Machine | Phishing / Enron spam email | 3k | truth | finance.fraud_indicators |
| Machine | Function-calling sets (request ↔ call match, with perturbed negatives) | 3k | truth | ai_systems.function_calling, tool_call_verification |
| World | MMLU (all 57 subjects, hint by subject) | ~15k | truth | per-subject nodes |
| World | ARC, SciQ, OpenBookQA, StrategyQA, BoolQ remainder | ~15k | truth | science, nature, history... |
| World | Quora closed questions (`data/raw/quora`, ~92k closed-form; regex, then Jev screen) | ~15k | none (real asked) | beam placement |
| Self | IPIP full item pool (~3.3k items; raw on disk) + remaining Open Psychometrics instruments | ~5k | human norms where available | personality |
| Self | Social IQa | ~8k | truth | love / etiquette / social |
| Self | DailyDilemmas, MoralChoice | ~4k | value tags / human labels | values (not everyday_ethics) |
| Self/World | Synthetic banks for thin nodes: mind, lifestyle, personality, `tech.ai`, health, money, future | ≤ 15k | none | the thin nodes |

**Later waves (queue, roughly in order)**
- **Real asked questions:** the rest of Quora; WildChat closed-ended user turns (public HF); Stack
  Exchange titles in closed form (archive.org dumps); Yahoo Answers closed-form titles.
- **Factual with truth:** Wikidata categorical facts (G4: continent, country, field, era, genre per
  entity) at scale; MedMCQA (≤ 5k per subject); CommonsenseQA, WinoGrande; per-subject caps.
- **Human data:** GSS public data files, Moral Machine (OSF), more Open Psychometrics norms, Manifold's
  next pools.
- **Taste with signal:** more GOAT categories; MovieLens / Goodreads rating-based pairs (the human
  preference comes from ratings).
- **Volume, capped:** Vital Level 5 entities, ETHICS justice / deontology / virtue / utilitarianism (new
  texts; commonsense stays frozen), Social Chemistry only as new templates.

## 6. Running next to the frontend agent
Another session is changing the UI at the same time. The expansion agent must not break it.
- **Files.** The expansion agent owns `sources/`, `authored/`, `tree/*.yaml` (additions),
  `src/askjev/` (except layout code), `scripts/` (except `star_layout.py`), `docs/10-expansion.md`,
  `docs/expansion-log.md`, `docs/corpus.md`, `docs/04-datasets.md`. It never edits `web/`,
  `docs/07-ui.md`, `scripts/star_layout.py`, or `db/migrations/004_*`.
- **Commits.** Commit only its own paths: `git commit -m "..." -- <paths>`. Never `git add -A` or
  `commit -a`. For a shared file with someone else's uncommitted edits (`08-roadmap.md`, `CLAUDE.md`),
  stage only its own hunk (`git diff` → keep own hunk → `git apply --cached`), or leave it for the next wave.
- **Database.** Migrations are additive only and numbered from `005`. No drops or renames.
- **Tree.**
  - New nodes may be added: splits, grows, new hand nodes for real gaps.
  - Existing node ids and paths never change. No `group` or retire operations while the UI is in flux.
- **Jev.** One pipeline process at `ASKJEV_RPS=16` leaves headroom for the UI's search rerank and ask box.
- **Tree additions allowed in wave 1:** hand nodes for consumer and practical decisions ("should I buy X or
  Y", home and DIY, tenant and consumer rights) and internet culture, if Quora placement shows they have no home.

## 7. Decisions made during the expansion
- **Template split** (`askjev template-split`, labels in `authored/template_nodes.yaml`): a node over the cap whose load is
  a high-volume template gets one grown child per template *that has an authored label*. The label is the judgment that the
  template is a topic: Machine dataset templates, pairwise taste sets (movie, book, board game, anime, music, beer matchups),
  and World fact templates about a topic (river lengths, city populations...). Generic templates ("have most adults heard of
  X?", GOAT pairs, "which century") stay on their topic node. Moves are deterministic and logged in `tree_events`.
- **Single-template nodes** (one Machine dataset, one pairwise set, one AITA template) are bounded by the template cap
  (3,000 Machine / 5,000 otherwise), not the node cap: splitting one template by its answer labels would leak the answer.
- **Descend** (`scripts/descend.py`): questions an adapter hint placed deterministically on an overfull *parent* go back
  to Jev's beam walk starting at that parent, so they settle into the right child or stay (`here`). Ids and answers don't change.
- **Ingest** skips rows already stored and embeds in length order (≈2× faster); NUL characters are stripped.
- **Jev lane** runs at `ASKJEV_RPS=16` with 40 workers (8 or 20 workers left the bucket half empty because screen
  requests are slow); round-trip filtering of synthetic banks runs beside it at 3 rps.
- **Source-level calls:** `moral_disputes` (MMLU) stays World factual (it asks what philosophers argue); Quora keeps world
  ≤ 60% in wave 1 and adds world-only items in wave 2; Ecchi and Hentai anime are dropped rather than flagged; beer pairs capped
  at 2,000 (many craft beers aren't widely known); scruples capped at 2,000 and moral_stories at 3,000 because values is over
  target; the weakest synthetic Score shape ("How should X handle Y" with one sensible level) is dropped before round trip.
- **Round-trip walk starts at the intended hemisphere** (2026-09-25): the author fixes the hemisphere, so the root step only spent a
  call (~20% of round-trip cost). The walk is still blind below it; a bank item can no longer be rejected for landing in another
  hemisphere (rare in earlier banks; rejects were almost all sibling nodes). The one-call fast path was tested as a cheaper
  round trip and rejected: on 500 W6 items it passed 60% of the beam walk's rejects and failed 12% of its accepts, because
  embedding candidates already sit next to the intended node. Round trips keep the beam walk.
- **Throughput** (2026-09-25): requests pack up to 64 questions / ~5k tokens (measured sweet spot; larger requests mostly 503);
  gateway pinned to TypeSafe's own provider; adaptive rate backs off 10% when > 30% of requests are throttled; packing several
  Machine inputs per request was tested and rejected (accuracy 84.5 → 82.5%).
- **Vital L3 nodes** are single entities (not topic groupings), so Vital L4 entities correctly sit on hand topic nodes;
  nothing to re-home (§1 corrected).

## 8. Coverage map and priorities for 500k → 1M (agreed with Brian, 2026-09-25)
Measured at 478k (World 40.0 / Self 30.7 / Machine 29.3; 71% anchored; 7.6% synthetic).

**Well covered (don't grow further unless a wave needs volume):** factual knowledge (20% vs 15%), moral dilemmas and values
(ETHICS, AITA, Moral Machine, Social Chemistry), entertainment taste pairs, arts and fictional characters, word-perception norms,
Machine text classification (spam, toxicity, intents, topics, sentiment, relevance, claims).

**Underrepresented vs targets:** personality 4.1% (9), Self › Love 2.8% (5), Self › Mind 2.6% (5), World › food 1.1 (3),
history 1.3 (3), sports 1.8 (4), tech 1.8 (3), money 1.4 (2); Machine › people 0.5 (2), finance 1.0 (2); Machine shapes extract
and rank; empty TypeSafe leaves (claims triage, KYC/AML, ad alignment, listing compliance, moderation enforcement, response
verification) with no public labeled data.

**Missing relative to what people actually ask:** real asked questions are only ~15% of the corpus; everything is English
(US/India skew); practical and consumer decisions have no node; health/personal advice and politics/religion are excluded or
hidden by design (kept that way); math and logic reasoning nearly absent; forecasting 1.1%.

**Priorities for waves 6+ (in this order):**
1. **Real asked questions**, the biggest mission gap: Stack Exchange and Yahoo remainders, Quora world pool, Reddit r/polls (with
   vote counts as human data, from public dumps), Natural Questions, more chatbot first turns, Metaculus/Manifold forecasts with
   resolutions. The anchored share may drift toward ~55-60% because of this; that is accepted and logged per wave.
2. **New hand nodes for practical decisions:** `world.money.buying_decisions` (which product or service to buy, is X worth it)
   and `world.society.everyday_how_to` (home, DIY, consumer rights, everyday practical judgments), fed by the real asked questions.
3. **Human-answer surveys behind a free login** (World Values Survey, European Social Survey, Pew, Eurobarometer): the best fix for
   Self and for non-US populations. The rules forbid signing up automatically; if Brian downloads them into `data/raw/<name>/`,
   they are ingested in the next wave.
4. **TypeSafe's empty Machine leaves:** realistic inputs authored by subagents, with labels decided at authoring time, marked
   `origin=synthetic` and `meta.synthetic_input=true`, counted inside the 15% synthetic cap, and reported separately (their labels
   are the author's judgment, not independent ground truth).
5. **A multilingual slice:** existing questions reworded into other languages as universes (overlays, never new questions), plus
   native-language real questions where the license allows.
6. **Kind gaps:** personality and Love/Mind through round-trip-filtered synthetic banks; food, history, sports, tech and money
   through real asked questions and new datasets; math/logic through a small closed-form reasoning set with truth.

## 9. Steering corrections after wave 5 (agreed with Brian, 2026-09-25)
At 564k: World 39.9 / Self 29.2 / Machine 30.8; factual ~21%, personality ~4.2%. Real asked questions (Stack Exchange, Yahoo)
turned out ~80% World factual, so prioritizing them pushed World and factual up and Self down.
- **Hold new World volume** (Yahoo top-up, MedMCQA, CommonsenseQA, further Stack Exchange) until World falls to ~36%.
- **Waves 6-7 are Machine + Self:** wave 6 = 40k Machine + the wave 6 Self bank; wave 7 = Reddit polls extended to every day
  (Self taste/opinion with vote shares) + a larger Self synthetic share.
- **Personality** grows through round-trip-filtered synthetic banks and public no-login surveys (Afrobarometer, PISA student
  questionnaires, the GlobalOpinionQA remainder, IPIP-NEO response data to anchor existing items). Login-gated surveys (WVS, ESS,
  Pew, GESIS) are ingested only if Brian downloads them; Claude does not create accounts or accept data licenses on his behalf.

## 10. Final sourcing plan to 1M at 35/35/30 (Brian, 2026-09-25)
End target ≈ 1.02M: **World ~350k · Self ~345-350k · Machine ~300k.** Measured at 584k: World 225k, Self 166k, Machine 193k.

| Hemisphere | Gap | Already queued | New sourcing |
|---|---|---|---|
| Self | +184k | Reddit polls extension (~28k Self), Self banks in round trip (~26k accepted), wave 9 banks (45k written, ~32k accepted) | **real**: Social Chemistry +20k (its freeze is lifted for Self balance), Social IQa +15k, Moral Machine +8k, Scruples remainder, behavioral-economics classics with published distributions (Many Labs, Kahneman-Tversky), moral vignettes with norms; **synthetic**: ~65k more written (personality, mind, love, values first), ~50k after round trip |
| World | +125k | 59k held (Stack Exchange, Yahoo, MedMCQA, CommonsenseQA), released as the World share allows | Wikidata facts/comparisons for thin L1s (sports, food, history, tech, nature) ~30k; synthetic evaluative/forecast for those L1s ~25k; new GOAT categories ~10k |
| Machine | +107k | wave 6 remainder ~22.5k | the running ~100k round, trimmed to ~85k at ingest, aimed at ai_systems, trust_safety, people, code, search, support, research (not documents, which is over) |

**Level-1 gaps at 1M (target from `03-questions.md` §2):** Self personality +50k, mind +35k, values +39k, love +27k, lifestyle +30k;
World sports +26k, food +21k, history +21k, nature +16k, tech +15k (society over); Machine ai_systems +29k, trust_safety +17k,
people +16k (documents over). **Missing types to add:** Self forecasts and evaluative judgments, behavioral-economics preferences
(risk, time, framing) with human data, forced trade-offs, World values.

## 11. Category review at 606k (2026-09-25)
94% of questions sit at depth ≥ 3. The top level (3 hemispheres, 28 L1s) covers what people ask; the gaps were one level down,
found by sampling the ~35k questions stuck at the root, a hemisphere or an L1:
- **New hand nodes:** History — Everyday Life in the Past, Economic & Money History, History of Science & Technology, Regional
  Histories; Sports — Rules & Officiating, Leagues, Teams & Transfers; Health — Health Claims & Remedies; Money — Business,
  Management & Marketing (plus the earlier Buying Decisions and Everyday Practical Questions).
- **Placement fixes:** 1,856 Social IQa items at Love's top level moved to Reading People (feelings/describe → Reading Feelings,
  the rest → Reading Motives); 2,202 word-norm items stuck at the root/hemispheres moved to the Word node; the questions at the root,
  the World hemisphere and the History/Sports/Money/Health/Society L1s re-walked by beam from where they sat.
- **Filter leak:** 356 demographic polls ("What color is your passport?") flagged `biographical` and hidden; the Reddit adapter's
  filter tightened for new rows.
- **Left as is:** Self, Arts, Places, Science and Machine are already fine-grained; Machine finance/people load is template children
  pending the wave 6 gate.

## 12. Coverage probe (2026-09-25)
Six context-free subagents wrote 666 closed questions (mundane, niche expert, absurd, edge, global, machine); each was matched
against the corpus by local embedding and walked down the tree by Jev (`scripts/probe_coverage.py`, report in `docs/coverage-probe.md`).
Mean nearest-neighbour similarity: mundane 0.835, edge 0.811, machine 0.773, absurd 0.765, niche 0.735, **global 0.697 (99% novel)**.
- **Content gaps:** culturally specific non-US/UK questions (exams, dishes, festivals, customs), the niche-expert long tail, and
  pure whimsy. → a ~12k global-cultures bank, a ~10k professions/expert-judgment bank, a ~1.5k shower-thoughts bank.
- **Structure gaps** (questions stuck at a hemisphere or L1): Machine lacked industry L1s → new **Healthcare & Clinical**, **Education
  & Grading**, **Operations, IoT & Logistics**; World lacked **Insurance & Risk** (money), **Libraries, Archives & Museums** (society)
  and **Shower Thoughts & Absurd Questions** (internet culture). Image, audio and camera inputs are out of scope (Jev reads text).
- The tree now has 31 L1s. The new Machine L1s take their share from documents (over target) so Machine stays ~30%.
