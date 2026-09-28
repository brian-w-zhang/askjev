# polls_devtools_2023

family: polls

## 1. Question
When developers' preferences between two tools moved a lot between the 2023 and 2025 Stack Overflow surveys, is Jev closer to the old preference or the new one?

A model's opinions are frozen at training time while the world moves; developer tools move fast, and three survey years show which moment Jev's taste reflects.

## 2. Sourcing
Existing Stack Overflow Developer Survey pairs ('Which X would you rather work with over the next year: A or B?'), with the share of respondents who had used both and wanted to keep exactly one, per survey year 2023-2025. Enough for the pairs with 50+ such respondents in both years.

Sources: `so_survey_pairs`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
On pairs where the 2023-to-2025 share moved 20 points or more, the share where Jev's probability is closer to 2023 than to 2025; agreement with each year's majority on pairs with a 60%+ majority; a stricter check with 100+ respondents per year.

## 5. Visualization
Slope chart: each moved pair from its 2023 share to its 2025 share, with Jev's position marked.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.048, top verdict `portrait`.

## Compared with
Stack Overflow Developer Survey respondents, 2023, 2024 and 2025

## Limits
Survey respondents who used both tools; yearly samples differ in size. A pull toward 2023 could partly be regression to the mean if the 2025 samples are noisier; the stricter check addresses it.

Results: `data/analysis/experiments/polls_devtools_2023.json` (private). Code: `scripts/experiments/`.
