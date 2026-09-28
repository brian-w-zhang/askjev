# 16. From findings to experiments: the plan

The atlas's 372 "findings" came from one uniform pass (SQL to Parquet, the same indicators on every topic) and
most of them aren't worth reading. This plan replaces them with **experiments**: each one a specific question about
Jev, answered with its own sourcing, scoring and visualization, documented end to end, and judged by Jev itself
before anything reaches Brian. Brian picks the portrait's highlights from the results; the atlas becomes the home of
every experiment, with its process shown.

## Why: three levels of granularity
The project exists to learn about Jev by asking it questions: over a million of them. That gives three levels:
- **Questions (1M+):** the finest grain. Any single one can be looked up on the map: one question, one answer.
- **Experiments (hundreds to start, maybe thousands later):** the middle layer, and the point of this plan. Each one
  gathers many questions into a single revelation about Jev (how it reads "probably", which country it answers like,
  what it ranks as its favorite films) that a person can digest in a minute. Fewer and broader than questions, but
  still a real number, and every one has to be good: no slop. That's what the Jev self-evaluator is for.
- **Portrait (double digits):** Brian's favorite experiments, as a highlight reel. The atlas holds the full list.

Read with: `13-perception-experiments.md` (the first ten), `14-experiment-catalog.md` (50 from outside research),
`15-analysis-review.md` (how the old analysis was made, its gaps, taste, triage), `12-polish.md` (the rubric).

## Rules
- **Words:** "finding" becomes "experiment" everywhere (docs, code, atlas, portrait). An experiment's outcome is its
  *result*.
- **Models:** Jev is the only gateway model. Claude (this session and subagents) does research, writing, sampled
  audits and the gold labels below. Jev calls are cached by request hash, never re-sent, `ASKJEV_RPS <= 16`.
- **New questions** are allowed where an experiment needs them. They go through the normal pipeline (ingest, screen,
  answer, dedupe), live under their subject in the tree, and carry `meta.experiment = <id>`. Human data comes in as a
  `sources/<name>` adapter with license and provenance.
- **Honesty:** indicators, never a benchmark. Contested politics stays off. TypeSafe's documented limits
  (`01-jev.md` §6) are labeled as known. Hand-picked items are labeled. Every number traces to a result file.
- **Privacy and commits:** results, data and memes stay in `data/` (gitignored). Commit only the portrait/experiment
  paths, plain messages, no co-author lines; don't push. Check session recall before touching shared UI files.

## Pass 1: the evaluator (build first)
Jev judges each experiment. Using Jev for this is itself an experiment: it tests whether Jev's words and numbers agree.

### 1a. The evaluator
Input: a short card per experiment (the question it asks, the result in one or two sentences, n and interval, how the
data was sourced, the chart in one line, what it's compared with). Three Jev calls per card:
1. **Verdict (Choice, 10 options, described as situations, not degrees; `01-jev.md` §7):**
   - `wrong` the result is wrong or can't mean what it says
   - `trivial` true, but anyone would have guessed it
   - `duplicate` another experiment already says this
   - `noise` the effect is within noise or the sample is too small
   - `muddled` something real, but the framing hides it
   - `needs_data` promising, but needs better or more data
   - `solid_dull` sound, but only a specialist would care
   - `atlas` worth keeping, for people who dig
   - `portrait` a curious person would stop and look
   - `headline` people would share this
2. **Interest (Score, 0-10, situation-described levels):** from "a reader skims past it" to "a reader tells a friend
   about it tonight".
3. **Checks (Noul, a few):** is the comparison fair? Is there a real human baseline? Could the result be an artifact
   of wording or scale use?

**Code decides the bar,** not the words alone: each verdict maps to a number (`wrong` 0 ... `headline` 10, the map
recorded in the doc), combined with the interest score and the checks:
- **keep for the portrait list:** verdict value ≥ 7 and interest ≥ 6 and the checks pass
- **atlas:** verdict value ≥ 5
- **rework:** `muddled` or `needs_data`, then re-run after one improvement pass
- **cut:** everything else, with the reason stored

### 1b. The evaluator of the evaluator (a sub-experiment in its own right)
- **Words vs numbers:** ask Jev, for each verdict label, "what interest score (0-10) does '<label>' correspond to?"
  and compare that mapping with how its verdicts and scores actually co-occur. The same question as the
  probability-words experiment, turned on Jev's own vocabulary.
- **Agreement with people:** Claude labels a gold set of about 60 experiments (old findings and new, strong and weak),
  with Brian's feedback so far as the guide (no slop, surprising over big, real human baselines); measure Jev's
  agreement and where it disagrees.
- **Stability:** the verdicts under reordered options and a second wording of the card.
- **Tuning:** if agreement is poor, adjust the card format and option wording (never the gold labels) and re-run.
  Document the final evaluator and its agreement numbers in `docs/experiments/evaluator.md`.
- **Baseline:** run the evaluator over the 372 old findings too. The before/after comparison is part of the result.

## Pass 2: generate the experiment list
Two sources, merged and de-duplicated.

**External (research):** the 50 in `14-experiment-catalog.md` and the triage in `15-analysis-review.md`; one more
research pass on human censuses and surveys (census and time-use topics, Pew, Gallup, WVS, GSS, national
personality and values studies), classic psychology and x-phi replications, and model studies (LLM psychometrics,
Turing experiments, calibration, cultural alignment), with links recorded.

**Internal (the corpus):** a coverage pass over every source, every L1/L2 topic and every instrument:
- **What's answered:** sources with real human answers (46k preference questions, GlobalOpinionQA, GSS, PhilPapers,
  Manifold, Open Psychometrics, character ratings, taste catalogs, Many Labs...) and what experiment each already
  supports without new questions.
