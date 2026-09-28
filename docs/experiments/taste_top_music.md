# Jev's favorite albums and sounds, ranked

`taste_top_music` · family: taste

## 1. Question
If Jev ranked every album or sound it was asked about, what would its top ten be?

Wrapped-style favorites, but from every item it rated rather than a handful of head-to-heads; the interesting part is what rises to the top and what sinks.

## 2. Sourcing
Existing one-at-a-time rating questions ("How much would you enjoy ...", five situation-described levels) under Self > Lifestyle > Ratings > music_ratings; items from lists written for this project (classic albums, everyday sounds). Enough: every item is rated, so the whole list can be ranked; the old head-to-heads (about 7 per item) are too thin to rank.

Sources: `g5_w13_ratings`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Each item's expected level (0-4) from Jev's probability over the five levels, averaged with the same question asked with the levels reversed; the gap between the two shows how much the order of the options matters. Ties are left as ties. The top 24 go to a head-to-head final (taste_finals).

## 5. Visualization
A ranked list, Wrapped style: the top ten with their level bars, and the bottom five for contrast.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
nothing outside the model: a ranking of Jev's own ratings

## Limits
A winner is only the best of what was on the list (lists written for this project (classic albums, everyday sounds)). Levels are Jev's probabilities over described situations, not a star rating.

Results: `data/analysis/experiments/taste_top_music.json` (private). Code: `scripts/experiments/`.
