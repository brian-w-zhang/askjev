# Jev vs 15-year-olds in seven countries

`resemble_teens` · family: resemble

## 1. Question
On the PISA student questionnaire (trust, belonging, ambition), which country's 15-year-olds does Jev answer like?

PISA asks teenagers the same attitude questions worldwide; Jev as one more student is a quick read on the attitudes it carries.

## 2. Sourcing
Existing questions from `pisa_questionnaire`, each with real answer distributions per population. Enough for a ranking of populations; the answer shares show where Jev stands out.

Sources: `pisa_questionnaire`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per question and population, 1 - Jensen-Shannon distance between Jev's distribution and the population's; mean per population with a 90% bootstrap interval over questions; plus the questions where Jev's top answer is furthest from the pooled populations.

## 5. Visualization
A ranked strip of populations by similarity, and the three questions where Jev differs most.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
15-year-old students in the PISA 2018/2022 samples of seven countries

## Limits
Questionnaire items only (no test scores); country samples are national, weighted by PISA.

Results: `data/analysis/experiments/resemble_teens.json` (private). Code: `scripts/experiments/`.
