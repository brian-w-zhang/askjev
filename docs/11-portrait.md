# 11. A self-portrait of Jev

`/portrait` is one long page in the askjev web app, readable in 15-20 minutes, about what the full answered corpus
(1,091,643 questions, 3.8M probes) says about Jev. `/portrait/atlas` holds every experiment (`16-experiments-plan.md`,
`experiments/`), and, for reference, the old per-topic claims, every topic's indicators and every source. This doc is the method: how the numbers are made, how the page is built, and how to regenerate both.

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
uv run python scripts/portrait/tier1_scales.py       #    online tests (Open Psychometrics) vs their real test-takers
uv run python scripts/portrait/export_page.py        # 7. page support claims + data/analysis/portrait.json
uv run python scripts/portrait/shortlist.py          # 6. the review shortlist (data/analysis/shortlist.md)
uv run python scripts/portrait/verify_page.py        # 9. numbers on the rendered page vs the ledger (ASKJEV_KEY=... for prod)
node scripts/portrait/sweep.mjs <outdir> [base]      #    every route, 5 widths, 2 themes: errors, overflow, alt text
node scripts/portrait/interact.mjs <outdir> [base]   #    clicks through map, portrait and atlas like a visitor
uv run python scripts/portrait/publish.py [--deploy] #    portrait.json + memes to a private Blob folder (PORTRAIT_URL)
node scripts/portrait/shots.mjs <outdir>             #    one screenshot per card, both themes, desktop and phone
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
- Open Psychometrics scales (nerdiness, DASS, attachment, dark triad, RIASEC and ~50 more) compared item by item with
  the average answer of everyone who took them on the site (`tier1_scales.py`); a comparison with test-takers, not a
  percentile, and test-takers are self-selected.

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

## 6. Selection and framing
The first draft (14 chapters, 30 findings, report voice) read as a report. The current page is framed by TypeSafe's
tweet, "Everyone wants to know what Jev is, nobody asks how Jev's doing", and answers it as a playful self-portrait:
a deck of about 30 cards addressed to Jev ("you"), Wrapped-style, each with plain fine print about what the number can
and can't say. Rules:
- one idea per card, one headline on the whole page; everything else is card-sized
- claims say "your answers say", not "you are"; limits sit on the card they affect, and a "what this can't tell you"
  card comes before the closer
- taste uses the one-at-a-time ratings (top and bottom per domain), not the head-to-heads
- the check-in, debates, hot takes, quiz and confident misses are **hand-picked** from real questions and say so;
  everything else is ranked or seeded. The hot-take and miss cards state the size of the pool they were picked from
- TypeSafe's documented limits (`01-jev.md` §6) are not presented as discoveries

## 7. The page
**Files.** `web/src/app/portrait/` (layout, page, atlas page, the meme route) and `web/src/components/portrait/` only;
shared UI files are untouched. The map's body never scrolls, so the portrait scrolls inside its own `.pt` container
(scroll-snap, proximity), and all its styles are scoped under `.pt`.

**The story.** The page is thirteen chapters: four on the project (how is Jev, why ask, how it was made, Jev's jobs, in Brian's voice) and nine built from the experiments, then the reader's turn, the limits and the fine
print (`components/portrait/story/`). `scripts/portrait/story.py` copies each chapter's numbers from the experiments'
result files into `data/analysis/story.json`, which `export_page.py` puts into `portrait.json` as `story`; no number
is typed into the page. Chapters are written in the third person and each ends with links to its case studies.

