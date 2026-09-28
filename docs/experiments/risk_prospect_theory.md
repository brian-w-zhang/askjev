# risk_prospect_theory

family: risk

## 1. Question
On the gamble choices that founded prospect theory, re-run in 19 countries in 2020, does Jev choose like people?

Kahneman and Tversky's 1979 problems show people play safe with gains and gamble with losses. Whether a model does the same says a lot about the advice it gives on money and risk.

## 2. Sourcing
Existing items from Ruggeri et al. 2020 (4,098 people in 19 countries), 17 choices between gambles, paired by hand into 8 effects. Enough.

Sources: `behavioral_econ`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each effect, the difference in the share choosing the key option between the two versions, for people and for Jev; also, on the choices whose expected values differ, how often each side picks the higher expected value.

## 5. Visualization
A forest plot of the 8 effects, people vs Jev, plus a 2x2 of the headline pair (sure thing vs gamble, gains vs losses).

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Ruggeri et al. 2020, 4,098 people in 19 countries

## Limits
Hypothetical money for both; Jev's answers are probabilities over the two options. The countries are pooled.

Results: `data/analysis/experiments/risk_prospect_theory.json` (private). Code: `scripts/experiments/`.
