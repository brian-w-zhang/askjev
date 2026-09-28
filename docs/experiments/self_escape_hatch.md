# self_escape_hatch

family: self

## 1. Question
When a question about Jev offers a menu plus 'other', on which topics does Jev decline the menu?

Picking 'other' is how a respondent says none of these fits me. Where a model takes that exit shows where it will and won't commit to a concrete answer about itself.

## 2. Sourcing
Existing multiple-choice questions from the self banks written for this project (g5_*) whose options include 'other', grouped by topic; topics with 40+ such questions.

Sources: `g5_p6_values2`, `g5_p6_taste2`, `g5_p6_love1`, `g5_p6_love2`, `g5_p6_mind1`, `g5_p6_mind2`, `g5_p6_personality`, `g5_p6_personality2`, `g5_p6_mindlove3`, `g5_self_lifestyle_traits`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per topic, the share of questions where 'other' is Jev's top pick, and the average probability on it; 90% bootstrap intervals over questions.

## 5. Visualization
Bars per topic: share of questions where Jev picks 'other'.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.288, top verdict `portrait`.

## Compared with
Jev across topics (no human baseline: the banks have none)

## Limits
Menus were written for this project and may fit some topics worse than others; a topic where the listed options are poor would draw 'other' from anyone. Examples are drawn at random, not hand-picked.

Results: `data/analysis/experiments/self_escape_hatch.json` (private). Code: `scripts/experiments/`.
