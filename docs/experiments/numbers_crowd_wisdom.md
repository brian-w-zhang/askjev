# numbers_crowd_wisdom

family: numbers · new questions: 160

## 1. Question
How far is it from Houston to Atlanta, how many people live in Algeria, how many watts does a desktop computer draw? Is Jev closer than a typical person, and closer than the crowd's median?

The wisdom of crowds says the median of many guesses beats almost every individual. A model has read everyone's writing: is it a single guesser, or already a crowd?

## 2. Sourcing
New questions (sources/crowd_estimates): the 160 text-only numeric questions of Simoiu et al. 2019 (8 domains x 20, about 500 people each, February 2017, MIT license), asked as the study asked them, with fixed ordered bins per domain. Each person's answer is binned the same way.

Sources: `crowd_estimates`

## 3. Collection
160 new questions, each asked as written and with the bins in three shuffled orders (averaged).

## 4. Scoring
Per domain and overall: share where Jev's median bin holds the true answer, against the share of individual people whose answer lands in it (the typical person) and whether the crowd's median bin holds it; mean distance in bins from the truth for Jev and for the crowd's median.

## 5. Visualization
Paired bars per domain: typical person, crowd median and Jev, share in the right bin.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.609, top verdict `portrait`.

## Compared with
About 500 US online participants per question (Simoiu et al. 2019) and the study's answer key

## Limits
Bins are coarse, so 'right' means within a bin (about 20-50% wide). People answered in 2017; populations and GDP are pinned to 2016 in the wording.

Results: `data/analysis/experiments/numbers_crowd_wisdom.json` (private). Code: `scripts/experiments/`.
