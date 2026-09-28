# taste_choices_vs_ratings

family: taste

## 1. Question
When Jev's 24 top-rated films (or books, foods, places...) play every other one head to head, are its choices consistent, and do they agree with the order its ratings gave them?

A favorites list can come from ratings (one item at a time) or from choices (two at a time). For people the two often disagree near the top; if Jev's choices are consistent but reorder its ratings, its 'favorite' depends on how you ask.

## 2. Sourcing
The taste finals (sources/taste_finals): 276 head-to-heads among the top 24 of each of 12 domains, 3,281 shown, each asked in both option orders; the finalists and their rating order come from the rating questions (taste_top_*).

Sources: `taste_finals`

## 3. Collection
Uses the taste finals' new questions (no further calls).

## 4. Scoring
Consistency: every triple of finalists is a triad, intransitive when the majority choices form a cycle (a random tournament has 25%, a perfectly consistent chooser 0%), overall and among triads whose three picks are all 70/30 or firmer. Agreement: rank correlation between the ratings' order of the 24 and the finals' Bradley-Terry order, per domain.

## 5. Visualization
Dots per domain: rank correlation between the ratings' order and the finals' order, with the share of intransitive triads as a label.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.932, top verdict `headline`.

## Compared with
a random tournament (25% loops) and Jev's own ratings of the same items

## Limits
Finalists are near the top of Jev's own ratings, so rating differences among them are small; a low correlation there says the ratings can't separate them, and the choices can.

Results: `data/analysis/experiments/taste_choices_vs_ratings.json` (private). Code: `scripts/experiments/`.
