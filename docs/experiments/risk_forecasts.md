# risk_forecasts

family: risk

## 1. Question
On 2,500 resolved Manifold prediction markets, how good are Jev's probabilities compared with the market's price at mid-life and with the actual outcome?

TypeSafe publishes no calibration numbers (docs/01-jev.md §6 lists calibration as open ground). Forecasting questions have real answers and a real crowd to beat, so they show both whether Jev's percentages mean what they say and how much it is willing to commit.

## 2. Sourcing
Existing Manifold questions (tech, AI, economy, science, sports and entertainment; no politics), each with the market probability just before its midpoint and the resolved outcome. Enough: 2,547.

Sources: `manifold`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Brier score (lower is better) for Jev, the market and a constant base-rate guess; calibration: the outcome rate in each tenth of stated probability; the share of forecasts above 80% or below 20%; 90% bootstrap intervals over questions.

## 5. Visualization
Calibration plot: stated probability (x) vs how often it happened (y), Jev and the market, with the diagonal; dot size by count.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.445, top verdict `portrait`.

## Compared with
Manifold market prices at each market's mid-life; the resolved outcomes

## Limits
Some questions resolved before Jev's training data ends, so it may know the answer; the per-year Brier scores are shown for that reason. Mid-life prices are not the market's best forecast. Questions about dates lean on a documented weak spot (docs/01-jev.md §6, item 3).

Results: `data/analysis/experiments/risk_forecasts.json` (private). Code: `scripts/experiments/`.
