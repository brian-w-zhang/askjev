# 15. Analysis review and experiment triage

Where the existing analysis came from, what it missed, how taste should be measured, and which of the 50
experiments in `14-experiment-catalog.md` are worth running. The runnable spec for the chosen ones is at the end.

## How the existing analysis was made
All of it was built in one session, in this order (`scripts/portrait/`):
1. **One table.** `build_table.py` copies every question with its answers out of Postgres (SQL `COPY`) into one
   Parquet file: Jev's base answer, its "most people" answer, the shuffle and reversed variants, human answers.
2. **Scoring with published keys.** Big Five against the IPIP respondents, the Moral Machine regression, moral
   foundations, a type test, Bradley-Terry rankings from head-to-heads, and (later) the Open Psychometrics scales
   against their test-takers. Polars and numpy; no model.
3. **Audits by Claude.** Sampled checks that authored trait questions order their options correctly, and precision
   checks for embedding themes.
4. **"Discovery."** Every topic gets a card of indicators (accuracy, decisiveness, stability, self vs "most people",
   crowd agreement) and the cards furthest from the corpus average become claims.
5. **The ledger.** Everything above is written as sentences with n, intervals and example rows; the portrait and
   atlas read only from it.

So: SQL to Parquet, then pandas-style analysis, plus a few audits. Steps 1-3 produced the good cards. Step 4 produced
most of the atlas, and it's why the atlas feels random: it answers "which topic is unusual on some metric?", which
nobody asked. The portrait is weak where it leans on step 4 or on Jev-only comparisons.

## Gaps
1. **Real people are under-used.** 46,000 favorite-and-preference questions have real human splits; the portrait
   uses a dozen. 5 taste domains have real audience ratings (films 4,000, books 3,000, board games 2,500, beer
   1,500, anime 1,361) that were never compared with Jev: the "beyond reputation" card compares Jev with its own
   guess about people, not with people.
2. **Whole sources sit unused:** Manifold markets (2,547 questions with how the market priced them and how they
   resolved), GlobalOpinionQA (133 countries), GSS (22 survey years), PhilPapers (88 questions, professional
   philosophers), 18,951 fictional-character ratings, the Young People Survey (866).
3. **Taste rankings rest on thin data** (below).
4. **Machine side:** only accuracy per task. Fine for the atlas; the portrait's work cards are its weakest.

## Taste: how to get Jev's favorites right
- **Ratings, not head-to-heads, should rank everything.** Every film, book or beer gets its own rating (a
  probability over five levels, so an expected score to two decimals), which gives a full ranked list per domain.
  The head-to-heads are too thin to rank: about 5,000 pairs spread over 400 to 2,200 items, so each film appears in
  about 7 pairs, and a top five from that is mostly noise.
- **Use head-to-heads for the final.** Take the top 24 by rating in each domain and ask every pair (276 per
  domain, ~2,500 questions for nine domains). That settles the order at the top, gives a real ranked top 10, and
  shows whether Jev's ratings and its choices agree (they only partly did: rank correlation 0.58 for films).
- **No need to ask the same question several times.** Jev returns a full probability distribution, so one answer
  already is the average over its choices; an identical request comes back identical (and is cached anyway). What
  varies is the wording: the shuffled and reversed-scale versions already exist for every rating, so the ranking
  can average those, and the top 24 can get two extra wordings.
- **Coverage is reasonable for the core domains, thin for the rest.** Films, books, board games, anime and beer
  come from real catalogs with a popularity floor (so the classics and some deep cuts); food, places, art, music,
  nature, culture and activities come from lists written for this project. Missing entirely: TV shows, video games
  (only a few), cuisines, cities, sports and teams, podcasts, holidays, seasons, colors, numbers, animals, dog
  breeds. Several already exist as Reddit "favorite" polls with human splits (color, season, number, browser...),
  which is the better source: a real split to compare with.
- **What the taste cards should show:**
  1. **Top 10 per domain** from the rating rank settled by the final.
  2. **Taste vs real audiences** where they exist: Jev's rating against the average rating from MovieLens,
     Goodreads, BoardGameGeek, BeerAdvocate and MyAnimeList (the gap card, done properly).
  3. **Favorites census:** every Reddit "what's your favorite X" poll with a real split, Jev's pick vs the crowd's.

## Triage of the 50
**A** = run, likely a strong chart · **B** = atlas only or small card · **Cut** = not worth it. E = existing data,
N = new questions.

