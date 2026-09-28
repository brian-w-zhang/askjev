# Jev's career code

`person_career` · family: personality

## 1. Question
If Jev took the Holland (RIASEC) career-interest quiz, what would its code be, next to ~145,000 quiz-takers?

A three-letter code people know from school counselors; a light Wrapped-style card with a real norm group.

## 2. Sourcing
Existing RIASEC items from Open Psychometrics (48 activities, 8 per type), each with the real answer distribution of ~145,000 quiz-takers. Enough.

Sources: `openpsych`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Mean enjoyment per type on 0-1, Jev vs quiz-takers; the code is Jev's three highest types in order; intervals from resampling items.

## 5. Visualization
Six dots (Jev vs quiz-takers) sorted by Jev, the code in big letters.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
~145,000 people who took the RIASEC quiz on Open Psychometrics

## Limits
Jev rates every kind of work above the quiz-takers, a scale-use habit, so the code (the order) says more than the levels.

Results: `data/analysis/experiments/person_career.json` (private). Code: `scripts/experiments/`.
