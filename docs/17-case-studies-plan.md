# 17. Experiments as case studies: the plan

The 192 experiments (`16-experiments-plan.md`, `experiments/`) have good topics, titles and verdicts. Everything under
the title reads like a developer's notes. This plan turns each experiment page into a case study an outsider can follow
and enjoy, on Brian's bar: no slop, honest, specific, fun where it earns it.

## What Brian asked for (the checklist; every item must be done)
1. **Every experiment is a case study**, written for an outsider, much more detailed than today's six short fields.
2. **Cut pipeline jargon.** No "questions asked: existing questions only; no new Jev calls", no source ids in prose.
   Anything a visitor can't understand without being the developer goes.
3. **Better answers for every section**, customized per experiment, reread twice.
4. **Jev's take:** the verdict box becomes Jev's own opinion of the experiment, stated clearly in words, built
   from Jev's own answers. The verdict, interest and rank stay, as supporting detail.
5. **Caveats, short title** (e.g. "Caveats" or "Where it could be wrong"): what could bias this experiment, and
   only what applies. Cover the human sample (Reddit, MTurk, students, one country or year), how the questions
   were phrased (ours vs the study's, described levels, option order, the word named first), coverage gaps,
   questions the screen hid, synthetic or Claude-written items and what that implies, possible training-data
   exposure (famous poems, puzzles), small n, and documented Jev limits (`01-jev.md` §6, labeled as known).
6. **All the rows, paged:** every question behind the result, not two examples. Show 5, with "show more" at the
   bottom for the next 5, and so on. Filters where useful (misses only, by group).
7. **One legend** at the top of the rows, not per row. The colors and words are "Jev's own answer", "what Jev
   thinks most people would say", "real people's answers" and "the right answer". "Jev for most people" is renamed
   everywhere: rows, charts, legends and prose.
8. **A unique meme per experiment**, woven into the page: relevant, with real meme taste, and no template reused
   across experiments. Claude edits text onto templates where needed.
9. **Hover memes on the atlas index:** hovering an experiment card shows its meme following the cursor.
10. **"On the map" gets a proper UI:** its own section on where the questions live (topics as a small tree or
    chips with counts, linking to the map), not a bare list in the sidebar.
11. **Better charts:** fix the weak ones and the thumbnails.
12. **Much better UI overall** for the experiment page and the index.
13. **One source of truth.** The site and the markdown docs render from the same write-up, with no drift.

## Where the write-up lives (item 13)
The repo is public and results are private, so:
- **Source:** `data/analysis/experiments/<id>.case.md` (private), one per experiment. It holds front matter (memes,
  caveats and pull-quote rows as structured fields) and named sections in markdown.
- **Site:** `scripts/experiments/export.py` parses it into `experiments.json`, and the page renders every section.
- **Public doc:** `docs/experiments/<id>.md` is generated from the same file by `lib.render()`, keeping only the
  method sections (the question, where the data comes from, what Jev was asked, how it's measured, caveats that
  don't state results). Findings, observations and memes stay private.
- **Numbers:** a write-up quotes numbers only from its result file. A check script
  (`scripts/experiments/check_cases.py`) flags any number in a case file that isn't in its `<id>.json`, the same
  way `verify_page.py` checks the page.

## Page structure (items 1-12)
Top to bottom:
1. **Header:** family, title, a one-line question, and the meme as a small OS-window card beside the title
   (stacked on phones).
2. **The result:** the result sentence, the chart (improved), and a one-line "how to read this chart".
3. **The case study**, as readable sections with short headings:
   - "Why ask this": the question and why it's interesting.
   - "The people and the data": who the humans are, the source, and the size.
   - "What Jev was asked": the real wording, one example, format and count, in plain words.
   - "How we measured it".
   - "What we found": the result, then 2-4 observations with numbers and real examples.
   - "What it means, and what it doesn't".
4. **Jev's take (sidebar):** a quoted first-person-style paragraph built from Jev's answers, with the verdict,
   interest and rank underneath.
5. **Caveats (sidebar):** a short bulleted list, only what applies.
6. **Where these questions live:** its own section with the topics as chips or a mini tree, counts, and map links.
7. **Every question:** the legend, then rows 5 at a time with "show more", and filters.
8. **Pager** to the previous and next experiment.

## Jev's take (item 4)
Jev answers only yes/no, pick-one or scale questions, so its opinion is assembled from new questions put to it
about each experiment's card. For example: would you have expected this result; is the comparison with these people
fair; which caveat matters most (Choice over that experiment's caveats); how much should a reader trust it
(Score). Cached, `ASKJEV_RPS <= 16`, Jev as the only gateway model. The paragraph is templated from those answers,
never invented, and each claim in it links back to the answer behind it.

## Memes (items 8-9)
- **Pick:** for each experiment, a format that fits its joke. Draw on current and classic formats (distracted
  boyfriend, drake, galaxy brain, "is this a pigeon", Gru's plan, two buttons, this is fine, expanding brain,
  stonks, surprised Pikachu, Woman yelling at cat, "they don't know", Bernie "I am once again asking", Anakin and
  Padmé, Spider-Man pointing, and many more). No reuse across experiments; nothing boomer or forced; no politics.
  If there's no good fit, cut the meme rather than force one, and count the cuts.
- **Make:** templates go in the gitignored `data/portrait/memes/templates/`, captioned images in
  `data/portrait/memes/exp/<id>.webp` via one script (`scripts/experiments/memes.py`, text boxes per template).
  Served privately like the portrait's memes, with captions labeled as ours.
- **Hover:** a React component on the index shows the hovered card's meme following the cursor (a ref and
  `requestAnimationFrame`, no re-render per mouse move, eased). It's off on touch devices and with
  prefers-reduced-motion, and never covers the card's text.

## Rows (items 6-7)
- A private route (`/portrait/atlas/rows?id=&page=`) serves every question id an experiment used, from a list the
  export writes. The page loads 5 at a time.
- One legend component at the top. The row component drops its per-row "Jev ... · Jev for most people ..." text in
  favor of colors and a hover or tap detail.

## Steps
1. **Rows and legend** (routes, export of every id, pager, filters, rename everywhere).
2. **Case file format, parser, renderer and check script.** Generate a first draft of every case file from today's
   spec and result, then rewrite each by hand, family by family (subagents allowed, each family reread twice).
3. **Jev's take:** questions, run, templated paragraph.
4. **Caveats:** a per-experiment list, only what applies.
5. **Memes:** pick 192 (a list with rationale, checked for reuse), template sourcing, captioning script, page
   placement, hover.
6. **Charts and thumbnails:** audit all chart types at 1440 and 390, and fix the weak ones.
7. **Page and index UI** redesign, including the "where these questions live" section.
8. **Audit:** check_cases.py clean; a sampled read against the result files; one full reread for slop.
9. **Ship:** sweep.mjs, interact.mjs (with paging and hover), verify_page.py --experiments, vitals.mjs,
   screenshots in both themes; export, publish.py, deploy; prod must match local.

## Rules
Results, data and memes stay private. Commit only own paths, with plain messages and no co-author lines; don't push.
Check session recall before touching shared UI files. No politics. Indicators, never a benchmark.
