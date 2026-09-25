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
  toxicity_harassment, personal_data, paper_screening, reranking, issue_triage...). The 965 Vital L3 topic
  nodes hold ≤ 2 questions each; the Vital L4 entities mostly landed on hand nodes instead.

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
- **Synthetic ≤ 15% per wave**, and only for nodes no real source covers. Rules for new banks:
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
- **Tree fixes allowed in wave 1:**
  - Re-home Vital L4 entity questions under their Vital L3 topic node when the adapter recorded the parent.
    Check a sample of 200 first. This moves questions, not nodes.
  - Add hand nodes for consumer and practical decisions ("should I buy X or Y", home and DIY, tenant and
    consumer rights) and internet culture, if Quora placement shows they have no home.
