# world_lost_wallets

family: world

## Why ask this
In 2019 a team of economists (Cohn, Maréchal, Tannenbaum and Zünd) handed 17,303 "lost" wallets to strangers at reception desks in 355 cities across 40 countries and counted how many got returned. Return rates ranged from under 20% to over 75% by country. And in 38 of the 40 countries, a wallet with money in it was returned more often than an empty one, the opposite of what economists and ordinary people predicted.

A model that reasons from self-interest ("more money, more temptation") would make the same wrong prediction. A model that knows people would get it right.

## The people and the data
The study's own data (public, CC0), covering 17,303 wallets in 355 cities of 40 countries. A wallet counts as returned when the staff member emailed its owner. For each country the data give the share returned without money and with about US$13 in local currency, plus a larger amount (about US$94) in the US, the UK and Poland. The "people" here are the staff at banks, hotels, post offices, museums and public offices who received the wallets, and each country's rate pools several cities and kinds of institution.

## What Jev was asked
The experiment described in full, per country and condition:

> In a field experiment in large cities in Peru, researchers handed lost wallets to staff at reception desks of
> banks, hotels, post offices, museums and public offices, saying they had found it on the street and asking the
> staff to take care of it. Each wallet was a clear card case with business cards showing the owner's name and
> email address, a grocery list, a key, and about 13 US dollars in local currency. What share of the staff emailed
> the owner to return it?
> *0% · 5% · 10% · ... · 100%*

(In Peru, about 13%.) Plus one direct question: which wallets were returned more often, with money or without? 84 questions in all, each asked with the options in shuffled orders and averaged.

## How it was measured
Jev's estimate is the middle of its answer. It is compared with the real return rate: how well Jev orders the 40 countries (rank correlation: 1 same order, 0 no relation), the average miss in percentage points, and, for each country, whether Jev's estimate with money is higher than without, as the real rates almost always are.

## Caveats
- **A middle-of-the-scale guess.** Estimates that hug the middle of a 0-100% scale can earn a moderate rank correlation and a large average miss at the same time.
- **It may know the study.** The study was covered widely in 2019. Jev knowing the headline (money helps) when asked directly, but not applying it country by country, looks like remembering a fact rather than reasoning from it.
- **Pooled across places.** Each country's rate pools several cities and kinds of institutions (banks, hotels, post offices, museums). Jev was told the setting in general terms, not which city or desk.
- **Human predictions not used.** The study also surveyed economists and ordinary people, who predicted that money would reduce returns. Those predictions are cited from the paper; their data weren't used here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