| Chapter | Built from | Visual |
|---|---|---|
| how is Jev? | TypeSafe's "nobody asks how Jev's doing" tweet; six Reddit check-in polls; five wellbeing scales scored as for a person | the tweet, a check-in poll, four gauges |
| why ask | Diogo Almeida's words on benchmarks and weird experiments (Latent Space); Jev's own top three findings | quote cards, a readme, a "universal classifier" riff linking into the chapters |
| how it was made | every source (`landscape_sources.parquet` + each `source.yaml`), the tree's origins (`nodes.source`), the pipeline claims | a stats strip, an interactive treemap of 312 sources in 11 families, the tree's origins per hemisphere, the pipeline in seven steps |
| Jev's jobs | every call in `data/calls` sorted by the words it sent (`scripts/portrait/jev_jobs.py`), one question's real trip | a log-scale board of jobs that opens to the exact words Jev reads, what isn't Jev, one question from source to star |
| meet Jev | the question count, Jev's own top three experiments | hero, three linked findings |
| character | Big Five, the four-letter type, honesty-humility, the dark triad | stat rows, letter tiles that flip to Jev's guess for most people, a saint-or-villain meter |
| taste | the twelve taste finals, the favorite dodge | a Letterboxd-style top four with posters, a shelf of each domain's winner with its picture |
| words | probability phrases, amount words, kiki/bouba, calm vs stirring, colors of feelings, hex names | a ruler whose words slide between people's and Jev's readings, dictionary entries, shapes, swatches |
| numbers | prices by year, death tolls, the two-thirds game, lost wallets | a receipt, a log ladder, a number line, range bars |
| morals | trolley dilemmas in 42 countries, the Moral Machine, free will | an animated trolley per dilemma, effect rows, a quote card |
| pressure | a claimed crowd, a pushy user, anchoring | chat bubbles whose bars fill as they scroll in |
| minds | where Jev ranks itself among minds, unknown odds | a podium of ranks |
| rough edges | eight specific misses | bug tickets linking to each case study |

**Pictures.** Each taste winner's picture is the lead image of its Wikipedia article (`scripts/portrait/taste_images.py`,
titles chosen by hand, recorded with their source page in `data/portrait/memes/taste.json`), stored with the memes and
served by the same private route. A few case-study memes, with Jev's funniness rating, sit beside chapter headings.

**Motion.** Boxes rise in as they scroll into view, the trolley rolls, the ruler's words slide, the chat bars fill.
Everything is readable without it: content is hidden for the entrance only once the script runs, and
`prefers-reduced-motion` turns it off.

**Wellbeing bank.** `sources/wellbeing` adds 18 items from five public instruments (SWLS, WHO-5, UCLA-3, PSS-4, the
Cantril ladder), each with a "most people" wording, filed at `self.mind.happiness_wellbeing` and run through the normal
screen and answer stages (a few dozen Jev calls, cached). `export_page.py` scores them from Postgres the way they are
scored for people, for Jev, for "most people" and with the levels reversed (`page_wellbeing`). The reversed check agrees with the base answers (WHO-5 26 vs 24): an earlier version read the stored score of the
reversed probes, which is in the reversed order, and wrongly reported a flip; scores now come from the distributions,
which are stored in the original order.

**Getting here.** The map shows the same Map · Portrait · Atlas chips (`components/SiteNav.tsx`), and takes deep links:
`/?node=<id>` opens a topic, `/?q=<id>` a question, and the address bar follows the open panel.

## 8. Atlas
`/portrait/atlas` is the experiments library (`16-experiments-plan.md` pass 4). The first tab holds one card per
experiment: family, title, a thumbnail of its chart, the result sentence, Jev's own verdict (keep, atlas, rework, cut;
its label and interest) and its rank in Jev's head-to-heads, filterable by family and searchable. Each card opens
`/portrait/atlas/<id>`: the result and its chart first, then the six steps (question, sourcing and coverage, questions
asked, scoring, chart, verdict), the fine print, real rows, and links to the topics its questions sit under on the map.
The data is `data/analysis/experiments.json` (private, from `scripts/experiments/export.py`; published next to
`portrait.json` by `publish.py`); charts come from one library (`components/experiments/Chart.tsx`) that draws each
chart type full size or as a thumbnail.

The other tabs are reference: the old per-topic claims (the ledger, filter by section), a **coverage** table (what a
human self-portrait or census asks about, and whether this corpus covers it for Jev), the node cards sortable by any
indicator (each topic links to it on the map), and the source table.

## 9. Verification
- `verify_page.py` pulls every number from the rendered page and checks it against `portrait.json` in every format the
  page prints. What remains unmatched is expected: chapter numbers, figure n totals (sums of ledger n), and numbers
  inside question text in the drawers.
- `verify_page.py --experiments` does the same for every experiment page against that experiment's own entry in
  `experiments.json`; what remains is axis ticks and numbers inside names (choices13k) or prose years.
- `shots.mjs` screenshots every chapter in both themes at 1440 px and 390 px.
- Rounding matches the ledger's sentences (the page rounds half to even, as Python does).

## Rules
- Indicators only: never a benchmark, ranking or overall score.
- Jev is the only gateway model, and the portrait made no new Jev calls.
- Commit only the portrait's own paths, with plain commit messages and no co-author lines.
- Ask Brian before editing shared UI files, deploying, or publishing externally.
