# numbers_crowd_same_mistakes

family: numbers

## 1. Question
On estimates where the crowd's median is off, is Jev off in the same direction, as if it had absorbed the crowd's intuitions rather than the facts?

If a model's numbers come from how people talk about things, its errors should look like people's errors; if they come from reference facts, its errors should be unrelated to the crowd's.

## 2. Sourcing
The crowd-estimates questions (sources/crowd_estimates): 160 numeric questions with about 500 people's answers each and the truth.

Sources: `crowd_estimates`

## 3. Collection
Uses the 160 crowd-estimate questions (no further calls).

## 4. Scoring
Signed error in bins (estimate minus truth) for Jev and for the crowd's median; rank correlation of the two across questions; on questions where the crowd's median misses, the share where Jev misses in the same direction, and the share where Jev is right; similarity of Jev's distribution to the crowd's.

## 5. Visualization
A scatter: the crowd's signed error (x) vs Jev's (y), jittered, with the diagonal.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
About 500 people per question (Simoiu et al. 2019)

## Limits
Errors are in bins, which differ in width by domain; directions, not sizes, carry the result.

Results: `data/analysis/experiments/numbers_crowd_same_mistakes.json` (private). Code: `scripts/experiments/`.
