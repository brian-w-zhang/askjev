# work_knows_hard_cases

family: work

## 1. Question
On work cases written to be deliberately borderline, does Jev's confidence drop, or is it as sure as on the clear ones?

A model that knows when a case is hard can hand exactly those to a person. Public datasets don't mark which cases are borderline; the questions written for this project in TypeSafe's style do.

## 2. Sourcing
Existing authored questions for TypeSafe's Machine leaves with no public data (claims triage, KYC, ad alignment, listing compliance, moderation enforcement, response verification, prohibited claims, methods checks, hiring evidence, purchase intent): 7,450 inputs written by hand, about 30% marked borderline at writing time. Plus the examples in TypeSafe's own docs, and public data for contrast. Enough.

Sources: `typesafe_authored`, `typesafe_seeds`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share right and share of answers at 95%+ confidence for clear vs borderline cases, per primitive, with 90% bootstrap intervals; the same for the docs' own examples and for public datasets.

## 5. Visualization
Paired bars: share right and share 95%+ sure, for docs examples, clear authored, borderline authored and public data.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.729, top verdict `portrait`.

## Compared with
the author's labels (authored), the docs' answers, and public datasets' labels

## Limits
Authored labels are the author's judgment, not independent ground truth, and the author knew which cases were borderline. The docs examples are few (a few hundred).

Results: `data/analysis/experiments/work_knows_hard_cases.json` (private). Code: `scripts/experiments/`.
