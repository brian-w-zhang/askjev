# taste_intransitive

family: taste

## 1. Question
When Jev's 24 favorite films (or books, foods, places...) play every other one head to head, are its choices consistent, or does it prefer A to B, B to C, and C to A?

A ranking only means something if preferences are transitive. People are mostly transitive on things they care about; a model whose picks loop can still crown a 'favorite', but the crown is an accident of which pairs were asked.

## 2. Sourcing
The taste finals (sources/taste_finals): 276 head-to-heads among the top 24 of each of 12 domains, 3,281 shown, each asked in both option orders.

Sources: `taste_finals`

## 3. Collection
Uses the taste finals' new questions (no further calls).

## 4. Scoring
Per domain, every triple of finalists is a triad; it is intransitive when the majority choices form a cycle. A random tournament has 25% intransitive triads, a perfectly consistent one 0%. Also: how decisive each pick is (distance of Jev's probability from 50%), how often the pick survives reversing the order, and the triads whose three picks are all decisive (70/30 or firmer).

## 5. Visualization
Bars per domain: share of intransitive triads, with the 25% random line and the decisive-only share.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
a random tournament (25%) and a perfectly transitive chooser (0%)

## Limits
Finalists are near the top of Jev's own ratings, so many pairs are close calls; the decisive-only count addresses that.

Results: `data/analysis/experiments/taste_intransitive.json` (private). Code: `scripts/experiments/`.
