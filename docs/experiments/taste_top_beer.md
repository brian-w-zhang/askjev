# taste_top_beer

family: taste · new questions: 276

## 1. Question
If Jev ranked every beer it was asked about, what would its top ten be?

Wrapped-style favorites, but from every item it rated and then a real final among the best, rather than a handful of head-to-heads; the interesting part is what rises to the top and what sinks.

## 2. Sourcing
Existing one-at-a-time rating questions ("How much would you enjoy ...", five situation-described levels) under Self > Lifestyle > Ratings > beer_ratings; items from BeerAdvocate (reviewed beers). Every item is rated, so the whole list can be ranked; the ratings crowd the top with near-ties, so the top 24 play a round-robin final (new questions, sources/taste_finals).

Sources: `taste_ratings`, `taste_finals`

## 3. Collection
The ratings exist. New: the finals, 276 head-to-heads among the top 24 ("Which film would you rather watch?"), each asked in both option orders.

## 4. Scoring
Ratings: each item's expected level (0-4), averaged with the same question asked with the levels reversed. Finals: Jev's probability for each side, averaged over both orders, summed into soft wins; the order is the Bradley-Terry strength fitted to all 276 games. Intransitive triads (A beats B, B beats C, C beats A) are counted as a consistency check.

## 5. Visualization
A ranked list, Wrapped style: the finals' top ten with their win counts, and the ratings' bottom five for contrast.

## 6. Evaluation
Jev's verdict (evaluator v3): **keep**, head-to-head strength 0.024, top verdict `portrait`.

## Compared with
nothing outside the model: a ranking of Jev's own ratings and choices

## Limits
A winner is only the best of what was on the list (BeerAdvocate (reviewed beers)). Finalists were chosen by Jev's own ratings, so an item it underrated never reached the final.

Results: `data/analysis/experiments/taste_top_beer.json` (private). Code: `scripts/experiments/`.
