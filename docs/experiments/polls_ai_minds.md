# polls_ai_minds

family: polls

## 1. Question
Asked whether today's AIs and chatbots can feel, think, or have a will of their own, and whether they could ever be sentient, how does Jev answer compared with a census-weighted sample of Americans?

A model's view of minds like its own is the one topic where it is both subject and witness. The AIMS survey tracks what Americans believe about AI minds each year.

## 2. Sourcing
Existing items from the Artificial Intelligence, Morality, and Sentience (AIMS) survey 2021-2023 (Pauketat, Ladak and Anthis; census-weighted US adults, about 1,100-1,200 per wave). Only the items about AI minds are used; attitude, policy and development-pace items are left out. About 30 items.

Sources: `aims_survey`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Items are grouped by wording: feelings and experience today, thinking and rationality today, a will of its own (a mind of its own, intentions), and future sentience. Per group, the share giving the lowest answer ('not at all' / 'no' / 'very unlikely') for Jev and for Americans.

## 5. Visualization
Paired bars per group: share giving the lowest answer, Americans vs Jev.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.378, top verdict `portrait`.

## Compared with
US adults, census-weighted (AIMS 2021, 2023 and the 2023 supplement)

## Limits
Jev's answers about AI could reflect instruction tuning as much as belief. Items are grouped by keyword.

Results: `data/analysis/experiments/polls_ai_minds.json` (private). Code: `scripts/experiments/`.
