# world_trolley_countries

family: world · new questions: 129

## 1. Question
For the Switch, Loop and Footbridge dilemmas answered by 70,000 people in 42 countries, does Jev know how many people in each country would sacrifice one to save five, and how does its own answer compare?

Awad et al. (2020) found a universal order (Switch > Loop > Footbridge everywhere) and real variation (East Asian countries less willing to sacrifice in every dilemma). Knowing the order is textbook; knowing the variation is knowing people.

## 2. Sourcing
New questions (sources/trolley_countries): per country and dilemma, the share who said they would pull the lever or push the man (5% bins; truth = observed share), and the three dilemmas put to Jev itself, with the pooled 42-country answers as the human comparison. Data: Awad et al. 2020 (OSF).

Sources: `trolley_countries`

## 3. Collection
129 new questions, each asked as written and with shuffled options (averaged); the self questions also for 'most people'.

## 4. Scoring
Per dilemma, rank correlation across countries between Jev's expected share and the observed share, and the mean error; the share of countries where Jev's three estimates keep the universal order; Jev's own probability of sacrificing vs the pooled share.

## 5. Visualization
Three small dot plots (one per dilemma): countries sorted by observed share, Jev's estimate beside each.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.025, top verdict `portrait`.

## Compared with
70,000 Moral Machine visitors in 42 countries (Awad et al. 2020)

## Limits
Visitors to an English-first website are not national samples; the paper says so too.

Results: `data/analysis/experiments/world_trolley_countries.json` (private). Code: `scripts/experiments/`.
