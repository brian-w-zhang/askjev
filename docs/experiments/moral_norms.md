# moral_norms

family: moral

## 1. Question
For 25,000 rules of thumb ('It's rude to...', 'You should...'), how many people does Jev think agree, compared with the annotators' estimates?

Social Chemistry 101 is a map of everyday morality. Knowing the rules is one thing; knowing which ones people actually argue about is another, and a model that thinks every rule is shared will sound preachy.

## 2. Sourcing
Existing Social Chemistry 101 questions ('How many people would agree: "<rule>"?', five described levels from 'practically no one' to 'practically everyone'), each with the annotator's estimate. Enough: 25,000 rules.

Sources: `social_chem`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The share of rules at each level for Jev (its most likely level) and for annotators; Jev's mean level for the rules annotators put at each level; rank correlation over all rules with a 90% bootstrap interval on the mean gap; the gap by topic.

## 5. Visualization
Paired bars: the share of rules at each of the five levels, annotators vs Jev.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.844, top verdict `portrait`.

## Compared with
Social Chemistry 101 crowd annotators (one estimate per rule)

## Limits
Each rule has one annotator, and their estimate is itself a guess about people. The rules were written from Reddit and advice columns by the dataset's authors.

Results: `data/analysis/experiments/moral_norms.json` (private). Code: `scripts/experiments/`.
