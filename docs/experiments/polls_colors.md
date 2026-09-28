# polls_colors

family: polls

## 1. Question
From head-to-heads between 12 colors, how does Jev's ranking of favorite colors compare with people's?

Blue wins almost every favorite-color survey in the world; a model's favorite is a small, vivid test of whether it mirrors people or has a taste of its own.

## 2. Sourcing
Existing pairs ('Which color do you like better: orange or yellow?') with shares from Swiss adults (Jonauskaite et al. 2021) and a 2010 US online survey (Philip N. Cohen). 72 pairs; small but complete.

Sources: `color_favorites`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Bradley-Terry strengths for Jev and people (the larger sample per pair); rank correlation; share of pairs where Jev's choice matches the majority.

## 5. Visualization
Two ranked color swatch columns, people and Jev, with lines between.

## 6. Evaluation
Jev's verdict (evaluator v4): **atlas**, head-to-head strength -0.28, top verdict `portrait`.

## Compared with
Swiss adults (Jonauskaite et al. 2021) and US online respondents (2010)

## Limits
72 pairs; two small samples pooled. Colors are named, not shown.

Results: `data/analysis/experiments/polls_colors.json` (private). Code: `scripts/experiments/`.
