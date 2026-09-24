# Roadmap and decisions

## Decisions log (settled; don't reopen without Brian)
| Date | Decision |
|---|---|
| 2026-09-24 | Name: **askjev** ("Everything Asked" rejected) |
| 2026-09-24 | Framing: **understanding Jev** (capabilities + defaults + jaggedness) with indicators, **not a benchmark** |
| 2026-09-24 | Visibility: **private** (Brian + TypeSafe). Non-commercial/unclear-license data OK; exclude only YouGov, Kalshi, either.io |
| 2026-09-24 | **Code repo is public** (github.com/brian-w-zhang/askjev). Personal notes (`resources/references/notion/`, `resources/conversations/`) are gitignored and stay local. The data, answers, findings, and site stay private until TypeSafe has seen them |
| 2026-09-24 | Goal: a tree that houses every closed question humans or machines ask; Jev traverses it for placement, search, and growth |
| 2026-09-24 | Tree: **World / Self / Machine at 35 / 35 / 30**, 28 L1 roots (`02-tree.md` §3); topic is the tree, kind/shape are tags |
| 2026-09-24 | World backbone: **Vital Articles** + pruned category graph only where depth is needed + Wikidata leaves; IAB is tags only |
| 2026-09-24 | Factual share **15%** (categorical only) for per-topic calibration |
| 2026-09-24 | Model access: **only `AI_GATEWAY_API_KEY`**; Jev = `typesafe-ai/jev` (latest), with the served version logged |
| 2026-09-24 | **Search is instant-first:** local embeddings (`bge-small`, free) + pgvector + trigram in ~50 ms; one Jev rerank request after; tree animations are human-paced and independent of latency |
| 2026-09-24 | **Jev is the only gateway model.** No other LLM or embedding model on the gateway. Authoring (descriptions, synthetic questions, transforms) is done by Claude Code and its subagents; embeddings come from a local open model. No spending cap needed for Jev |
| 2026-09-24 | Stack: Python pipeline first; Next.js UI later |
| 2026-09-24 | **Proposed, awaiting Brian:** Postgres on Neon (ltree + pgvector) as the system of record, raw data and call logs as files, DuckDB for analysis only (`06-pipeline.md` §1) |
| 2026-09-24 | **Proposed, awaiting Brian:** questions are never tree nodes; follow-ups are `question_links`; overload handled by dedupe → split → group, as batch jobs (`02-tree.md` §8) |
| 2026-09-24 | **Proposed, awaiting Brian:** rewording "universes" as overlays on the one tree (same nodes and question ids, transformed probe text); they replace the paraphrase experiment (`05-experiments.md` §1) |
| 2026-09-24 | **Proposed, awaiting Brian:** per-question core metadata + screen request / answer bundle (`03-questions.md` §8) |

## M0: Setup
- [x] Docs, resources (transcript, Notion pages, full TypeSafe docs archive + digest)
- [x] `AI_GATEWAY_API_KEY` in `.env`; Jev found on the gateway as `typesafe-ai/jev`
- [x] Local Postgres 17 (Homebrew) running, DB `askjev` with ltree/vector/pg_trgm, `DATABASE_URL` in .env
- [ ] Apply `db/migrations`
- [ ] Spike: the gateway request/response shape (probabilities, confidence, served version)
- [ ] Spike: determinism noise floor and batch invariance (`05-experiments.md` §0)

## M1: Tree skeleton
- [ ] Sample questions per L1 (all three primitives, both frames, mixed kinds/shapes) to sanity-check the roots
- [ ] Hand-write root → 3 hemispheres → 28 L1 → ~200 L2 (description, not_for, examples) in `tree/`
- [ ] Known-path taxonomy test (CPC, Shopify, MeSH, SIC) + traversal check; fix descriptions

## M2: Pipeline + the 10k slice
- [ ] Jev client (gateway), append-only call log, request-hash cache
- [ ] Screen request, dedupe, answer bundle, measure, rollup; restructure job (split/group/grow)
- [ ] Adapters: IPIP, WYR, GlobalOpinionQA, Scruples, MFQ, Moral Machine sample, NBA pairwise, TypeSafe doc seeds + 2-3 machine datasets
- [ ] Run stages end to end (`06-pipeline.md` §4); mix report against `03-questions.md` §2

## M3: Experiments + findings
- [ ] Starter universes on a stratified 5k sample (terse, verbose, old-english, synonyms, typos, statement-form, french, negated)
- [ ] Experiments 1-11 on the slice; findings notebook
- [ ] Coverage test; first growth round
- [ ] Draft 3-5 findings in the standard format

## M4: UI
- [ ] Sunburst + question cards + findings page (`07-ui.md`)
- [ ] Ask box (private)

## M5: Outreach
Plan (from `resources/references/notion/become-typesafe-first-intern.md`): apply to "Member of Staff:
Create your own role", then send a short Discord DM to Sasha Sheng linking this one project.
- [ ] Send the findings privately to TypeSafe; ask about the "Jev" name and anything they want held back
- [ ] Anything public happens only after they've seen it and agreed

## M6: Scale (after outreach, or alongside it)
- [ ] 100k: Vital L3-L4, the remaining core datasets, G5 banks, the synthetic method with round-trip filtering
- [ ] 1M: Vital L5, Wikidata leaves, high-volume datasets, machine datasets at scale, jaggedness mining

## Open questions
- Local embedding model: `BAAI/bge-small-en-v1.5` (384 dims); upgrade only if the search-recall test is poor
- Subtree-sample option values vs opaque keys for traversal (`05-experiments.md` §10)
- Moral Machine sampling unit; Eurobarometer wave selection; which machine datasets per L2
