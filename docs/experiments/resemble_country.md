# resemble_country

family: resemble

## Why ask this
When Anthropic researchers compared several language models with opinion surveys from dozens of countries (Durmus and colleagues, 2023, the GlobalOpinionQA dataset), the models' answers looked most like those of people in the United States and parts of Europe. That's a portrait of whose voice a model carries by default.

Jev was trained differently and by a different company. Whose answers does it end up closest to?

## The people and the data
The questions come from two of the largest cross-national surveys: the Pew Global Attitudes Survey and the World Values Survey, as compiled in GlobalOpinionQA. Each question comes with the share of people in each country who gave each answer, from national samples.

## What Jev was asked
Each survey question, with its answer options, as the survey asked it:

> How frequently do the following things occur in your neighborhood? Alcohol consumed in the streets
> *Very frequently · Quite frequently · Not frequently · Not at all frequently · Don't know*

Each question was also asked with the options in shuffled orders, and Jev's answers were averaged over the orders.

## How we measured it
First we took "don't know" and "refused" out of both Jev's answer and each country's, and rescaled what was left. Then, for each question and country, we compare the two spreads of answers on a scale from 0 (nothing in common) to 1 (identical), the measure the GlobalOpinionQA authors used. A country's score is its average over the questions it answered, with a 90% range from resampling the questions.

## Caveats
- **"Don't know" had to go.** Left in, it would rank countries by how rarely their people say "don't know", so we dropped it from both sides and compared the remaining answers.
- **Different questions per country.**
- **Close scores, wide ranges.** Read the map for regions, not ranks.
- **Politics removed.** About 70% of the original survey items are political. A content filter hides political and sensitive questions from the site, so this compares attitudes to society, institutions and daily life only.
- **The surveys' own reach.** Pew and World Values Survey samples are national, but face-to-face and phone surveys still miss people; we dropped Pew's non-national (mostly urban) samples entirely.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
