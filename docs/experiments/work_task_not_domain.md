# work_task_not_domain

family: work

## 1. Question
Across 120 kinds of machine work in 14 fields, does knowing the field (legal, code, healthcare...) tell you how often Jev gets it right, or does it depend on the specific task?

Buyers pick a model per field ('is it good at legal?'). If reliability swings more between tasks inside a field than between fields, that question is the wrong one, and every new task needs its own check.

## 2. Sourcing
Existing Machine-hemisphere questions from public labeled datasets with a right answer (Noul, Choice), grouped by the tree's field (level 1) and by source task. Authored TypeSafe-style questions are left out (their labels are the author's), and so are graded-scale tasks (work_grading_scales). Enough: ~270,000 questions, 120+ tasks.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per task, the share Jev gets right (its most likely answer equals the dataset's label). Per field, the pooled share with a 90% bootstrap interval over tasks, and the lowest and highest task in it. The share of the variance in task-level results that the field explains (between-field over total).

## 5. Visualization
One row per field: a dot at the pooled share, a line from its weakest to its strongest task, weakest and strongest named.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
each dataset's own labels (a right answer, not a crowd)

## Limits
A dataset's label is not always right, and harder datasets sit in some fields. Tasks differ in chance level (2 to 77 options). Indicators, not a ranking of fields.

Results: `data/analysis/experiments/work_task_not_domain.json` (private). Code: `scripts/experiments/`.
