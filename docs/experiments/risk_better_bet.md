# risk_better_bet

family: risk

## 1. Question
Choosing between two gambles, how strongly does Jev lean toward the one that pays more on average, compared with people choosing for real money?

A model could be a cold expected-value maximizer or a coin flipper. Human choices sit in between: people follow a better bet more the bigger its edge. Whether Jev draws the same curve says whether its sense of risk is human-shaped.

## 2. Sourcing
Existing choices13k questions (Peterson et al. 2021, Science): about 1,900 two-gamble problems with stated odds, each answered by about 15 US MTurk workers playing for real bonuses. Wulff et al.'s meta-analysis of described gambles (about 460 problems) as a second population. Problems with unstated odds are left to risk_ambiguity. Enough.

Sources: `choices13k`, `wulff_description`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each problem, the expected-value edge of the better gamble as a share of the largest payoff; the share choosing the better gamble, binned by edge, for Jev and for people; the rank correlation of the choice shares over problems; the share of problems where each side's majority picks the better gamble.

## 5. Visualization
Two lines over the edge bins: share choosing the better gamble, people vs Jev, with the 50% line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.971, top verdict `portrait`.

## Compared with
choices13k MTurk workers (real stakes); participants in Wulff et al. 2018's described-gamble studies

## Limits
Jev's answers are probabilities over two options, not a single real choice. Reading payoffs and percentages leans on numbers, a weak spot TypeSafe documents for Jev (docs/01-jev.md §6, item 2), so this is labeled known territory.

Results: `data/analysis/experiments/risk_better_bet.json` (private). Code: `scripts/experiments/`.
