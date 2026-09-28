# perception_adjectives

family: perception · new questions: 1498

## 1. Question
Given two adjectives from the same scale ('warm' and 'hot', 'big' and 'vast'), does Jev pick the stronger one the way linguists and crowd workers ordered them?

Intensity is how people grade things in words, and it is subtle: 'dim' vs 'dark', 'content' vs 'pleased'. A model that gets the order wrong will misread reviews, feedback and hedges.

## 2. Sourcing
New questions (sources/scalar_adjectives): 'Which word expresses a stronger degree of the same quality: "<a>" or "<b>"?' for every pair of differently ranked words in three gold sets: de Melo & Bansal 2013 (linguists), Wilkinson & Oates 2016, and Cocos et al. 2018 (crowd). 749 pairs.

Sources: `scalar_adjectives`

## 3. Collection
1,498 new questions: each pair with the two words in both orders in the question text, each also asked with the options shuffled (all averaged).

## 4. Scoring
Per pair, Jev's probability for the stronger word averaged over both word orders; share of pairs where that is above one half, by set and by how far apart the words sit on their scale; the same share per word order, to show how much naming a word first helps it; the scales where it errs most.

## 5. Visualization
Bars: agreement by gold set and by distance on the scale, with 90% intervals.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.08, top verdict `portrait`.

## Compared with
Three published gold orderings (linguists and crowd workers)

## Limits
Gold orderings disagree with each other on some scales; a 'miss' can be a defensible order.

Results: `data/analysis/experiments/perception_adjectives.json` (private). Code: `scripts/experiments/`.
