# resemble_young_slovaks

family: resemble

## 1. Question
On the Young People Survey (fears, hobbies, music, spending), where does Jev differ from ~1,000 people aged 15-30?

A single real sample with hundreds of everyday questions; the items where Jev is sure and they aren't are the story.

## 2. Sourcing
Existing questions from `young_people_survey`, each with real answer distributions per population. Enough for a ranking of populations; the answer shares show where Jev stands out.

Sources: `young_people_survey`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per question and population, 1 - Jensen-Shannon distance between Jev's distribution and the population's; mean per population with a 90% bootstrap interval over questions; plus the questions where Jev's top answer is furthest from the pooled populations.

## 5. Visualization
A ranked strip of populations by similarity, and the three questions where Jev differs most.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.321, top verdict `portrait`.

## Compared with
Slovak young people aged 15-30 (2013 survey, n≈1,000)

## Limits
One country, one age group, one year.

Results: `data/analysis/experiments/resemble_young_slovaks.json` (private). Code: `scripts/experiments/`.