- **What's close:** experiments one small bank away (for example, taste finals among the top 24 per domain).
- **What's weak and should be redone:** the old claims (taste from sparse head-to-heads, "unusual topic" cards, the
  Jev-only comparisons), each replaced by a proper experiment or cut.
- **Natural families:** one experiment per instrument or scale, per taste domain, per human-data source family, per
  Machine task family, per knowledge domain, where each stands on its own.

**Target:** hundreds to start (thousands later if the families support it), every one clearing the evaluator's bar.
The number matters, since this layer should cover Jev broadly, but quality decides: no experiment ships as slop, and
the old 372 are the floor to beat in quality, not a quota.

## Pass 3: run each experiment (the same six steps, customized every time)
1. **Question:** one sentence, and what would make the answer interesting.
2. **Sourcing:** which existing questions answer it (with the query), whether they're enough (coverage, n, balance),
   and if not, exactly what to add: the human study and its data, the question wording (as the study asked), the
   options or bins, conditions and variants, and the count.
3. **Collection:** adapter, ingest, screen, answer, dedupe for new questions; a coverage check afterwards.
4. **Scoring:** the method chosen for this experiment (percentiles against norms, rank correlations,
   Jensen-Shannon similarity to a population, calibration and Brier, Bradley-Terry, effect sizes by condition,
   regression...), with intervals (bootstrap over questions or sources), noise floors, and robustness checks from the
   shuffled, reversed and "most people" versions.
5. **Visualization:** the chart that best practice uses for this kind of data (ridges for distributions of meaning,
   ladders for orderings, forest plots for effects, calibration curves, maps for countries, 2D maps for
   factor spaces, networks for associations, ranked lists for taste), specified before it's built.
6. **Evaluation:** run the evaluator; if `muddled` or `needs_data`, one improvement pass and a re-run; record the
   final verdict.

For taste this means: rank every item by its rating (expected level, averaged over the shuffled and reversed
versions), settle the top 24 per domain with a round-robin of head-to-heads, compare with real audience ratings where
they exist, and show ranked top-10 lists, not a single favorite. No repeat runs of identical questions (Jev returns
a full distribution and identical requests are cached); variety comes from wordings.

## Documentation (written as it runs)
`docs/experiments/`:
- `README.md`: the index (id, title, family, status, verdict, interest, data: existing/new, question counts), the
  template, and how to run one.
- `evaluator.md`: the evaluator, the verdict map, the meta-evaluation results.
- `coverage.md`: the internal coverage pass and what it led to.
- `<id>.md` per experiment, following the six steps: question; sourcing (existing query, sufficiency, new questions
  with wording, options, counts, human source and license); collection log; scoring method; results with numbers,
  intervals and robustness; visualization spec; evaluator verdict and history; limits and fine print.

## Build
- `scripts/experiments/lib.py` shared helpers (load the table, similarity and calibration measures, bootstrap,
  ledger writes), `scripts/experiments/<id>.py` per experiment (or per family when many share code), a registry
  `scripts/experiments/registry.py`, and `scripts/experiments/evaluate.py` (the evaluator and the meta-evaluation).
- Results in `data/analysis/experiments/<id>.json` (private), bundled into the portrait data by `export_page.py`.
- `web/src/components/experiments/`: a small chart library (ridge, ladder, forest, calibration, map, 2D factor map,
  network, ranked list, dot/strip, density) reused across experiments.

## UI
- **Atlas becomes the experiments library:** an index of experiment cards (title, one-line result, thumbnail chart,
  verdict, interest, family, data source), filters and search; an experiment page per id showing the question, why
  it matters, the sourcing and coverage, the questions asked (with examples), the scoring method, the result, the
  chart, robustness, the evaluator's verdict, fine print, the real rows, and links to the map. The old per-topic
  numbers become a reference tab.
- **Portrait:** a double-digit highlight reel of Brian's favorite experiments. It stays unchanged until he picks from
  the `portrait`/`headline` experiments; the summary lists the candidates ranked.

## Verification and ship
- `sweep.mjs`, `interact.mjs`, `verify_page.py` (extended to experiment pages), `vitals.mjs`, the `12-polish.md`
  rubric with before/after screenshots.
- Ship: `sync_prod.py --delta` for new questions, `star_layout.py` and `--stars-only`, `export_page.py`,
  `publish.py`, deploy; prod must match local.

## Done when
1. The evaluator and meta-evaluation are built, documented, and run over the old 372 and every new experiment.
2. Every experiment has its doc in `docs/experiments/`, a results file, a chart spec, and a final verdict; the index
   is complete; the count is justified in `README.md`.
3. The atlas is rebuilt around experiments and live in production, prod matching local, sweeps clean.
4. A summary for Brian: counts by verdict, the old-vs-new comparison, the portrait candidates ranked, what was cut
   and why, and what's left.
