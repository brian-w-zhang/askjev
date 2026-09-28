# taste_pairs_audience

family: taste

## 1. Question
Offered two films, books, board games, anime, beers or artists, does Jev pick the one the real audience preferred, and is it closer when choosing for itself or when guessing what most people would pick?

Head-to-heads are how people actually choose. The audiences' splits are real (users who rated or played both), so they test Jev's taste directly; comparing its own pick with its guess of 'most people' shows which of its two views of taste is closer to real crowds.

## 2. Sourcing
Existing head-to-head questions ('Which movie would you rather watch?') from six catalogs, each with the share of users who rated (or played) both and preferred each side: MovieLens 32M, goodbooks-10k, BoardGameGeek, MyAnimeList, BeerAdvocate, Last.fm 360K. About 27,000 pairs. A different method from taste_vs_audience_* (one-at-a-time ratings).

Sources: `movielens_pairs`, `goodreads_pairs`, `boardgame_pairs`, `anime_pairs`, `beer_pairs`, `music_pairs`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per catalog, the share of pairs where Jev's own pick (averaged over both option orders) is the audience's majority, and the same for its 'most people' guess, with 90% bootstrap intervals over pairs; agreement by the audience's margin (how lopsided the split was).

## 5. Visualization
Dots per catalog: agreement of Jev's own pick (square) and of its guess for most people (ring), with a 50% line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.785, top verdict `portrait`.

## Compared with
the audiences of six catalogs (users who rated or played both items)

## Limits
Audiences rate what they chose to watch or read, so their splits lean toward fans. Last.fm's split is play counts, not ratings. Pairs were drawn within genre, so many are close calls.

Results: `data/analysis/experiments/taste_pairs_audience.json` (private). Code: `scripts/experiments/`.
