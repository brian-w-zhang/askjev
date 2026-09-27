# 11. A self-portrait of Jev

One long scrolling page at `/portrait` in the askjev web app, grounded in the full answered corpus (1.09M questions,
~3.8M answers), in TypeSafe's style. It should be readable in 15-20 minutes, and an atlas appendix holds every finding.
This doc is the plan; once the page exists, it becomes the method.

Read first: `CLAUDE.md`, `01-jev.md` (§6: documented jaggedness is labeled as known, never as a discovery),
`03-questions.md`, `05-experiments.md`, `findings-preview.md`, `07-ui.md` ("Look"), `web/src/app/globals.css`,
`web/src/lib/theme.ts`.

## Models
- **Feltron Annual Reports** set the frame: deadpan precision about one subject.
- **The Pudding** shows each metric on one real example first, then gives every aggregate a drawer of real rows.
- **NYT Upshot** has the reader answer first, then shows you vs Jev vs humans.
- **FiveThirtyEight, "Checking Our Work"** sizes calibration dots by count and draws bands.
- **Our World in Data** makes the chart title the finding.
- **Anthropic, "On the Biology of a Large Language Model"** prefers case studies to grand claims.

## 1. Analysis table
Pure SQL/Polars, no Jev. `scripts/portrait/build_table.py` writes `data/analysis/questions.parquet`, one row per
question. Columns:
- id, node path, hemisphere, kind, primitive, source, origin; truth, correct
- Jev: base distribution, top, p_top, expected level (`score_scalar`)
- humans: distribution, mean, n
- people-frame answer and gap
- shuffle and reversed-level shifts
- `meta.measures`
- instrument metadata: trait, facet, keyed, level_map, dichotomy/poles, foundation
- entity ids for matchups and ratings
- flags, display_ok

Anything shown excludes `display_ok = false` and `harmful` rows. Contested politics stays off the page.

## 2. Scoring in three evidence tiers
Every claim states its tier.

**Tier 1: validated instruments** with published keys and human norms.
- IPIP / Open Psychometrics / EPQ (trait, facet, keyed, level_map): Big Five, HEXACO and 16PF percentiles vs norms.
- OEJTS (dichotomy, poles): a Myers-Briggs-style type, with per-axis strength and uncertainty.
- MFQ: moral foundations.
- Moral Machine: effect sizes vs the world and the three country clusters.
- Bradley-Terry rankings from the head-to-heads, cross-checked against single-item ratings of the same entities.

**Tier 2: authored trait questions** (`meta.measures`, 33 facets, ~42k).
- A subagent audits option direction (low→high) on a random ~50 per facet.
- Fix or exclude any facet below ~90% direction accuracy.
- Score with the facet weights shown.

**Tier 3: embedding-gathered themes** the tree does not capture (attitudes to AI, risk).
- Gather candidates with local embeddings plus node filters.
- A subagent labels a random 200 for precision, and the page states it ("~N questions, P% on-topic by audit").
- Merge equivalent questions (e.g. several favorite-season questions) by embedding clusters, spot-checked.

Semantic work is done by Claude and subagents on samples, never by another gateway model.

## 3. Discovery pass (SQL)
Compute a standard indicator card for every node (~1,700) and every source:
- n; accuracy and ECE where there is truth; crowd agreement where there is human data
- decisiveness; people-frame gap; order and reversal shifts
- Jev's most extreme answers

Rank the cards by standardized deviation from the corpus baseline (minimum n) and take 100-200 candidate findings
across all categories.

Also compute:
- **Calibration:** by L1, L2 and primitive; confident misses.
- **Machine tasks:** placed against the noise band as saturated, informative or near chance.
- **Jaggedness:** order, reversal, frame, pair-vs-rating, transitivity.
- **Humor:** near chance.
- **Ratings:** the middle-level lean.
- **Taste beyond reputation:** self minus people-frame.

