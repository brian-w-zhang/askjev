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
9. **Atlas index:** cards highlight in pink on hover; memes appear only on the case study page, beside the findings.
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
Top to bottom, every block the same width, the finding first (the order data stories and research write-ups use:
the finding and a short summary up front, the method compact and after it):
1. **Header:** family, title, a one-line question.
2. **The result:** the result sentence, the chart, a one-line "how to read this", the fine print.
3. **In short:** 2-3 takeaways (front matter `takeaways`).
4. **What the data shows,** with the meme floated beside it, sized by its shape; then **What it means, and what it
   doesn't**.
5. **Caveats** beside **Jev on this experiment**: Jev's answers to questions about the experiment, shown as
   answers.
6. **Why ask this**, then **How this was done**: the people and the data, what Jev was asked, how it was measured.
7. **Where these questions live**, then **Every question** (each opens on the map), then the pager.

Case studies are written in the third person: no "we", "our" or "us".

## Ranking
Jev's rank is mostly Jev's own head-to-heads over the whole case studies (`scripts/experiments/rank.py`): it reads
two write-ups side by side (result, takeaways, why ask this, what the data shows, what it means, caveats) and picks
the one that teaches a curious reader more, each pair in both orders; every experiment meets about 14 others, and
Bradley-Terry turns the picks into one strength. The rank is a weighted sum of standardized parts: that strength (0.60),
how sure Jev is a curious person would find it interesting (0.15), how much a reader should rely on the result (0.15)
and how fair the comparison is (0.10). Whether a result describes Jev, and whether Jev saw it coming, are facts about
the experiment, not its quality, so they're sorts on the index instead. The index sorts by Jev's rank, most interesting,
describes Jev most or least, most surprising to Jev, most reliable, fairest comparison, most questions and family;
under any sort but rank, family and size, each card shows the value it's sorted by next to its question count.

## Jev's take (item 4)
Jev answers only yes/no, pick-one or scale questions, so its opinion is assembled from new questions put to it
about each experiment's card. For example: would you have expected this result; is the comparison with these people
fair; which caveat matters most (Choice over that experiment's caveats); how much should a reader trust it
(Score); and would a curious person find it interesting to read (yes/no; Jev says yes to all 192, so only its certainty ranks). Cached, `ASKJEV_RPS <= 16`, Jev as the only
gateway model. The page shows the answers themselves, each with its probability or level, not a paragraph built
from them.

## Memes (items 8-9)
- **Pick:** for each experiment, a format that fits its joke. Draw on current and classic formats (distracted
  boyfriend, drake, galaxy brain, "is this a pigeon", Gru's plan, two buttons, this is fine, expanding brain,
  stonks, surprised Pikachu, Woman yelling at cat, "they don't know", Bernie "I am once again asking", Anakin and
  Padmé, Spider-Man pointing, and many more). No reuse across experiments; nothing boomer or forced; no politics.
  If there's no good fit, cut the meme rather than force one, and count the cuts.
- **Make:** templates go in the gitignored `data/portrait/memes/templates/`, captioned images in
  `data/portrait/memes/exp/<id>.webp` via one script (`scripts/experiments/memes.py`, text boxes per template).
  Served privately like the portrait's memes, with captions labeled as ours.
- **Never punch at a country, its people or a named person.** Results by country are captioned as Jev's misses, not
  as a joke about the place, and templates that are photos of real private people or play on poor countries are out.
- **Jev rates each meme:** it can't see images, so it reads the meme in words (the template's name, a hand-written
  description of the image and how the format is used, the words on it, the caption and the result it's about) and
  answers "How funny is this meme?" on five levels described as situations, from no reaction to "the kind of meme
  people send to friends" (`scripts/experiments/meme_funny.py`). The page shows its pick and how sure it is of each
  level under the meme.

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
   placement.
6. **Charts and thumbnails:** audit all chart types at 1440 and 390, and fix the weak ones.
7. **Page and index UI** redesign, including the "where these questions live" section.
8. **Audit:** check_cases.py clean; a sampled read against the result files; one full reread for slop.
9. **Ship:** sweep.mjs, interact.mjs (with paging), verify_page.py --experiments, vitals.mjs,
   screenshots in both themes; export, publish.py, deploy; prod must match local.

## Status (2026-09-28)
Steps 1-9 are done and live. 189 of 192 experiments have a meme; 3 were cut rather than forced, each with its reason
in the private assignment file (`data/portrait/memes/assign.py`, `CUT`). Every case file was checked against its
result file by `cases.py check` and audited claim by claim; 98 offensive jokes and captions behind the humor
experiments were hidden. Open: rebuild the map's star snapshot so hidden questions drop from it, and redraw the few
thumbnails that are a single line or dot.

## Rules
Results, data and memes stay private. Commit only own paths, with plain messages and no co-author lines; don't push.
Check session recall before touching shared UI files. No politics. Indicators, never a benchmark.

## Style guide for case files
The exemplar is `words_arousal_is_mood` (private; ask for it). Every case file follows it.
- **Reader:** a curious outsider who has never seen the project. No pipeline words: never "probe", "source",
  "node", "parquet", "no new calls", "existing questions", "the screen", "Jev for most people", ids in backticks or
  family names. Say "a content filter hides political and sensitive questions from the site" the first time hidden
  questions matter, "what Jev thinks most people would say" for the human frame, "the answer order reversed" for
  robustness checks.
- **Why ask this:** the phenomenon in plain words, with a concrete everyday example, and why a model getting it
  wrong would matter. Two short paragraphs.
- **The people and the data:** who the humans are (where, when, how recruited, how many, paid or volunteers), what
  the dataset is famous for, and the license if it's unusual. Only verified facts: from the source's `source.yaml` or
  adapter, the result file, or a source you checked (put outside numbers in `facts:` with the citation). Never
  from memory.
- **What Jev was asked:** quote one real question with its answer options exactly as Jev saw them (from the
  question table), then the format, how many, and the checks (answer order reversed or shuffled, "most people"
  version) in plain words. Say if the wording is the study's or ours.
- **How we measured it:** the comparison in words a reader can follow; define any statistic in one clause (rank
  correlation: 1 same order, 0 no relation). No formulas.
- **What we found:** the headline, then 2-4 concrete observations with numbers and named examples, as bullets
  where a list reads better. Every number must be in the result file (or a cited fact); `cases.py check` enforces it.
- **What it means, and what it doesn't:** what a reader should take away, and the limits of the claim. One or two
  short paragraphs. Point to related experiments by their titles when useful.
- **Caveats (front matter):** 2-5 items, each a short label and 1-3 sentences, only what applies to this one:
  the human sample, our wording vs the study's (and any lean in our examples or level descriptions), option or
  word order, coverage gaps, questions the content filter hid (with the count if known), synthetic or
  Claude-written items and what that implies, possible training-data exposure (famous poems, puzzles, trivia),
  small n, and documented Jev limits (`01-jev.md` §6, said to be known). Think about where bias actually creeps in
  for this experiment; check the real question wording and levels for leading examples, as the exemplar does.
- **Result (front matter):** the headline sentence, rewritten for an outsider if the script's is stiff; same
  numbers. **chart_note:** one sentence on how to read the chart.
- **Tone:** plain, specific, honest; fun where it earns it; no sweeping claims, no hype words, no "notably",
  "crucially", "fascinating". Indicators, never a benchmark or a score. Hand-picked examples are labeled.
- **Check:** `uv run python scripts/experiments/cases.py check <id>` must be clean, then reread the file twice.
