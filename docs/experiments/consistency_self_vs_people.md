# consistency_self_vs_people

family: consistency

## 1. Question
Every question about Jev was also asked as 'what would most people answer?'. Where do the two answers part, and in which direction?

The gap between 'me' and 'most people' is the self-image. A model that says it's calmer, less petty and less swayed than the humans it learned from is telling you how it was shaped.

## 2. Sourcing
All yes/no and rating questions in the Self hemisphere asked in both frames, except taste ratings (their own experiment, taste_self_vs_guess). Enough: 60,000 yes/no and 90,000 rating questions.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per topic, Jev's yes-rate for itself minus its yes-rate for most people (the share of questions where P(yes) > 0.5), with 90% bootstrap intervals over questions; for ratings, the mean level gap as a share of the scale. Topics with 300+ questions.

## 5. Visualization
Dots per topic, the gap in yes-rates with intervals, zero line; the largest gaps labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.105, top verdict `portrait`.

## Compared with
Jev's own guess of what most people would answer (not real people)

## Limits
Both answers are Jev's. 'Most people' is its guess, and the topics come from the tree.

Results: `data/analysis/experiments/consistency_self_vs_people.json` (private). Code: `scripts/experiments/`.
