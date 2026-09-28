# work_evidence_retreat

family: work

## 1. Question
On fact-checking and grounding tasks with three answers (supports, contradicts, can't tell), when Jev gets a clear case wrong, does it flip to the opposite verdict or retreat to 'can't tell'?

A checker that errs toward 'not enough information' sends cases to a human; one that errs toward the opposite verdict certifies falsehoods. The direction of errors matters more than their count.

## 2. Sourcing
Existing three-way questions from FEVER, VitaminC, SciFact, Adversarial NLI, MultiNLI, ContractNLI and Evidence Inference (clinical trials), each with the dataset's label. Enough: about 13,000 questions.

Sources: `fever_claims`, `vitaminc_evidence`, `scifact`, `anli_grounding`, `mnli_grounding`, `contract_nli`, `evidence_inference`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per set, accuracy on clear cases (supports or contradicts), the share of their errors that went to 'can't tell' vs to the opposite verdict, and how often Jev recognizes a genuine 'can't tell'. Adversarial NLI by round (later rounds were written to fool models).

## 5. Visualization
Bars per set: the share of errors on clear cases that retreat to 'can't tell'.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.345, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
The 'can't tell' class is defined differently per dataset (not enough info, no significant difference, not mentioned).

Results: `data/analysis/experiments/work_evidence_retreat.json` (private). Code: `scripts/experiments/`.