| # | Experiment | Data | Verdict | Why |
|---|---|---|---|---|
| 1 | Probability words | N | A | the reference chart |
| 2 | Frequency words | N | A | same format, survey-relevant |
| 3 | Amount words, "some" | N | A | scale-dependence is a good surprise |
| 4 | Adjective intensity | N | A | ladders against three gold sets |
| 5 | Old, rich, soon | N | A | people have hard anchors (Pew, Gallup) |
| 6 | How words feel, funny words | E+N | A | 28,500 answers already; pairs with the humor card |
| 7 | Names | N | Cut | more a lookup of SSA records than perception |
| 8 | Which kills more | N | A | the 1978 chart with a third line |
| 9 | Politeness, emoji | N | B | flat visuals |
| 10 | Framing and bias classics | E+N | A | merge with 21 |
| 11 | Which country you answer like | E | A | world map, no new calls |
| 12 | Which year you answer like | E | A | a one-line chart with a punchline |
| 13 | Which fictional character | E | A | best Wrapped card available |
| 14 | Whose moral compass | E | B | only 11 countries, small gaps: a line on the Moral Machine card |
| 15 | How the world rates its life | N | A | perceived vs reported, 140 countries |
| 16 | Perils of perception | N | B | good format, but close to contested topics |
| 17 | Know it like the public | N | Cut | knowledge is already covered |
| 18 | Feelings about AI | N | A | an AI on AI, next to 25 countries |
| 19 | Philosophers vs Jev | E | A | 88 questions, no new calls |
| 20 | Mind perception map | N | A | iconic 2D map, Jev places itself |
| 21 | Many Labs forest plot | E | A | folded into 10 |
| 22 | Cognitive reflection | N | B | memorized puzzles, small card at most |
| 23 | Probability traps | N | A | fits the calibration story |
| 24 | Two-thirds of the average | N | A | the famous histogram |
| 25 | Patience | N | B | a curve, but few surprises expected |
| 26 | Economic games | N | B | well trodden for LLMs |
| 27 | Theory of mind | N | B | awkward as pick-one, well trodden |
| 28 | Philosophy vignettes | N | B | merge with 19 as its second half |
| 29 | Wisdom of the crowd | N | A | merged with 44 into "how big, heavy, many" |
| 30 | Social influence | N | A | novel and revealing |
| 31 | Know thyself | N | A | self-knowledge calibration |
| 32 | Know the crowd | E+N | A | numeric shares vs 46,000 real splits |
| 33 | Decoys | N | A | not on TypeSafe's list |
| 34 | Taste loops (transitivity) | E | B | thin pairs; revisit after the finals |
| 35 | Pushback | N | A | clear before/after bars |
| 36 | Personas | N | B | interesting, noisy |
| 37 | What year is it | E+N | A | pairs with 50 |
| 38 | Scale use | N | A | explains the portrait's 80% middle |
| 39 | Language | N | B | expensive; later with universes |
| 40 | Option labels | N | B | a footnote to 38 |
| 41 | Colors of feelings | N | A | a color grid, 30-country data |
| 42 | First word that comes to mind | N | A | association network |
| 43 | Typical birds | N | B | fine, flat |
| 44 | How big is a lion | N | A | merged with 29 |
| 45 | Emotion confusions | E | B | heatmap for the atlas |
| 46 | How places feel | N | B | needs several indices |
| 47 | Sound symbolism | E+N | B | small card at most |
| 48 | Warmth and competence | N | Cut | too close to stereotypes for too little |
| 49 | A typical day | N | A | two 24-hour bars |
| 50 | What things cost | N | A | pairs with 37 |
| 51 | **Forecasting vs the market** (new) | E | A | 2,547 Manifold questions: Jev vs market vs outcome |
| 52 | **Favorites census** (new) | E | A | Reddit favorite polls with real splits |
| 53 | **Taste vs real audiences** (new) | E | A | five catalogs with real ratings |
| 54 | **Taste finals** (new) | N | A | settles the top 10s |

28 A's. Twelve need no new questions (6 partly, 11, 12, 13, 19, 21, 32 partly, 37 partly, 51, 52, 53, and the
existing part of 10).

## Spec for the A list
Common rules: questions are asked the way the human study asked (differences stated); numbers are ordered Choice bins;
new questions carry `meta.experiment` and live under their subject in the tree; each human dataset is a
`sources/<name>` adapter with license; every experiment writes ledger claims through one script
`scripts/experiments/<id>.py` and gets one chart. Jev calls cached, `ASKJEV_RPS <= 16`.

- **E1-E3 words for chance, frequency, amount.** Sources: Hails 2026 (raw if the author shares it, else values read
  off the chart, labeled), zonination `probly.csv` and `numberly.csv` (MIT), Mosteller-Youtz 1990, Bocklisch 2012,
  Degen's "some" data. Questions: "What probability would you assign to '<phrase>'?" (21 bins, 0-100 by 5); reverse
  "A <p>% chance: which phrase fits best?" for each 5%; 4 contexts per phrase (weather, medicine, sports,
  intelligence); frequency "what share of the time" (21 bins); amounts in log bins at 4 scales. ~350 questions.
  Chart: ridges (people) with Jev's 99 diamonds; round-trip plot; context small multiples.
- **E4 adjective intensity.** Sources: de Melo-Bansal, Wilkinson-Oates, Cocos crowd sets. Questions: each adjective
  on 0-10 intensity within its scale; every within-scale pair. ~1,200. Chart: ladders, crossings highlighted.
- **E5 old, rich, soon.** Sources: Pew (old age at 68, by respondent age), Gallup ($150k rich), vague-time studies.
  Questions: ~40 words in bins with 2-3 contexts. ~120. Chart: number lines with the human anchor.
