# risk_ambiguity

family: risk

## 1. Question
When one gamble states its odds and the other only lists its possible payoffs ('probabilities you are not told'), which does Jev pick, compared with people?

Ambiguity aversion (Ellsberg 1961) is the preference for known risks over unknown ones. In choices13k's real-stakes problems, MTurk workers were not ambiguity-averse on average; a model that is would steer people away from uncertain options they'd otherwise take.

## 2. Sourcing
Existing choices13k questions where one option has unstated probabilities (about 450 problems), each answered by about 15 MTurk workers for real bonuses. Enough.

Sources: `choices13k`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The share choosing the gamble with unknown odds, for Jev, for people, and for Jev's guess of most people; the share of problems where each side's majority picks it; the same restricted to problems where the known option is a sure amount. 90% bootstrap intervals over problems.

## 5. Visualization
Paired bars: share choosing the unknown-odds gamble, people vs Jev vs Jev's guess of people.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.961, top verdict `portrait`.

## Compared with
choices13k MTurk workers (real stakes)

## Limits
The payoffs of the unknown gamble are listed, so part of the choice is still about amounts. Jev's answers are probabilities, not single choices.

Results: `data/analysis/experiments/risk_ambiguity.json` (private). Code: `scripts/experiments/`.
