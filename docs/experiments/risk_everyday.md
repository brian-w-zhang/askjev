# risk_everyday

family: risk

## 1. Question
Asked how likely it would be to do 110 risky things (bungee jumping, shoplifting, betting a week's income, speaking up for an unpopular cause), does Jev order them like adults do?

Risk-taking isn't one trait: people who'd skydive may never gamble. The DOSPERT scale splits it into ethical, financial, health, recreational and social risks, so the profile says what kind of risk-taker Jev plays.

## 2. Sourcing
Existing Basel-Berlin Risk Study items (DOSPERT, five described likelihood levels), each with the answers of about 1,500 adults in Basel and Berlin. Enough: 110 activities in five domains.

Sources: `bbrs_risk`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's expected level (0-4) per activity vs the adults' mean level; rank correlation over activities; per domain, the mean gap with a 90% bootstrap interval over activities; the activities with the largest gap each way.

## 5. Visualization
Paired dots per domain (adults vs Jev), with the three largest single-activity gaps labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.122, top verdict `portrait`.

## Compared with
Basel-Berlin Risk Study adults (about 1,500, German-language questionnaire)

## Limits
Jev can't do any of these; the answer is the risk-taker it describes itself as. Adults are Swiss and German.

Results: `data/analysis/experiments/risk_everyday.json` (private). Code: `scripts/experiments/`.
