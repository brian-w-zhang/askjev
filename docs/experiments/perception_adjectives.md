# perception_adjectives

family: perception · new questions: 749

## 1. Question
Given two adjectives from the same scale ('warm' and 'hot', 'big' and 'vast'), does Jev pick the stronger one the way linguists and crowd workers ordered them?

Intensity is how people grade things in words, and it is subtle: 'dim' vs 'dark', 'content' vs 'pleased'. A model that gets the order wrong will misread reviews, feedback and hedges.

## 2. Sourcing
New questions (sources/scalar_adjectives): 'Which word expresses a stronger degree of the same quality: "<a>" or "<b>"?' for every pair of differently ranked words in three gold sets: de Melo & Bansal 2013 (linguists), Wilkinson & Oates 2016, and Cocos et al. 2018 (crowd). 749 pairs.

Sources: `scalar_adjectives`

## 3. Collection
749 new questions, each asked in both orders (averaged).

## 4. Scoring
Share where Jev's pick matches the gold order, by set and by how far apart the words sit on their scale (neighbors vs two or more steps); the scales where it errs most.

## 5. Visualization
Bars: agreement by gold set and by distance on the scale, with 90% intervals.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Three published gold orderings (linguists and crowd workers)

## Limits
Gold orderings disagree with each other on some scales; a 'miss' can be a defensible order.

Results: `data/analysis/experiments/perception_adjectives.json` (private). Code: `scripts/experiments/`.
