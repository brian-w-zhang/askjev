# taste_pairs_audience

family: taste

## Why ask this
"Seabiscuit or Closer tonight?" Asking which of two things someone would rather have is the simplest test of taste, and for six catalogs the record shows how thousands of real people split between the same two items.

People ask models exactly this kind of question when picking a film, a book or a game, and a model can answer in two ways: with its own pick, or with its guess of what most people would choose. Comparing both with real audiences shows which of its two views of taste is closer to the crowd.

## The people and the data
Six real audiences, each from a public dataset: MovieLens users (films, from MovieLens 32M), Goodreads readers (books, from goodbooks-10k), BoardGameGeek users (board games), MyAnimeList users (anime), BeerAdvocate reviewers (beers) and Last.fm listeners (music artists, from Last.fm 360K). For each pair, the audience's split is the share of people who rated both items and rated each one higher (for Last.fm, who played each one more), with ties split. Pairs were drawn within a genre or style, so a film faces a film of its own kind.

## What Jev was asked
Each pair as a simple choice:

> Which movie would you rather watch?
> *Closer (2004) · Seabiscuit (2003)*

Once for itself, and once with the instruction "Do not give your own view. Choose the answer that most people would give (the most common human answer)". Each was asked with the options in both orders.

## How it was measured
For each catalog, the share of pairs where Jev's top pick is the audience's majority pick, with a 90% interval. The same for its guess of most people. Then the agreement split by how lopsided the audience was.

## Caveats
- **The audience is the people who rated both.** For each pair, the audience is only the users who rated both items (at least a few hundred, fewer for books and beers), which leans toward fans. On Last.fm it's play counts, not ratings.
- **Close calls on purpose.** Pairs were drawn within a genre or style, so many are close calls where the audience itself is split nearly evenly. That caps how high agreement can go.
- **Famous items.** Every item is well known, and Jev has read about them. Agreeing with the audience may partly mean knowing which item has the better reputation.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
