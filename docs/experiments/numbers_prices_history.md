# numbers_prices_history

family: numbers · new questions: 97

## 1. Question
Asked what an item cost in US cities in 1985, 1995, 2005 and 2015, does Jev know the old prices as well as recent ones, and which way does it err?

Price history is a concrete test of how a model holds the past: does it project today's prices back, or remember that a dozen eggs cost under a dollar in 1985?

## 2. Sourcing
New questions (sources/bls_prices): 'What was the average retail price of <item> in US cities in <year>?' for 29 items and the years each BLS series fully covers (97 questions), in the same 12 bins as the 'right now' questions.

Sources: `bls_prices`

## 3. Collection
97 new questions, each asked as written and in three shuffled orders (averaged).

## 4. Scoring
Per year, the share where Jev's median bin is the bin holding that year's average price, the share within one bin, and the mean signed error in bins (positive = too high), with 90% bootstrap intervals.

## 5. Visualization
Dots per year: share right (and within one bin), with the mean signed error as a label.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.146, top verdict `portrait`.

## Compared with
BLS average prices by year

## Limits
Items start at different years (some in 1995 or 2006), so earlier years have fewer items.

Results: `data/analysis/experiments/numbers_prices_history.json` (private). Code: `scripts/experiments/`.
