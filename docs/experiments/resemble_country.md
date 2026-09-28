# resemble_country

family: resemble

## 1. Question
On the world's cross-national opinion surveys, whose answers do Jev's most resemble, country by country?

Earlier work found language models closest to the US and parts of Europe (Durmus et al. 2023, GlobalOpinionQA); where Jev lands, and how far it is from everyone, is a direct portrait of whose voice it carries.

## 2. Sourcing
Existing GlobalOpinionQA questions (Pew Global Attitudes and World Values Survey items, via Anthropic/llm_global_opinions), each with real answer distributions for up to 133 countries. Politically flagged items are hidden and excluded, and Pew's non-national (mostly urban) samples are left out so every row is a national sample. Enough: ~500 shown questions; only questions asked in 30+ countries count, so every country is compared on a broad set.

Sources: `globalopinionqa`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per question, similarity = 1 - Jensen-Shannon distance between Jev's distribution and the country's (the measure Durmus et al. used). A country's score is its mean similarity over the questions it answered; countries with fewer than 20 such questions are dropped. 90% intervals from resampling questions. Jev's 'most people' answer is scored the same way as a check.

## 5. Visualization
A world map shaded by similarity, with the top ten and bottom five as a ranked strip beside it.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.023, top verdict `portrait`.

## Compared with
national survey samples in up to 133 countries

## Limits
Surveys differ by country and year; similarity is over the questions each country was asked. Items about politics are excluded, which leaves attitudes to institutions, society and daily life.

Results: `data/analysis/experiments/resemble_country.json` (private). Code: `scripts/experiments/`.
