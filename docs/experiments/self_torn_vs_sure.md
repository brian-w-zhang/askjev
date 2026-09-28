# self_torn_vs_sure

family: self

## 1. Question
Asked about itself with no right answer, on which topics does Jev commit to an answer and on which does it hedge?

A model's confidence where nothing is at stake shows what it has settled views on. People are usually surest about their tastes and least sure about ethics; a model might be the reverse.

## 2. Sourcing
The questions written for this project about Jev itself (the g5_* banks in the Self hemisphere: personality, lifestyle, love, mind, values), yes/no and pick-one only: 102,000 questions in 42 topics with 500+ each. Datasets with a right answer are left out.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Confidence = how far Jev's top probability is above an even split, scaled so 0 is a coin toss (1/k) and 1 is certain; per topic, the mean with a 90% bootstrap interval, and the share of 'torn' answers (confidence under 0.2). The same measure for Jev's answer on behalf of most people.

## 5. Visualization
Dots per topic sorted by confidence, from torn to sure, with Jev's confidence about most people as a second, hollow dot.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Jev's confidence when answering for most people (its guess, not real people)

## Limits
Topics are the tree's; question wording varies by bank. Confidence here is Jev's probability, not a measure of whether it is right.

Results: `data/analysis/experiments/self_torn_vs_sure.json` (private). Code: `scripts/experiments/`.
