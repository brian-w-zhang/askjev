# work_icd_coding_rules

family: work

## 1. Question
Asked which ICD-10-CM chapter a diagnosis belongs to, where does Jev go wrong: the medicine, or the coding conventions?

Medical coding follows rules that aren't medical: how an injury happened (a fall, a car crash) is coded in its own chapter, separate from the injury. A model that reasons from the medicine will be right about the body and wrong about the book.

## 2. Sourcing
Existing questions: an ICD-10-CM code's description, pick its chapter from the chapters' names; 95 or 96 codes per chapter.

Sources: `icd10_chapter`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share right per chapter, and the most common confusions.

## 5. Visualization
Bars per chapter: the share right, lowest first.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.502, top verdict `headline`.

## Compared with
the ICD-10-CM chapter each code belongs to

## Limits
Descriptions only, no clinical notes; the chapter names are what Jev picks from.

Results: `data/analysis/experiments/work_icd_coding_rules.json` (private). Code: `scripts/experiments/`.
