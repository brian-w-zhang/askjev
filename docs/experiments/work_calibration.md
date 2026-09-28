# work_calibration

family: work

## 1. Question
When Jev is 90% sure of an answer to a work task, is it right 90% of the time, and does that depend on whether it answers yes/no or picks from options?

TypeSafe publishes no calibration numbers (docs/01-jev.md §6). A confidence you can take at face value is what lets a pipeline send only the unsure cases to a person.

## 2. Sourcing
Existing Machine questions with a right answer from public datasets: yes/no (Noul) and pick-one (Choice). Enough: ~275,000 questions.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's probability on its chosen answer, binned (50-60%, ..., 99%+); in each bin the share right. Overconfidence = mean confidence minus share right, per primitive, with 90% bootstrap intervals over questions. The share right when Jev is 95%+ sure, by primitive and by field.

## 5. Visualization
A reliability diagram: confidence (x) vs share right (y), one line for yes/no and one for pick-one, with the diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.3, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
Dataset labels have their own error, which caps the share right in the top bins. Fields differ in task mix.

Results: `data/analysis/experiments/work_calibration.json` (private). Code: `scripts/experiments/`.
