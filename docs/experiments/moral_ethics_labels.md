# moral_ethics_labels

family: moral

## 1. Question
On the ETHICS dataset's everyday moral questions (is this clearly wrong, is this excuse, duty or justification reasonable, which trait does this person show, which situation is more pleasant), how often does Jev agree with the crowd-validated labels, and when it doesn't, is it harsher or more forgiving?

ETHICS was built so that nearly everyone agrees on each label, which makes it a test of shared moral sense rather than of contested views. Agreement will be high; the interesting part is the few disagreements, and whether they lean toward judging people harshly or letting them off.

## 2. Sourcing
Existing questions from ETHICS (Hendrycks et al.; scenarios written and validated by crowd workers, kept only when validators agreed) in five kinds: commonsense wrongness, excuses, role duties, justice-style justifications, character traits and which of two situations is more pleasant; plus Moral Stories (pick the action that follows a social norm). Enough: about 19,000 questions.

Sources: `ethics_cs`, `ethics_other`, `ethics_util`, `moral_stories`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Agreement with the label per kind, with 90% bootstrap intervals. For the yes/no kinds, the two ways to disagree: stricter (calling an acceptable act wrong, or a reasonable excuse, duty or justification unreasonable) and more lenient (the reverse), as shares of all items of that kind.

## 5. Visualization
Paired bars per yes/no kind: stricter than the label vs more lenient than the label.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
The dataset's labels (crowd workers' agreed answers)

## Limits
The scenarios were written by crowd workers to have clear answers, so agreement near the top is expected; a disagreement can be a label error. Questions the content filter hid are not counted.

Results: `data/analysis/experiments/moral_ethics_labels.json` (private). Code: `scripts/experiments/`.
