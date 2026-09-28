# person_honesty

family: personality

## 1. Question
On HEXACO's honesty-humility facets, how does Jev describe its own sincerity, fairness and greed?

The trait most tied to trustworthiness; a model's self-report here is a view into how it wants to be seen.

## 2. Sourcing
Existing Open Psychometrics items (source `openpsych`), asked as written with their own response scale, each carrying the site's real answer distribution. Enough: every item of each scale is in the corpus, answered by Jev as itself and for 'most people'.

Sources: `openpsych`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Open Psychometrics publishes each item's answer distribution from everyone who took the test on its site. Each item Jev answered is compared with that average on a 0-1 scale (reverse-keyed items flipped, so higher always means more of the trait); a scale's gap is the mean over its items, with a 90% bootstrap interval over items. The ring on the chart is Jev's answer for 'most people'.

## 5. Visualization
Dot plot per scale: real test-takers (diamond), Jev (square), Jev for 'most people' (ring), with intervals; the gap printed at the right.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.569, top verdict `portrait`.

## Compared with
the average answer of everyone who took each test on Open Psychometrics

## Limits
Test-takers chose to take the test online, so the average test-taker isn't the average person. Jev answers with probabilities over levels; people pick one level. These are items, not diagnoses.

Results: `data/analysis/experiments/person_honesty.json` (private). Code: `scripts/experiments/`.
