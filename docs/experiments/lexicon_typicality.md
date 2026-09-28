# lexicon_typicality

family: lexicon · new questions: 350

## 1. Question
How good an example of its category does Jev find each member (a penguin of a bird, a tuba of a wind instrument, boredom of an emotion), compared with people's ratings?

Typicality is how people's categories are shaped: some members are central, some marginal. A model that treats every member as equally good, or ranks them differently, reasons about categories differently.

## 2. Sourcing
New questions (sources/category_norms): 'How good an example of a bird is a penguin?' on five described levels (very poor to very good example, the study's endpoints) for 350 members sampled evenly over the range of UK adults' mean ratings (Banks, Wingfield & Connell 2023; at least 12 raters per item, means only).

Sources: `category_norms`

## 3. Collection
350 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Rank correlation between Jev's expected level and people's mean, with a 90% bootstrap interval, overall and for concrete vs abstract categories; the members it rates much higher or lower than people.

## 5. Visualization
A scatter: people's mean rating (x, 1-5) vs Jev's level (y, 0-4), with the largest disagreements labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.697, top verdict `portrait`.

## Compared with
UK adults on Prolific (Banks, Wingfield & Connell 2023)

## Limits
Only means are published, so ranks are compared, not distributions. The level descriptions are this project's, anchored on the study's endpoints.

Results: `data/analysis/experiments/lexicon_typicality.json` (private). Code: `scripts/experiments/`.
