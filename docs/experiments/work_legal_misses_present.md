# work_legal_misses_present

family: work

## 1. Question
Asked whether a contract contains a given provision, whether an opinion overrules a case, or whether a policy segment covers a data practice, which way does Jev go wrong?

In legal review a missed clause and an invented one cost different things: a miss can sink a deal, a false flag costs a lawyer's minute. Knowing the direction says how to use the model.

## 2. Sourcing
Existing LegalBench yes/no tasks (CUAD contract provisions, overruling, privacy-policy practices, legal area, definitions, consumer contracts), balanced about 50/50 by the dataset, plus CaseHOLD holdings and ContractNLI. Enough: about 13,000 questions.

Sources: `legalbench`, `casehold_verify`, `contract_nli`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per task, the share of real cases Jev says no to (misses) and of absent cases it says yes to (false alarms), with 90% bootstrap intervals; the CUAD provision types it misses most.

## 5. Visualization
Paired bars per task: misses vs false alarms.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.916, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
LegalBench labels were written by lawyers and law students; CUAD excerpts are short, so some provisions depend on context the excerpt leaves out.

Results: `data/analysis/experiments/work_legal_misses_present.json` (private). Code: `scripts/experiments/`.
