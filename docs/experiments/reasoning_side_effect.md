# reasoning_side_effect

family: reasoning · new questions: 12

## 1. Question
When a boss doesn't care about a side effect, does Jev call a harmful side effect intentional and a helpful one not, like people do, even in stories it has never seen?

Knobe's chairman (82% say he harmed the environment intentionally, 23% that he helped it intentionally) is one of the most replicated results in experimental philosophy, and Jev overdoes it on the original (judgment_classics). New stories test whether that is the famous vignette or a general habit.

## 2. Sourcing
New questions (sources/philosophy_vignettes, family side_effect): six help/harm pairs written for this project in the chairman's exact structure (a development company, a restaurant chain, a factory, a band, a software company, a delivery company).

Sources: `philosophy_vignettes`

## 3. Collection
12 new questions, each asked as written, for 'most people', and with yes/no swapped (averaged).

## 4. Scoring
Per pair, Jev's probability of 'intentionally' for the harm minus the help version; the mean over pairs with a 90% interval by pair; people's published gap on the original is 82% - 23% = 59 points.

## 5. Visualization
A dumbbell per story: help vs harm probability of 'intentionally'.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Knobe 2003's chairman (82% vs 23%); Jev's own answer on the Many Labs 2 chairman (judgment_classics)

## Limits
Four of the six pairs are shown (the screen hid two), so n = 4 stories. The new stories have no human data; people's gap on the original is the reference.

Results: `data/analysis/experiments/reasoning_side_effect.json` (private). Code: `scripts/experiments/`.
