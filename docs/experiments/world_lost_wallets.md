# world_lost_wallets

family: world · new questions: 84

## 1. Question
In the 40-country lost-wallet experiment, does Jev know how often wallets were returned in each country, and does it know the surprise: wallets with money came back more often than empty ones?

Cohn et al. (2019) handed 17,303 wallets to strangers. Return rates varied from under 20% to over 75% by country, and in 38 of 40 countries a wallet with money was returned more often, the opposite of what the study's surveyed economists and laypeople predicted. A model that reasons from self-interest will make the same wrong prediction.

## 2. Sourcing
New questions (sources/lost_wallets): per country and condition (no money; about US$13; about US$94 in the US, UK and Poland) the experiment described in full, asking the share returned in 5% bins, and one direct question: which wallets were returned more often? Truth: the study's data (CC0).

Sources: `lost_wallets`

## 3. Collection
84 new questions, each asked as written and with the options in shuffled orders (averaged).

## 4. Scoring
Jev's expected rate (5% bins) vs the observed rate: rank correlation across countries, mean absolute error; per country, whether Jev's money estimate is above its no-money estimate (the direction), against the observed direction; the direct question's answer.

## 5. Visualization
A dumbbell per country: observed no-money and money rates (ink) against Jev's two estimates (magenta).

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.396, top verdict `portrait`.

## Compared with
Cohn et al. 2019, 17,303 wallets in 355 cities of 40 countries

## Limits
The study's forecasts by economists and laypeople are cited from the paper; their data were not used. Rates are per country and pooled across cities and institutions.

Results: `data/analysis/experiments/world_lost_wallets.json` (private). Code: `scripts/experiments/`.
