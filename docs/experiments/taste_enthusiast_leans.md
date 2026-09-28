# taste_enthusiast_leans

family: taste

## 1. Question
Enthusiast audiences have leans of their own: do BoardGameGeek users prefer newer games and BeerAdvocate reviewers stronger beers, and does Jev share those leans?

An audience's taste is partly the audience: hobbyists chase the new and the extreme. Where Jev parts from them in a systematic direction, that direction says what kind of taste it has.

## 2. Sourcing
Existing head-to-heads from BoardGameGeek (years and rating counts per game), BeerAdvocate (ABV and review counts per beer) and MovieLens as a control (years and rating counts), with the audience's split. Pairs are kept when the label (year or style) identifies which item is which: about 4,700 board-game, 4,650 film and 1,550 beer pairs.

Sources: `boardgame_pairs`, `beer_pairs`, `movielens_pairs`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per catalog, the share of pairs where the pick is the older item (films, games) or the weaker beer (lower ABV), and where it is the more-rated item, for the audience's majority, Jev's own pick and its 'most people' guess, with 90% bootstrap intervals.

## 5. Visualization
Paired bars per catalog and lean: audience majority vs Jev.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.97, top verdict `headline`.

## Compared with
BoardGameGeek users, BeerAdvocate reviewers, MovieLens users (who rated both items)

## Limits
Older games have had more time to collect ratings, so 'older' and 'more rated' overlap. Pairs were drawn within subdomain or style family.

Results: `data/analysis/experiments/taste_enthusiast_leans.json` (private). Code: `scripts/experiments/`.
