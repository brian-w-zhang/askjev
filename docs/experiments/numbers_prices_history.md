# numbers_prices_history

family: numbers

## Why ask this
Price history is a concrete test of how a model holds the past. Does it know that a dozen eggs cost under a dollar in 1985, or does it project today's prices backward? And does it know the recent past as well as the distant one?

## The people and the data
No people: the truth is the average retail price in US cities recorded by the Bureau of Labor Statistics (public domain, via the St. Louis Fed's FRED database). There are 29 everyday items, from cheddar cheese to field-grown tomatoes, each asked for 1985, 1995, 2005 and 2015 wherever its price series covers the full year.

## What Jev was asked
One question per item and year, in the same 12 price ranges as the "right now" questions:

> What was the average retail price of a pound of cheddar cheese in US cities in 2015?
> *Under $2.40 · $2.40 to $2.64 · ... · $6.50 to $7.29 · $7.30 or more*

## How it was measured
For each year, the share of items where Jev's middle answer is the range holding that year's average price, the share within one range, and the average lean of its misses in ranges (positive means too high), with 90% intervals from resampling items.

## Caveats
- **Different items per year.** Part of the difference between years is which items are included.
- **Wide ranges.**
- **Numbers are a known weak spot.** TypeSafe lists raw numeric values among Jev's known weaknesses; ordered ranges instead of free numbers keep that from dominating, but not entirely.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
