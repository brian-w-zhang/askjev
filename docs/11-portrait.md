# 11. A self-portrait of Jev

`/portrait` is one long page in the askjev web app, readable in 15-20 minutes, about what the full answered corpus
(1,091,643 questions, 3.8M probes) says about Jev. `/portrait/atlas` holds every finding, every topic's indicators and
every source. This doc is the method: how the numbers are made, how the page is built, and how to regenerate both.

Read first: `CLAUDE.md`, `01-jev.md` (§6: documented jaggedness is labeled as known, never as a discovery),
`03-questions.md`, `05-experiments.md`, `07-ui.md` ("Look").

## Models
- **Feltron Annual Reports** set the frame: deadpan precision about one subject.
- **The Pudding** shows each metric on one real example first, then gives every aggregate a drawer of real rows.
- **NYT Upshot** has the reader answer first, then shows you vs Jev vs humans.
- **FiveThirtyEight, "Checking Our Work"** sizes calibration dots by count.
- **Our World in Data** makes the chart title the finding.
- **Anthropic, "On the Biology of a Large Language Model"** prefers case studies to grand claims.
- **typesafe.ai** sets the look: each page is one full-bleed color (pink home, teal manifesto, sage blog, magenta band,
  ink), text sits in a narrow column with a thin left rule and tiny mono labels, headlines are huge grotesk, figures
  are OS windows with black pixel title bars on dotted pads. Dark mode follows docs.typesafe.ai (aubergine black,
  hot pink). Jev is magenta in every chart (the star on TypeSafe's own charts); people are ink.

## Pipeline
Pure SQL/Polars, local only; no Jev calls. Each script appends its claims to `data/analysis/findings.json` (the
ledger), replacing its own earlier claims. `data/` is gitignored: the findings stay private.

```
uv run python scripts/portrait/build_table.py        # 1. data/analysis/questions.parquet (~12 min)
uv run python scripts/portrait/tier1_bigfive.py      # 2. tier 1: Big Five vs IPIP-FFM respondents
uv run python scripts/portrait/tier1_values.py       #    Moral Machine regression, MFQ
uv run python scripts/portrait/tier1_type_taste.py   #    OEJTS type, Bradley-Terry favorites
uv run python scripts/portrait/tier2_traits.py       #    tier 2: audited authored trait facets
uv run python scripts/portrait/tier3_themes.py       #    tier 3: embedding themes (then tier3_finalize.py)
uv run python scripts/portrait/discovery.py          # 3. indicator cards per node, L2, L1, source
uv run python scripts/portrait/findings.py           # 4. the ledger
uv run python scripts/portrait/landscape.py          #    data landscape claims + source table
uv run python scripts/portrait/pipeline.py           #    "Jev built its own map" claims
uv run python scripts/portrait/export_page.py        # 7. page support claims + data/analysis/portrait.json
uv run python scripts/portrait/shortlist.py          # 6. the review shortlist (data/analysis/shortlist.md)
uv run python scripts/portrait/verify_page.py        # 9. numbers on the rendered page vs the ledger
node scripts/portrait/shots.mjs <outdir>             #    screenshots, both themes, desktop and phone
```

## 1. Analysis table
`build_table.py` writes one row per question:
- id, node path, L1/L2, hemisphere, kind, primitive, source, origin, text, options, attached content (first 2,000
  characters), truth, flags, `display_ok`, `harmful`
- Jev: the base answer's distribution and expected level, top answer, p_top, stability, frame gap, correct, Brier
- Jev's answer for "most people" (distribution and level)
- the reordered and reversed-level variants
- every human distribution with its population and n
- the meta keys the tiers use (`meta.measures`, trait/facet/keyed, dichotomy/poles, foundation, entity ids)

Anything shown excludes `display_ok = false` and `harmful` rows; contested politics stays off the page.

## 2. Three tiers of evidence
Every claim states its tier.

**Tier 1: published instruments and real answers.**
- IPIP 50-item Big Five markers, scored as percentiles against the 603,322 IPIP-FFM respondents, with a 90% interval
  from resampling the ten items per trait; the reversed-level and "most people" versions are reported beside it.
- OEJTS: a type-like profile with per-axis strength. Its human norms are not in the corpus, so the comparison is Jev's
  own "most people" answer.
- Moral Machine: the Awad et al. regression (chance of sparing a side per unit difference) fitted to Jev's
  26,020 dilemmas and to the players' shares.
- MFQ foundations, self vs "most people".
- Bradley-Terry rankings from the head-to-heads, with rank correlation against people's own head-to-heads and against
  Jev's single-item ratings of the same entities.
- Accuracy and calibration where there is a right answer; crowd agreement where there are human answers; real gambles.

**Tier 2: authored trait questions** (`meta.measures`). A subagent audited option direction on a random sample of
1,650 items across 33 facets (`data/analysis/audit/`). Most rating (Score) items ran low to high (81% as written);
multi-option Choice items mostly did not (12%), so they are excluded. Only facets whose Score items pass ≥ 90% are
scored: 21.

**Tier 3: embedding themes** (AI, death, risk, honesty, money, animals, tradition, humor), gathered by local
embeddings plus node filters, with precision measured on a labeled random sample. Their stances are near 50/50, so
they live in the atlas, not on the page.

Semantic work (audits, labels) is done by Claude and subagents on samples, never by another gateway model.

## 3. Discovery
`discovery.py` computes an indicator card for every node, L2, L1 and source: n, accuracy and ECE where there is truth,
confidence and confident misses, decisiveness (p_top ≥ 0.95), stability under reordering, frame gap (self vs "most
people"), crowd agreement. Cards are ranked by standardized distance from the corpus baseline (in the ledger as
`page_baseline`). Machine tasks are banded against the noise floor as saturated, informative or near chance; the page
shows each task's chance level (one over its number of options) instead of the label.

## 4. The ledger
`data/analysis/findings.json`: one entry per claim with the sentence, section, tier, script, n, effect, a 90%
cluster-bootstrap interval (resampling whole sources, so one big dataset cannot manufacture confidence), the noise
floor (±0.03 Noul/Score, ±0.08 Choice), robustness notes, three example ids chosen by a fixed seed (md5 order, never
by hand), and the Jev version. Nothing reaches the page unless it is in the ledger; the few numbers the page needs
beyond the analysis claims (frame gap by domain, the taste lenses, rating-level shares, the gamble scatter, the quiz
and cold-open questions, the baseline) are added by `export_page.py` as `page_*` claims.

## 5. Robustness
No extra Jev calls were made for the portrait. Every question was already asked four ways: as asked, for "most
people", with options reordered, and (for scales) with levels reversed. Those are the robustness checks, shown where
they matter: stability by primitive and domain, the Big Five under reversed levels, and self vs "most people"
throughout. Headline claims that depend on scale use (the Big Five percentiles) are framed against Jev's "most
people" answer, because Jev rates in the middle and people rate themselves generously.

## 6. Selection
A shortlist of 36 candidates (`shortlist.py`) went to Brian, who approved 30 for the page and 6 for the atlas only
(taste agreement per domain, confident misses, fragile domains, themes, question kinds, probes per question). Some of
their numbers appear on the page as context: fragile domains next to the stable ones (S1), agreement with people next
to agreement with its own ratings (J3), the probe count on the cover. Editorial rules:
- about 14 chapters and 30 findings; taste gets at most two sections (favorites; beyond reputation)
- Self, World and Machine each carry real weight
- surprising and robust over big; one strong example per idea
- TypeSafe's documented limits (`01-jev.md` §6) are not presented as discoveries

## 7. The page
**Files.** `web/src/app/portrait/` (layout, page, atlas page) and `web/src/components/portrait/` only; shared UI files
are untouched. The map's body never scrolls, so the portrait scrolls inside its own `.pt` container, and all its
styles are scoped under `.pt`.

**Data.** `export_page.py` writes `data/analysis/portrait.json` (about 1.6 MB): the ledger, the real rows behind every
example, the work tasks, the source table and the node cards. `components/portrait/data.ts` reads it on the server
(re-reading when the file changes). It is never copied into `web/public`, so the findings stay out of the public repo;
deploying the page needs Brian's go-ahead and a private way to ship that file.

**Chapters and fields.**

| # | Chapter | Field | Findings |
|---|---|---|---|
| — | Cover | paper, pink dithered hero | stacked question windows, three big numbers, three highlights, contents |
| 1 | One question | paper | the cold open: one seeded question, Jev for itself vs for "most people" vs real people |
| 2 | Where the questions come from | pink | L1 unit chart, L2 answer shapes, L3 anchoring, L5 hidden |
| 3 | Jev built its own map | sage | F1 pipeline diagram, F3 blind round trip per bank, F4 content screen |
| 4 | Answer it yourself | paper | five seeded questions with real human splits |
| 5 | How Jev answers | teal | D1 middle-level lean, D2 stability under reordering |
| 6 | Personality | pink | P1 Big Five percentiles, P2 muted self, P3 type, P4 where the lenses disagree |
| 7 | Values | sage | V1-V3 Moral Machine, V4 undecided dilemmas, V5 MFQ, V6 gambles |
| 8 | Taste | magenta | T1 favorites, B1 beyond reputation (films), B2 small multiples |
| 9 | What Jev knows | paper | K1 accuracy vs confidence by domain, C1 draw-first calibration |
| 10 | Jev at work | teal | W1 task scatter, W2 hardest tasks vs chance, W3 code clones |
| 11 | Jaggedness | ink | J1 humor, J3 head-to-heads vs own ratings, J4 self vs "most people" by domain |
| 12 | What never moves | sage | S1 most and least stable domains, A1 crowd agreement |
| 13 | You vs Jev | pink | your quiz answers vs Jev vs the crowd |
| 14 | Method | paper | this doc in short, F2 placement methods, the bill |

**Every figure** has a sentence title that is the finding, direct labels, n, an interval where one exists, the ledger
ids it rests on, and a "show the rows" drawer of real questions with Jev's distribution next to the human one (or
Jev's "most people" answer). Charts are HTML dot rows and bars (legible at phone width) and SVG scatters; no 3D, glow
or radar charts. The quiz and calibration guesses stay in the reader's browser. Light and dark themes share the map's
`askjev.theme` key.

## 8. Atlas
`/portrait/atlas`: a searchable table of every ledger claim (filter by section), the node cards sortable by any
indicator, and the full source table. The map has no deep links yet, so node rows are not linked into it; adding
them means a change to the map's shared code.

## 9. Verification
- `verify_page.py` pulls every number from the rendered page and checks it against `portrait.json` in every format the
  page prints. What remains unmatched is expected: chapter numbers, figure n totals (sums of ledger n), and numbers
  inside question text in the drawers.
- `shots.mjs` screenshots every chapter in both themes at 1440 px and 390 px.
- Rounding matches the ledger's sentences (the page rounds half to even, as Python does).

## Rules
- Indicators only: never a benchmark, ranking or overall score.
- Jev is the only gateway model, and the portrait made no new Jev calls.
- Commit only the portrait's own paths, with plain commit messages and no co-author lines.
- Ask Brian before editing shared UI files, deploying, or publishing externally.
