# numbers_prices_year

family: numbers

## Why ask this
A model's sense of "now" is frozen at the point its training data ends, but it carries no visible date stamp. Prices make that stamp visible: they move every year, and the US Bureau of Labor Statistics records the average price of dozens of everyday items every month. So each price Jev gives for "right now" points to a year.

## The people and the data
No people: the truth is the BLS average retail price in US cities (public domain, via the St. Louis Fed's FRED database), monthly from 1980 to August 2026, for 29 everyday items: bread, cheese, bananas, beer, eggs, gasoline, electricity and more.

## What Jev was asked
One question per item, answered in 12 price ranges spanning the item's 1980-2026 prices:

> What is the average retail price of a pound of lemons in US cities right now?
> *Under $0.57 · $0.57 to $0.66 · $0.67 to $0.77 · ... · $2.30 to $2.69 · $2.70 or more*

Plus one more: "What year is it right now?" That's 30 new questions, each asked with the options in three shuffled orders and averaged.

## How it was measured
For each item whose average yearly price rises steadily, the analysis finds the years whose price falls in Jev's answer; the middle of those is the item's implied year. The report gives the median across items with a 90% range, how often Jev's answer covers the August 2026 price, and the year Jev names.

## Caveats
- **Wide answer bins.**
- **Only steadily rising prices.** Items whose prices went up and down (eggs, gasoline) can't point to a single year, so they're left out of the implied year and kept only in the "right now" accuracy count.
- **Dates are a known weak spot.** TypeSafe lists date and time comparison among Jev's known weaknesses. A model can't know today's date without being told; the interesting part is which year its prices come from and how that differs from the year it names.
- **Averages across cities.** The truth is the BLS "U.S. city average" price, which no single store charges.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
