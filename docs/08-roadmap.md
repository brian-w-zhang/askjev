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
| 2026-09-24 | Gateway exposes Jev at `POST /v1/evaluate` (Noul = `boolean`) with **no version number**; we log `typesafe-ai/jev@<date>` + generationId |
| 2026-09-24 | Noise floor for reported effects: ±0.03 Noul/Score, ±0.08 Choice top-p; a label "flip" only counts when the base margin > 0.1 |
| 2026-09-24 | Stateless questions (and all screen questions) share a neutral state and are packed ~100+ per request (batch invariance measured within noise) |
| 2026-09-24 | Human frame = the question plus a `perspective` field ("choose the answer most people would give"), unless the source provides `human_text` |
| 2026-09-24 | Stability probes: 3 option shuffles for Choice; a reversed-level probe for Score; none for Noul (noise floor covers it) |
| 2026-09-24 | Restructure is two-step: `propose` (clusters) → authored labels → `apply` (Jev re-route + accept rules). New children may be added *below* locked hand nodes; locked nodes themselves never change |
| 2026-09-24 | Round-trip rule for synthetic questions: accept if placed at the intended node or a descendant (or at the parent of an L3 intended node) |
| 2026-09-24 | Big single-domain machine datasets capped (banking77/sms_spam/jailbreaks 400, emotion 300) so one Machine L1 doesn't swamp the hemisphere |
| 2026-09-24 | Manifold: the human distribution is the **midlife** market price (the real forecast); the at-close price is kept in meta only |
| 2026-09-24 | Scruples human votes pool the 5 gold + 5 extra MTurk annotations (n=10) |
| 2026-09-24 | Bulk placement keeps the **beam** walk (held-out: 90.1% exact) over the fast path (hemisphere step + nearest-node Choice: 84.9%, 2 requests instead of ~4-5); fast is used only for batches over 20k. Most sources place deterministically from exact hints |
| 2026-09-24 | Coverage growth added 6 hand nodes (Politics & Government [hidden content], Identity & Demographics, Personal Care, Telecom & Networks, Moving Abroad, Memories & Life Story), so every question has a home |
| 2026-09-24 | Dedupe keeps the plain "same question?" Noul (F1 0.66 on Quora pairs); a contrastive variant measured worse (0.54) |
| 2026-09-24 | Phase 6: Vital Level-3 articles became 965 topic nodes (tree ≈ 1,220 nodes); Level-4 articles became entity questions (recognition Noul + importance Score); 22 GOAT pairwise categories (G3, top-25 by sitelinks); volume datasets (AITA, Social Chemistry, ETHICS, BoolQ, OpenTDB sweep) plus authored taste/personality/love/mind banks to rebalance kinds |
| 2026-09-24 | Parallel Jev processes are throttled with `ASKJEV_RPS` / `ASKJEV_WORKERS` so their combined rate stays under 1,200 req/min |
| 2026-09-24 | **Search is instant-first:** local embeddings (`bge-small`, free) + pgvector + trigram in ~50 ms; one Jev rerank request after; tree animations are human-paced and independent of latency |
| 2026-09-24 | **Jev is the only gateway model.** No other LLM or embedding model on the gateway. Authoring (descriptions, synthetic questions, transforms) is done by Claude Code and its subagents; embeddings come from a local open model. No spending cap needed for Jev |
| 2026-09-24 | Stack: Python pipeline first; Next.js UI later |
| 2026-09-24 | **Decided (approved via the /goal run):** Postgres (local now, Neon later) with ltree + pgvector as the system of record, raw data and call logs as files, DuckDB for analysis only (`06-pipeline.md` §1) |
| 2026-09-24 | **Decided (approved via the /goal run):** questions are never tree nodes; follow-ups are `question_links`; overload handled by dedupe → split → group, as batch jobs (`02-tree.md` §8) |
| 2026-09-24 | **Decided (approved via the /goal run):** rewording "universes" as overlays on the one tree (same nodes and question ids, transformed probe text); they replace the paraphrase experiment (`05-experiments.md` §1) |
| 2026-09-24 | **Decided (approved via the /goal run):** per-question core metadata + screen request / answer bundle (`03-questions.md` §8) |
| 2026-09-24 | Main view is a **3D nebula** (`07-ui.md`): every node and every displayable question drawn as stars; detail on approach; one search/ask box, "I'm feeling lucky", and search as a journey led by Jev's own live walk (green is Jev's color only). High-volume Machine templates (≥100 instances) become topic nodes |
| 2026-09-24 | UI follows **TypeSafe's brand** (`07-ui.md` Look): light dithered sky, questions as colored particles, OS-window panels, pixel type; free stand-ins for their licensed fonts |
| 2026-09-24 | **Expansion to 1M runs in waves of ~100k** (`10-expansion.md`), each sourced, answered, measured, split, and committed before the next; sourcing overlaps with Jev answering (stream, don't stockpile) |
| 2026-09-24 | Expansion mix rules: ≤ 5,000 rows per question text (3,000 per Machine template; over-cap sources frozen), ≥ 60% anchored per wave, synthetic ≤ 15% per wave (no `other` escape options, no personal-biography questions, no synthetic factual), node cap 1,500 direct questions → split, stop scaling a source that is ≥ 95% correct and ≥ 60% decisive |
| 2026-09-24 | While the UI is in flux, the expansion agent adds nodes but never changes existing node ids or paths (no group or retire), writes only additive migrations from `005`, runs Jev at `ASKJEV_RPS=16`, and commits only its own paths |
| 2026-09-25 | Expansion tree rules: high-volume templates split into their own child only when an authored label says the template is a topic (`authored/template_nodes.yaml`); single-template nodes are bounded by the template cap; hint-placed questions on overfull parents are re-walked by Jev from the parent ("descend") (`10-expansion.md` §7) |
| 2026-09-25 | Waves 6+ priorities (`10-expansion.md` §8): real asked questions first (anchored share may drift to ~55-60%, logged); new hand nodes for buying decisions and everyday how-to; login-gated surveys ingested if Brian downloads them; TypeSafe's empty Machine leaves get authored inputs marked `synthetic_input` inside the 15% cap; a multilingual slice as universes |
| 2026-09-25 | Synthetic share is a ~15-20% guideline, not a hard cap (Self may exceed it); new World volume held until World ≈ 36%; waves 6-7 are Machine + Self (`10-expansion.md` §9) |
| 2026-09-25 | Final plan to ~1.02M at 35/35/30 (`10-expansion.md` §10): Self gets ~100k more beyond the queue (real + synthetic); Social Chemistry's freeze is lifted for Self balance; Machine's last round is trimmed to ~85k and kept out of documents |
| 2026-09-25 | Authored questions never open with a trait or topic label (`01-jev.md` §7); labels were stripped from the queued Self banks and from 3,684 ingested synthetic questions, which were re-answered (`10-expansion.md` §7) |

## M0: Setup
- [x] Docs, resources (transcript, Notion pages, full TypeSafe docs archive + digest)
- [x] `AI_GATEWAY_API_KEY` in `.env`; Jev found on the gateway as `typesafe-ai/jev`
- [x] Local Postgres 17 (Homebrew) running, DB `askjev` with ltree/vector/pg_trgm, `DATABASE_URL` in .env
- [x] Apply `db/migrations`
- [x] Spike: the gateway request/response shape (probabilities, confidence, served version)
- [x] Spike: determinism noise floor and batch invariance (`05-experiments.md` §0)

## M1: Tree skeleton
- [x] Sample questions per L1 (tree YAML examples + held-out routing set)
- [x] Hand-write root → 3 hemispheres → 28 L1 → ~200 L2 (description, not_for, examples) in `tree/`
- [x] Known-path taxonomy test (CPC, Shopify, MeSH, SIC) + traversal check; fix descriptions

## M2: Pipeline + the 10k slice
- [x] Jev client (gateway), append-only call log, request-hash cache
- [x] Screen request, dedupe, answer bundle, measure, rollup; restructure job (split/group/grow)
- [x] Adapters (38 sources; Moral Machine deferred: large OSF file, aggregates only)
- [x] Run stages end to end (`06-pipeline.md` §4); mix report against `03-questions.md` §2

## M3: Experiments + findings
- [ ] Starter universes on a stratified 5k sample (terse, verbose, old-english, synonyms, typos, statement-form, french, negated)
- [ ] Experiments 1-11 on the slice; findings notebook
- [x] Coverage test; first growth round
- [ ] Draft 3-5 findings in the standard format

## M4: UI
- [x] Constellation view + question cards + findings page (`07-ui.md`)
- [ ] Nebula main view: every node and question drawn, detail on approach (`07-ui.md`)
- [x] Ask box (private)

## M5: Outreach
Plan (from `resources/references/notion/become-typesafe-first-intern.md`): apply to "Member of Staff:
Create your own role", then send a short Discord DM to Sasha Sheng linking this one project.
- [ ] Send the findings privately to TypeSafe; ask about the "Jev" name and anything they want held back
- [ ] Anything public happens only after they've seen it and agreed

## M6: Scale (after outreach, or alongside it)
- [x] 100k: Vital L3-L4, core datasets, G5 banks with round-trip filtering (99,458 questions)
- [ ] 200k → 1M in waves of ~100k (`10-expansion.md`; progress in `expansion-log.md`)

## Open questions
- Local embedding model: `BAAI/bge-small-en-v1.5` (384 dims); upgrade only if the search-recall test is poor
- Subtree-sample option values vs opaque keys for traversal (`05-experiments.md` §10)
- Moral Machine sampling unit; Eurobarometer wave selection; which machine datasets per L2
