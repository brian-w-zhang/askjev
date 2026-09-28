# numbers_prices_year

family: numbers · new questions: 30

## 1. Question
Asked what eggs, gas, bread or electricity cost in US cities right now, which year's prices does Jev give, and what year does it say it is?

A model's sense of 'now' is frozen at its training data, but nobody sees the date stamp. Prices make it visible: they move every year, and BLS records them monthly, so each answer points to a year.

## 2. Sourcing
New questions (sources/bls_prices): 'What is the average retail price of <item> in US cities right now?' for 29 items with BLS average prices (U.S. city average, public domain, via FRED), in 12 log-spaced bins over each item's 1980-2026 range; plus 'What year is it right now?'.

Sources: `bls_prices`

## 3. Collection
30 new questions, each asked as written and with the options in three shuffled orders (averaged).

## 4. Scoring
For each item whose yearly price rises steadily (rank correlation of price with year 0.9 or more), the years whose average price falls in Jev's median bin; the item's implied year is the middle of them. Across items, the median implied year with a 90% bootstrap interval; the share of items where Jev's bin holds the August 2026 price; Jev's answer to the year question.

## 5. Visualization
A strip of implied years, one dot per item, with the year Jev says it is and August 2026 marked.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
BLS average prices by year, 1980-2026

## Limits
Bins are wide (about 15-20% each), so an implied year is a range; items whose prices went up and down (eggs, gasoline) are left out of the implied year and kept in the accuracy count.

Results: `data/analysis/experiments/numbers_prices_year.json` (private). Code: `scripts/experiments/`.