## 3b. Data landscape (SQL)
The portrait is only as good as what Jev was asked, so the page also shows the corpus itself. Every figure below goes
into the claims ledger like any other claim:
- **Where the questions come from:** counts by source family (surveys and polls, psychometric instruments, labeled
  task datasets, knowledge and exam banks, pairwise taste data, real asked questions, authored banks), real vs
  authored, and licenses.
- **Shape:** hemisphere, L1 and kind; primitive (Noul / Choice / Score); option and level counts; the tree's depth
  and node sizes.
- **Anchoring:** the share with ground truth, the share with real human answer distributions (and the number of human
  respondents behind them), and the share with neither.
- **Filtering:** round-trip acceptance for authored banks, what is hidden and why (sensitive, political, duplicate,
  biographical, harmful), and the fitted norms that were removed.
- **Jev's side:** probes and answers per question, the served version, cached calls.

## 4. Claims ledger
`data/analysis/findings.json` holds one entry per claim:
- the sentence, tier and query/script
- n, effect vs the noise floor, and a cluster-bootstrap CI (by source/template)
- the robustness checks passed
- 3 example ids chosen by fixed seed (never hand-picked)
- the Jev served version

Nothing reaches the page unless it is in the ledger.

## 5. Optional robustness pass
These are the only Jev calls: cached, never re-sent, `ASKJEV_RPS <= 16`.
- Rewordings or universes on a stratified ~20k sample, for headline candidates only.
- Claims that fail are marked fragile or dropped.

## 6. Shortlist, then stop for Brian
A short review doc of ~40 candidates, each with its sentence, a chart sketch, n/CI, tier and 2 real examples.
Editorial rules:
- **Page budget:** ~14 sections, 25-35 findings.
- **Balance:** taste gets at most 2 sections (favorites; taste beyond reputation). Self, World and Machine each carry
  real weight.
- **Selection:** surprising and robust over big; one strong example per idea.

Wait for Brian's picks before building the page.

## 7. Page
**Files.** New files only under `web/src/app/portrait/**` and `web/src/components/portrait/**`; shared files the
frontend session owns stay untouched. Data comes from `web/public/portrait/portrait.json`, exported from the ledger.

**Look.** Reuse the CSS tokens, window and chip classes, and pixel type. Light and dark themes. No 3D, glow or radar
charts.

**Sections, in order:**
1. Cold open: one real question ("one of 1,091,643").
2. The data landscape: where the 1.09M questions come from and what shape they have (sources, primitives,
   anchoring, filtering).
3. Answer it yourself: 5 questions, and your answers carry down the page.
4. How Jev answers (defaults).
5. Personality.
6. Values.
7. Taste favorites.
8. Taste beyond reputation.
9. Knowledge map.
10. Calibration (draw-first).
11. Work effectiveness.
12. Jaggedness (the same question, asked two ways).
13. The stable core.
14. You vs Jev.
15. Methods.

**Every chart** has a sentence title, direct labels, n and an interval, and a "show the rows" drawer of real questions
with Jev's answer next to the human answer. Charts are dot/interval in plain SVG/React, or a library already in
`web/package.json`. On mobile: a single column and no hover-only facts.

## 8. Atlas
`/portrait/atlas` (or an appendix section): a searchable, filterable table of every candidate finding and every node
card, each linking into the star map, plus the full source table from the data landscape. Everything found but not on
the page lives here.

## 9. Verify
- Every number on the page equals `findings.json`.
- Screenshots of both themes, at desktop and mobile widths (the `web/scripts/ui_shots.mjs` pattern).
- Read the page end to end as a visitor, and cut anything unsupported.
- Rewrite this doc as the method: tiers, ledger, how to regenerate.

## Rules
- Indicators only: never a benchmark, ranking or overall score.
- Jev is the only gateway model.
- Commit only your own paths, with plain commit messages and no co-author lines.
- Ask Brian before editing shared UI files, deploying, or publishing externally.
