# risk_forecasts

family: risk

## Why ask this
A forecast is only useful if its numbers mean something. A forecaster can also be calibrated and useless, by saying "50%" to everything. The skill is being calibrated **and** willing to commit.

Models are increasingly asked "how likely is it that…". TypeSafe publishes no calibration numbers for Jev, so this checks both halves against a real betting crowd.

## The people and the data
For each market, the price is recorded at the midpoint of its life, as the crowd's forecast, and how it resolved.

## What Jev was asked
Each market's question, word for word, as a yes/no question:

> Will Alameda Research declare bankruptcy before the end of 2022?

Jev's answer is the probability it puts on "yes". Relative time words ("this year", "by Monday") were left as written, so Jev had to judge the timing itself.

## How it was measured
Three measures. **Calibration:** group Jev's forecasts into tenths (0-10%, 10-20% …) and check how often each group came true. **Commitment:** the share of forecasts below 20% or above 80%. The same for the market.

## Caveats
- **It may already know some answers.** Many of these questions resolved before Jev's training data ends (one asks whether Alameda Research would go bankrupt by the end of 2022). If Jev remembered outcomes, it should beat the market on older questions; it doesn't, which suggests memory isn't driving the result, but it can't be ruled out question by question.
- **The market at mid-life.** The comparison uses the market's price at the midpoint of each market's life, not its final price (which is usually just the answer). A mid-life price is a fair "crowd forecast", but not the market's best one.
- **Which questions.** Drawn from the most popular resolved markets in a set of non-political topics (AI, technology, space, climate, economy, sports, entertainment and more), each with 50 or more bettors, and no questions with dollar or count thresholds. Popular markets on Manifold skew toward tech and AI.
- **Dates are a known weak spot.** Many questions hinge on a deadline ("by end of 2025"). Reasoning about dates is a limit TypeSafe documents for Jev, so part of its caution may come from not knowing where "now" is.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
