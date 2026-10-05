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
| 2026-09-24 | Main view is a **3D nebula** (`07-ui.md`): every node and every displayable question drawn as stars; detail on approach; one search/ask box, "I'm feeling lucky", and search as a journey to the result (one color is Jev's only). High-volume Machine templates (≥100 instances) become topic nodes |
| 2026-09-24 | UI follows **TypeSafe's brand** (`07-ui.md` Look): light dithered sky, questions as colored particles, OS-window panels, pixel type; free stand-ins for their licensed fonts |
| 2026-09-24 | **Expansion to 1M runs in waves of ~100k** (`10-expansion.md`), each sourced, answered, measured, split, and committed before the next; sourcing overlaps with Jev answering (stream, don't stockpile) |
| 2026-09-24 | Expansion mix rules: ≤ 5,000 rows per question text (3,000 per Machine template; over-cap sources frozen), ≥ 60% anchored per wave, synthetic ≤ 15% per wave (no `other` escape options, no personal-biography questions, no synthetic factual), node cap 1,500 direct questions → split, stop scaling a source that is ≥ 95% correct and ≥ 60% decisive |
| 2026-09-24 | While the UI is in flux, the expansion agent adds nodes but never changes existing node ids or paths (no group or retire), writes only additive migrations from `005`, runs Jev at `ASKJEV_RPS=16`, and commits only its own paths |
| 2026-09-25 | Expansion tree rules: high-volume templates split into their own child only when an authored label says the template is a topic (`authored/template_nodes.yaml`); single-template nodes are bounded by the template cap; hint-placed questions on overfull parents are re-walked by Jev from the parent ("descend") (`10-expansion.md` §7) |
| 2026-09-25 | Waves 6+ priorities (`10-expansion.md` §8): real asked questions first (anchored share may drift to ~55-60%, logged); new hand nodes for buying decisions and everyday how-to; login-gated surveys ingested if Brian downloads them; TypeSafe's empty Machine leaves get authored inputs marked `synthetic_input` inside the 15% cap; a multilingual slice as universes |
| 2026-09-25 | Synthetic share is a ~15-20% guideline, not a hard cap (Self may exceed it); new World volume held until World ≈ 36%; waves 6-7 are Machine + Self (`10-expansion.md` §9) |
| 2026-09-25 | Final plan to ~1.02M at 35/35/30 (`10-expansion.md` §10): Self gets ~100k more beyond the queue (real + synthetic); Social Chemistry's freeze is lifted for Self balance; Machine's last round is trimmed to ~85k and kept out of documents |
| 2026-09-26 | Search journeys go **straight down the chosen question's stored path** (embeddings + one Jev rerank pick it); Jev's own tree walk is **on demand** from the question card ("Where Jev would file it"), not part of every search: it cost 1-2 s and a detour whenever Jev filed a question elsewhere. Rerank check (`web/scripts/rerank_eval.mjs`, 30 queries): Jev changes the top result in 50%, median 243 ms |
| 2026-09-26 | **Deployment:** Vercel (from `web/`) + a trimmed Postgres copy (PlanetScale, single node) built by `scripts/sync_prod.py`; search drops its trigram leg (never changed the #1 on 30 queries, ~590 ms) and production uses half-precision embeddings with a 1-bit HNSW index (#1 matches exact search 97%, 292 MB vs 1.85 GB); private via a shared-link key; ask box answer-only in production (`07-ui.md`, Deployment) |
| 2026-09-25 | Authored questions never open with a trait or topic label (`01-jev.md` §7); labels were stripped from the queued Self banks and from 3,684 ingested synthetic questions, which were re-answered (`10-expansion.md` §7) |
| 2026-09-26 | Taste gets single-item Score ratings next to the head-to-heads: new hand node Self > Lifestyle > Ratings (12 domain children); real-data ratings with human distributions for films, books, board games, anime and beer (`taste_ratings`), an authored bank for the other domains (`10-expansion.md` §7) |
| 2026-09-26 | Personality (trait) banks accept any Self placement from the round trip and keep the intended trait as `meta.measures`; other banks keep the strict filter (`10-expansion.md` §7) |
| 2026-09-26 | Format banks (memes, who-would-win, shower thoughts, ratings) keep the author's node once the round-trip walk completes; earlier rejects recovered (`10-expansion.md` §7) |
| 2026-09-26 | Human data must be observed: fitted normal curves from published means/SDs (lancaster, glasgow_norms, concreteness; 22,000 rows) moved out of `human_dists` into `meta.fitted_dist`; comparisons use the published mean (`04-datasets.md`) |
| 2026-09-27 | Content screen: narrow 03 §6 topics plus contested policy debates and sex work, attached content included, hide at p >= 0.3 with a keyword backstop; all hidden questions re-screened (17,833 unhidden) and Moral Machine shown (`03-questions.md` §6, `10-expansion.md` §7) |
| 2026-09-27 | Harm review: an embedding and keyword scan (no Jev) found 32 visible World/Self questions to remove; hidden with a permanent `harmful` flag rather than deleted (kept in dev, never in the production copy); Machine moderation inputs stay visible by choice (`03-questions.md` §6) |
| 2026-09-26 | Search is **find-only and live**: every keystroke (minus a trailing fragment under 3 chars) re-lights the map as ink heat over the top 20's dots and paths, with the category named and the rest faded; Jev stays one request at the pause, drawn in green. No answering LLM or citations. Asking new questions becomes a separate **compose mode** later (`07-ui.md`, Search and Ask box) |
| 2026-09-27 | **Self-portrait** (`11-portrait.md`): one page at `/portrait` plus `/portrait/atlas`, 30 findings on the page and the rest in the atlas, with a pipeline chapter ("Jev built its own map"). Its data is private: `scripts/portrait/export_page.py` writes `data/analysis/portrait.json`, read on the server, never from `web/public`. No extra rewording calls: the existing four probes per question (as asked, 'most people', reordered, reversed) are the robustness checks |
| 2026-09-27 | Portrait reframed around TypeSafe's "nobody asks how Jev's doing" tweet: a Wrapped-style deck of ~30 cards addressed to Jev, with fine print on every card, memes on about a third of them (templates kept in gitignored `data/portrait/memes/`), taste from ratings rather than head-to-heads, and hand-picked check-in/debate/hot-take/miss cards labeled as hand-picked (`11-portrait.md` §6-7). Scrollable now; a stories mode can wrap the same cards later |
| 2026-09-27 | The map links to the portrait and atlas with TypeSafe-style nav chips (top center; bottom on phones) and takes deep links (`/?node=`, `/?q=`, the address bar following the open panel). A wellbeing bank (`sources/wellbeing`: SWLS, WHO-5, UCLA-3, PSS-4, Cantril ladder; 18 items) was added and answered for the portrait's checkup card (`11-portrait.md` §7) |
| 2026-09-27 | Polish pass (`12-polish.md`): a rubric for map, portrait and atlas scored before and after; online tests scored against their real test-takers (`tier1_scales.py`); atlas findings as cards; routine prod refreshes via `sync_prod.py --delta`; portrait data served from a private Blob folder (`PORTRAIT_URL`). Production matches local |
| 2026-09-28 | **Findings become experiments** (`16-experiments-plan.md`, `experiments/`): each gathers many questions into one comparison, documented in six steps and judged by Jev itself (`experiments/evaluator.md`: head-to-heads against a gold set, keep/atlas/rework/cut in code, plus Claude's sampled audit). New questions only where an experiment needs them, as `sources/<name>` adapters of published human data, tagged `meta.experiment`. The atlas becomes the experiments library (a page per experiment); the old per-topic claims move to a reference tab. The portrait's cards stay; its candidates are ranked from Jev's verdicts |
| 2026-09-28 | Dedupe skips experiment variants (questions with `meta.base_id`, e.g. "most people answered X"): they reword an existing question on purpose. The first gate run had hidden 1,686 of them as duplicates; they were restored |
| 2026-09-28 | Experiments are **ranked** mostly by Jev's head-to-heads over the whole case studies (`scripts/experiments/rank.py`), adjusted by whether a curious person would find it interesting, how much to rely on it and how fair the comparison is (weights in `scripts/experiments/export.py`); whether it describes Jev and whether Jev saw it coming are index sorts, not rank inputs. No verdict is shown: a keep-or-discard call was tried and dropped as not telling, and the ten-label evaluator verdict stays off the page. Case studies are **third person** and lead with the finding (`17-case-studies-plan.md`, Page structure) |
| 2026-09-28 | Case-study memes never target a country, its people or a named person; **Jev rates each meme's funniness** (1-5, the case studies' and the portrait's) from a description in words, shown under the meme (`17-case-studies-plan.md`, Memes) |
| 2026-09-28 | Jev's color (its pick, walk, trail, and the selection) is typesafe.ai's main magenta `#D45BB6` (was green `#03AA5C`): on-brand; accepted trade-off that it sits near Self's pink and the indicators' hot end |
| 2026-09-28 | **Moral Machine thinned for display** to 1,000 per topic (4,031 of 26,020 shown; the rest hidden with the `thinned` flag, not deleted, `scripts/thin_source.py`): one template filled in 26k ways crowded its topics; its four topics renamed "Self-Driving Car: …" |
| 2026-09-28 | The site is **open, no site key** (`SITE_KEY` unset): Brian shares the link with TypeSafe directly instead of a keyed link |
| 2026-09-29 | **Portrait rebuilt as chapters from the experiments** (`11-portrait.md` §7, The story): character, taste with pictures, words, numbers, morals, pressure, minds and rough edges, each a custom visual with links to its case studies; third person; numbers copied from result files by `story.py`; the Wrapped-style summary is gone |
| 2026-09-29 | **Framing: curiosity, not a benchmark.** The portrait opens with TypeSafe's "nobody asks how Jev's doing" tweet and Jev's answers, then why ask (the stance in the project's own words: not a benchmark, just curious), how the data was gathered (a source treemap, the tree's origins, the pipeline) and every job Jev does (counted from the call logs); the README leads the same way |
| 2026-09-30 | **Dataset on Hugging Face** (`brian-w-zhang/askjev`, dataset repo), **private** until TypeSafe has seen the findings, shared with them alongside; built by `scripts/export_hf.py`, checked by `scripts/hf/check.py`, uploaded by the `/publish-dataset` skill. CC BY-NC-SA 4.0. Tables: questions, answers, question_meta, tree, placements, human_dists, experiments, a calls sample. Hidden questions never ship. Yahoo Answers words withheld with a `restore_ref` and `restore_yahoo.py`; MovieLens and Last.fm human data dropped; Reddit and Quora text ships with attribution and a removal route |
| 2026-09-30 | **Atlas: coverage replaces the old claims.** A Coverage tab measures, for every branch and topic, the share of its shown questions used by an experiment about that topic, apart from corpus-wide ones (calibration, option order, repeat noise, self vs people, torn vs sure, closed-question lean), plus the share with a right answer or real people's answers (`scripts/experiments/coverage.py`, run by `export.py`). The old per-topic claims tab and the hand-written coverage list are retired; the search box no longer sticks; the heading follows the open tab. New experiments go where coverage is thin, from data already in the corpus first |
| 2026-10-02 | **Portrait audit**: jaggedness ("Similar tasks, very different results") drops the topic web, which pooled whatever datasets sit under each tree topic ("operations 64%" was mostly a log-anomaly task below a coin toss), for pairs of look-alike checks from single experiments plus a new experiment, `work_sure_and_wrong` (on 29 of 123 work tasks Jev is 10+ points surer than right); no new probes, since requests over ~6.5k tokens mostly fail at the gateway, which rules out a long-context test. At work drops the clown meme, the field-range figure and the borderline-cases figure (it repeated the calibration point). A risk chapter brings back prospect theory and unknown odds, top-10 experiments that lost their place with the minds chapter. New memes for habits, morals and risk |
| 2026-10-02 | **Atlas sorts by Jev's interest rating** by default; the head-to-head rank stays as a sort but leaves the cards. |
| 2026-10-04 | **At work becomes "Wrong in predictable ways"**: it said confidence again, after the knowledge chapter and before jaggedness's "sure and wrong". It now shows which way each kind of check leans when Jev is wrong (two tasks per kind, the storage-block check left to jaggedness) and where its misses land (routing next door, evidence to "can't tell", "nothing here" underused, contracts overlooked), with the where-monkey meme. Jaggedness is "Similar tasks, different results". The README drops the line that Claude wrote the code |
| 2026-10-04 | **At work is cut.** Its frame didn't hold: the four kinds of check are a hand grouping of 46 tasks, and within each group the tasks lean both ways (a few extreme ones made the "leans yes/no" look systematic), while its headline case, fake hotel reviews, is one people can't spot either. Its experiments stay in the atlas; the portrait's work findings are jaggedness's look-alike pairs and "sure and wrong". Fourteen chapters |
| 2026-10-05 | **The portrait's ending**: the "what this can't tell you" card folds into the fine print, which becomes six questions opened one at a time (like typesafe.ai's FAQ), with that one open first; the repeats go (the stability checks were listed twice and "not a benchmark" three times, and chapter 04 already credits what isn't Jev). The closer stays. The footer is "askjev · a toy by Brian Zhang · not affiliated with TypeSafe". The chapter rail follows scroll position, so a jump no longer leaves it on chapter 01 |
| 2026-10-05 | **The portrait borrows more of typesafe.ai's print language**, measured from their site: the fine print is their FAQ (ink #1e1e1e, JetBrains Mono 13px/300 questions with 0.05em tracking, dashed-then-solid left rule, chevron box, one open at a time, a [B.64] block saying "So, how's Jev doing? Probably fine."); the fine print's headline is framed in crop marks. Tried and dropped: rule-and-mono chapter headings (they keep their number box), a dotted stage behind figure panels, crop marks on the closer. The dark fields stay |
| 2026-10-05 | **Memes are typesafe.ai team cards**: a black pixel title bar naming the chapter (or "case study"), the picture in a grey frame, and Jev's funniness rating as the tilted "fun fact" window over the corner. This replaces the raw template filename bar and the five-bar "how funny" chart that repeated under every meme. The charts stay in plain panels |
| 2026-10-05 | **The map's vertical caption is base64 encoded once** ("I want to join the jevolution", 40 characters on one line); seven rounds like typesafe.ai's "No comment." made it 252 characters in three wrapped lines |
| 2026-10-05 | **Meme cards follow typesafe.ai/team**: straight (no tilt), no pink shadow, their soft drop shadow, a #c4c4c4 frame holding the picture with the caption and the five-bar "how funny" chart in white blocks under it; the black bar names only the chapter. Tried and dropped: Jev's rating as a "Fun fact" window over or under the card (it hid meme text, and the chart says more) |
| 2026-10-05 | **Meme captions only where they are the joke**: a meme with words on the picture loses its caption (it restated the result between the meme and its rating); a reaction format with no words on the picture keeps it, above the picture as the setup. The composability cards show Jev's prompts in full, shortened (exact wording on hover), instead of clipped until hovered. The wellbeing gauges are drawn like the other Jev-vs-most-people rows (thin line, 11px square and amber ring, a hairline between them) |
| 2026-10-05 | **The root topic is "All questions"** ("Every question on the map, in three branches: the World, the Self and the Machine"), not the rejected "Everything Asked" name with "every closed question": the map holds a million, not every one. Set in `tree.py`, the local and production `nodes` row, and the re-exported portrait and atlas data. The topic panel drops its "asked here" tag: it counted questions saved through the ask box, which production never saves |
| 2026-10-05 | **The opening's check-ins and gauges, tidied**: the yes-or-no check-ins are two clean columns (the question; Jev's answer and how sure it was), without the people share; the wellbeing gauges show only Jev's score, a square on a thin line (no "most people" ring or text), each with a word; the ladder's is Gallup's band (7 and up thriving, 4 or below suffering, struggling between) |

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

## M3: Experiments
- [ ] Starter universes on a stratified 5k sample (terse, verbose, old-english, synonyms, typos, statement-form, french, negated)
- [ ] Experiments 1-11 on the slice; findings notebook
- [x] Coverage test; first growth round
- [ ] Draft 3-5 findings in the standard format

## M4: UI
- [x] Constellation view + question cards + findings page (`07-ui.md`)
- [ ] Nebula main view: every node and question drawn, detail on approach (`07-ui.md`)
- [x] Ask box (private)
- [ ] Compose mode: write a new question in its primitive's spec and watch Jev dedupe, place and answer it live on the map (`07-ui.md`, Ask box)

## M5: Outreach
Plan (from `resources/references/notion/become-typesafe-first-intern.md`): apply to "Member of Staff:
Create your own role", then send a short Discord DM to Sasha Sheng linking this one project.
- [ ] Send the findings privately to TypeSafe, with the private dataset link; ask about the "Jev" name, anything they want held back, and whether Jev's answers may be published
- [ ] Anything public happens only after they've seen it and agreed

## M6: Scale (after outreach, or alongside it)
- [x] 100k: Vital L3-L4, core datasets, G5 banks with round-trip filtering (99,458 questions)
- [ ] 200k → 1M in waves of ~100k (`10-expansion.md`; progress in `expansion-log.md`)

## Open questions
- Local embedding model: `BAAI/bge-small-en-v1.5` (384 dims); upgrade only if the search-recall test is poor
- Subtree-sample option values vs opaque keys for traversal (`05-experiments.md` §10)
- Moral Machine sampling unit; Eurobarometer wave selection; which machine datasets per L2
