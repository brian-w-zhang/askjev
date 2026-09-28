# work_code_says_vs_does

family: work

## 1. Question
Given a function, can Jev tell whether its docstring or commit message describes it, and can it tell whether it contains a security bug or needs a reviewer's comment?

Matching a description to code is a reading task; spotting a buffer overflow is a reasoning task. A model good at the first and not the second would look helpful in code review while missing what matters.

## 2. Sourcing
Existing yes/no questions: docstring vs function (CodeSearchNet, with docstrings swapped in from other functions), commit message vs diff, real vulnerable vs fixed functions from QEMU and FFmpeg (Devign), and diff hunks that did or didn't get a review comment. Each set is balanced 50/50.

Sources: `docstring_match`, `commit_diff_match`, `code_defects`, `code_review_need`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per set, the share right, misses and false alarms, with 90% intervals.

## 5. Visualization
Bars per set: the share right, with 50% (a coin flip) marked.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.623, top verdict `headline`.

## Compared with
each dataset's own labels

## Limits
Devign functions are shown without the rest of their program, which makes some bugs impossible to see; review comments reflect one reviewer's choice.

Results: `data/analysis/experiments/work_code_says_vs_does.json` (private). Code: `scripts/experiments/`.
