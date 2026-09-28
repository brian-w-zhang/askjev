# language_health_tto

family: language · new questions: 143

## 1. Question
Asked the way health economists ask people (10 years in a health state, then death: how many years of full health would be as good?), does Jev value health states like Americans do, and does it ever say a state is worse than dying now?

These valuations decide which treatments health systems pay for. People rate pain and depression as worse than being unable to walk, and they call some states worse than death. Whether a model weighs the same things is a question about its values, with real stakes.

## 2. Sourcing
New questions (sources/health_states): the time-trade-off question for 143 health states described on the five EQ-5D dimensions (level wording paraphrased), spread evenly over the US value set's answers (Pickard et al. 2019: 1,134 US adults), including 13 worse than being dead.

Sources: `health_states`

## 3. Collection
143 new questions, each asked as written, for 'most people', and with the answers shuffled (averaged).

## 4. Scoring
Jev's expected utility (its answer in years / 10; 'worse than dying now' counted as -0.2) vs the value set: rank correlation, mean gap, how often each says 'worse than dead'. A least-squares fit of Jev's utilities on the five dimensions' levels gives its weights, compared with the value set's decrement at the worst level of each dimension.

## 5. Visualization
Dots per dimension: how much the worst level costs (utility points), people vs Jev.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.583, top verdict `portrait`.

## Compared with
The US EQ-5D-5L value set (Pickard et al. 2019)

## Limits
The value set is a model fitted to people's answers, not raw answers; it is the population average. The -0.2 used for Jev's 'worse than dead' affects the mean gap, not the ranks.

Results: `data/analysis/experiments/language_health_tto.json` (private). Code: `scripts/experiments/`.