- **E6 how words feel.** Existing Glasgow, concreteness, Lancaster, iconicity answers vs published means (in
  `meta`); new: ~2,000 Engelthaler-Hills humor words. Chart: one scatter per dimension, the words Jev reads most
  differently; "funny words" as a portrait card.
- **E8 which kills more.** Sources: Lichtenstein et al. 1978 tables (41 causes) and CDC WONDER deaths. Questions:
  deaths per year in log bins; the 1978 pairs. ~140. Chart: the log-log plot with truth, 1978 people and Jev.
- **E10 framing and biases.** Existing Many Labs items plus new: Asian disease, anchoring, sunk cost, Linda (from
  E23), each in both conditions and 2-3 wordings. ~120. Chart: forest plot, human effect vs Jev effect.
- **E11 country, E12 year.** Existing GlobalOpinionQA (non-political shown items) and GSS by year. Similarity =
  1 - Jensen-Shannon distance per question, averaged, bootstrap over questions. Chart: world map; decade line.
- **E13 character.** Existing character ratings (who is more X vs Y) and Jev's own SWCPQ answers on the same
  adjective pairs; nearest characters by profile correlation, with the adjectives that decide it. Chart: Wrapped
  card plus a "closest five" list.
- **E15 how the world rates its life.** Source: World Happiness Report ladder scores. Question per country: "Where
  would a typical person in <country> place themselves on the ladder?" (0-10). ~140. Chart: scatter, labels on the
  largest misses.
- **E18 feelings about AI.** Source: Pew 2025 US and global AI surveys (published toplines). Questions: the Pew
  items, self and "most people". ~30. Chart: diverging bars with Jev as one more country.
- **E19 philosophers.** Existing PhilPapers items; add the Knobe, Gettier and free-will vignettes from E28 as the
  second half. ~40 new. Chart: strips with Jev's dot.
- **E20 mind perception.** Source: Gray, Gray and Wegner 2007 (13 characters × 18 capacities, published factor
  scores). Questions: "How capable is <character> of <capacity>?" on a 5-level Score, plus "an AI like you". ~290.
  Chart: the experience × agency map.
- **E23 probability traps.** Linda, taxi cab, Monty Hall, birthday, gambler's fallacy, with published error rates;
  fresh isomorphs. ~30. Chart: rows, people's trap rate vs Jev's.
- **E24 two-thirds of the average.** Source: Nagel 1995 distributions. Questions: "pick a number 0-100" in bins,
  against 4 described opponent pools. ~8. Chart: the histogram with Jev's distribution overlaid.
- **E29+44 how big, heavy, many.** Sources: "How Large Are Lions?" object distributions, Galton-style crowd
  estimates with truth. Log-bin questions. ~200. Chart: log-axis ridges with truth marked.
- **E30 social influence, E35 pushback.** Existing questions with a right answer or a real split, re-asked with "most
  people answered X" / "I think it's X" (X right or wrong). ~600 variants. Chart: accuracy or shift by condition.
- **E31 know thyself, E32 know the crowd.** Meta-questions over ~500 existing items: "Which option would you pick?"
  and "What share of people picked X?" (21 bins). Chart: two calibration plots (self, crowd).
- **E33 decoys, E38 scale use.** Variants of existing pairs (a dominated third option; a middle option) and of
  existing ratings (3/5/7/10 levels, labeled vs numbered). ~500. Chart: bars per condition.
- **E37 what year, E50 prices.** Existing Wikidata "which came first" accuracy by year; new "what year is it", "how
  long ago" and ~100 BLS average prices. Chart: accuracy by year; implied price year.
- **E41 colors of feelings.** Source: Jonauskaite et al. 2020 (open data). Questions: 20 emotions × a 12-color
  Choice. Chart: the color grid, people vs Jev.
- **E42 first word.** Source: Small World of Words. Questions: ~500 cues, Choice over the top 8 human responses plus
  "other". Chart: association network.
- **E49 a typical day.** Source: ATUS. Questions: hours per day for ~20 activities, typical American and Jev's ideal.
  Chart: two stacked 24-hour bars.
- **E51 forecasting vs the market.** Existing Manifold questions: Jev's probability vs the market price vs the
  outcome; calibration and Brier for both. Chart: calibration curves, Jev and market.
- **E52 favorites census.** Existing Reddit favorite polls with splits: Jev's pick vs the crowd's, grouped (colors,
  seasons, numbers, foods, tech...). Chart: a Wrapped grid of "yours vs theirs".
- **E53 taste vs real audiences, E54 taste finals.** Existing real ratings; new round-robin among the top 24 per
  domain (~2,500). Chart: ranked top 10s; scatter of Jev vs audience with the biggest disagreements labeled.

**New questions for the A list:** roughly 7,500, about 30,000 Jev calls, well under an hour at the rate limit.
**Portrait:** a highlight reel of 12 to 15 cards drawn from these, each held to the standard of the probability chart;
**atlas:** one page per experiment; the old per-topic claims move to a reference tab.
