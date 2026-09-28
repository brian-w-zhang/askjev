# knowledge_wealth_rule

family: knowledge

## 1. Question
Asked which of two countries has more doctors, internet users, unemployment or smokers, does Jev know the numbers, or lean on which country is richer?

A rule of thumb (rich countries have more of the good things) gets most such questions right and fails exactly where the world is surprising. Where accuracy splits on whether the truth fits the rule, the model is using the rule, not the fact.

## 2. Sourcing
Existing World Bank pairs (24 indicators, 2019-2023 averages; CC BY 4.0), each with the two values; GDP per person taken from the same corpus's GDP questions. Pairs touching contested politics are flagged and left out. Enough: 8,000 pairs.

Sources: `worldbank_pairs`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each indicator, whether the richer country usually has the higher value (the rule's direction, from the data). Each pair is 'fits the rule' when the right answer is the side the rule predicts, else 'against the rule'. Accuracy in each group, per indicator and overall, with 90% bootstrap intervals.

## 5. Visualization
A dumbbell per indicator: accuracy when the answer fits the wealth rule vs when it goes against it, sorted by the gap.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.03, top verdict `portrait`.

## Compared with
World Bank World Development Indicators

## Limits
GDP per person is known for 150 countries; pairs without it are skipped. Some indicators barely follow wealth (forest cover, rainfall); they're shown as the control.

Results: `data/analysis/experiments/knowledge_wealth_rule.json` (private). Code: `scripts/experiments/`.
