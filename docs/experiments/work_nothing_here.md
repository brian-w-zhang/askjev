# work_nothing_here

family: work

## 1. Question
When a menu of labels includes 'none of these' (the passage has no answer, the sentence states no relation), how often does Jev pick it when it's right, and how often when it isn't?

Extraction pipelines break when a model always finds something: an answer that isn't in the passage, a drug interaction the sentence never states. The 'nothing here' option is the guard.

## 2. Sourcing
Existing Choice questions whose options include a 'none' answer: SQuAD 2.0 (unanswerable questions), ChemProt relations, DDI drug interactions, unfair terms-of-service clause types, PII kinds. Enough: about 8,000 questions, about 2,300 whose answer is 'none'.

Sources: `squad2_spans`, `relation_extract`, `ddi_interactions`, `unfair_tos`, `pii_detect`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per set, the share of 'none' cases where Jev picks 'none', and the share of other cases where it wrongly picks 'none', with 90% intervals.

## 5. Visualization
Paired bars per set: 'none' when right vs 'none' when wrong.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.562, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
'None' means different things per dataset (no answer, no stated relation, no unfair type).

Results: `data/analysis/experiments/work_nothing_here.json` (private). Code: `scripts/experiments/`.
