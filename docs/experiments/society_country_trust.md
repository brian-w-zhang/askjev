# society_country_trust

family: society · new questions: 109

## 1. Question
For each of about 100 countries, what share of people say most people can be trusted in its latest World Values Survey or European Values Study, and does Jev know?

Trust in strangers ranges from under 5% to over 70% of people, and it predicts a great deal about a country. A model's picture of it shows whether it knows the world or projects one country onto all of them.

## 2. Sourcing
New questions (sources/country_values): 'In the <year> World Values Survey or European Values Study in <country>, what share of people ...?', 21 bins (0-100% by 5), for every country with a survey since 2010; the answer is the published share (Integrated Values Surveys, via Our World in Data).

Sources: `country_values`

## 3. Collection
109 new questions, each asked as written and with the bins in three shuffled orders (averaged).

## 4. Scoring
Jev's median share vs the published share: mean absolute error, bias (mean signed error) with a 90% bootstrap interval, rank correlation over countries; the largest over- and underestimates.

## 5. Visualization
A scatter: published share (x) vs Jev's median (y), one dot per country, diagonal, the largest misses labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.002, top verdict `portrait`.

## Compared with
Integrated Values Surveys respondents (WVS and EVS, nationally representative samples)

## Limits
One survey per country, in different years (2010-2023); the published share has sampling error of a few points.

Results: `data/analysis/experiments/society_country_trust.json` (private). Code: `scripts/experiments/`.
