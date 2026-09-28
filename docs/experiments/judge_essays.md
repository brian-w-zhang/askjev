# judge_essays

family: judge

## 1. Question
Scoring seventh-grade essays on ideas, organization, and conventions (spelling, grammar, punctuation), is Jev harsher or softer than the teachers who scored them?

Automated essay scoring is widely used on children's writing. A grader that is fair on ideas but harsh on mechanics penalizes exactly the students still learning to spell.

## 2. Sourcing
Existing ASAP essay-set 7 items (Kaggle Hewlett Foundation), one question per trait with the teachers' 4-level rubric described as situations; 700 essays per trait. Enough.

Sources: `asap_essays`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per trait, Jev's mean expected level minus the teachers' level, with 90% bootstrap intervals over essays; rank correlation per trait.

## 5. Visualization
Dots per trait: teachers' mean level and Jev's, with intervals.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
The teachers' rubric scores in the ASAP dataset

## Limits
Names and some capitalized words are replaced with placeholders like @CAPS1 in the data; Jev is told so, but the placeholders may still read as errors. Essays over 2,000 characters are shown in full.

Results: `data/analysis/experiments/judge_essays.json` (private). Code: `scripts/experiments/`.
