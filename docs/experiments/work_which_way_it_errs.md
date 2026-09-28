# work_which_way_it_errs

family: work

## 1. Question
When Jev gets a yes/no work check wrong, does it err in one direction, and does the direction depend on what is being checked?

Knowing that a checker is 85% right is not enough to deploy it; knowing it waves through bad work, or cries wolf, tells you which side needs a second look.

## 2. Sourcing
Existing yes/no Machine questions from 46 public labeled datasets, sorted by hand into four kinds of question: is this work good enough, is every claim supported, are these two things a match, is something wrong here. Enough: ~90,000 questions.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per task, the lean: the share of items Jev passes (or, for 'is something wrong', flags) minus the share the labels pass (or flag). Positive = too many passes (or too many flags). Per kind, the mean lean over tasks with a 90% bootstrap interval over tasks.

## 5. Visualization
A dot plot, one row per task grouped under its kind, the lean around zero; the bad-case catch rate as a label on the extreme rows.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.298, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
The four kinds are a hand grouping. Some datasets are hard for people too (fake hotel reviews were near chance for human judges in the original study). Math checking is a documented limit (docs/01-jev.md §6), shown for completeness.

Results: `data/analysis/experiments/work_which_way_it_errs.json` (private). Code: `scripts/experiments/`.
