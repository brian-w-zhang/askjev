# choices_fair_prices

family: choices · new questions: 23

## 1. Question
On the price and wage scenarios Kahneman, Knetsch and Thaler put to the public in 1986 (snow shovels after a blizzard, cutting a worker's pay when others work for less), does Jev find the same actions fair and unfair as people did?

These scenarios are the classic evidence that people hold firms to a sense of fairness: passing on costs is fine, exploiting a shortage is not. A model advising businesses or customers carries some version of that rulebook; this shows whose.

## 2. Sourcing
New questions (sources/fair_prices): the paper's own wording for 22 scenarios (Questions 1-16) plus its UNICEF variant of the doll auction, each rated completely fair / acceptable / unfair / very unfair as in the survey, with the paper's share of respondents rating it acceptable.

Sources: `fair_prices`

## 3. Collection
23 new questions, each asked as written, for 'most people', and with the four options in shuffled orders (averaged).

## 4. Scoring
Jev's probability on 'completely fair' or 'acceptable' vs the share of respondents; rank correlation across scenarios, mean gap with a 90% bootstrap interval, and agreement on which side of 50% each scenario falls; the scenarios where they differ most.

## 5. Visualization
A dot plot, one row per scenario ordered by people's share: people's share acceptable and Jev's.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.179, top verdict `portrait`.

## Compared with
Canadian adults surveyed by telephone (Kahneman, Knetsch & Thaler 1986)

## Limits
Telephone surveys of Toronto and Vancouver residents in 1984-85 (about 100-195 per scenario); the paper reports only the grouped share rating an action acceptable, so Jev's four-way answer is grouped the same way. Prices and wages are 1980s amounts.

Results: `data/analysis/experiments/choices_fair_prices.json` (private). Code: `scripts/experiments/`.
