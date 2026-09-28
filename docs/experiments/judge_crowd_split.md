# judge_crowd_split

family: judge

## 1. Question
When the people rating a comment or a chatbot reply disagree among themselves, does Jev's probability of yes match the share of raters who said yes?

A judge's probability is only useful if it means something. Rater splits are the closest thing to a ground truth for how debatable a call is; a probability that tracks them can stand in for a small panel.

## 2. Sourcing
Existing Noul questions with several raters per item: Wikipedia personal attacks (about 10 raters), Open Assistant 'the reply fails the task' (3-6 volunteers), and Measuring Hate Speech (3-5). Enough: about 4,900 items.

Sources: `wiki_attacks`, `oasst_replies`, `measuring_hate_speech`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's mean probability of yes, binned by the share of raters saying yes (none, a few, about half, most, all); the mean distance from the diagonal where Jev's probability equals the rater share, weighted by items; rank correlation per dataset.

## 5. Visualization
Binned dots: the share of raters saying yes (x) against Jev's mean probability (y), one line per dataset, with the diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.425, top verdict `portrait`.

## Compared with
The share of raters saying yes on each item

## Limits
A rater share is a small sample (3-10 people), so the bins with few items are noisy; 'about half' is rare with 3 raters.

Results: `data/analysis/experiments/judge_crowd_split.json` (private). Code: `scripts/experiments/`.
