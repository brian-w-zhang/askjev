# choices_fair_prices

family: choices

## Why ask this
In 1986, the psychologist Daniel Kahneman and economists Jack Knetsch and Richard Thaler asked the public about small business decisions: a hardware store raising the price of snow shovels after a blizzard, a landlord raising rent, a store keeping its price when its costs drop. The answers showed that people hold firms to an unwritten sense of fairness: passing on higher costs is fine, exploiting a shortage is not. The study became a classic of behavioral economics.

Models now advise both businesses and customers. Whose rulebook does Jev carry: the public's, or something closer to a textbook where prices simply follow supply and demand?

## The people and the data
The respondents were adults in Toronto and Vancouver, reached by telephone in 1984 and 1985 for Kahneman, Knetsch and Thaler's paper in the American Economic Review. The paper reports only the share who said completely fair or acceptable, so that grouped share is the people's number.

Jev was given all 23 of the paper's scenarios (Questions 1 to 16, several with variants, plus the UNICEF version of the doll auction). A content filter hid 14 of them from the site, mostly the wage-cutting ones, which leaves 9, mostly about prices.

## What Jev was asked
The paper's own wording and answers:

> A grocery store has several months supply of peanut butter in stock which it has on the shelves and in the
> storeroom. The owner hears that the wholesale price of peanut butter has increased and immediately raises the price
> on the current stock of peanut butter. Please rate this action as completely fair, acceptable, unfair or very
> unfair.
> *Completely fair · Acceptable · Unfair · Very unfair*

## How it was measured
For each scenario, Jev's probability on "completely fair" or "acceptable" against the share of respondents who said so. The analysis checks whether the scenarios fall in the same order (rank correlation: 1 means the same order), how far apart the two are on average, and whether they land on the same side of 50%.

## Caveats
- **Most scenarios hidden.** A content filter hid 14 of the 23 scenarios from the site, including the famous snow shovels and most of the wage-cutting ones, likely because they read as political. The 9 left are mostly about prices, so this says little about Jev's view of wages.
- **A 1980s Canadian public.** Their sense of fairness, and the dollar amounts, belong to that time and place.
- **Grouped answers only.** The paper reports only the share who said "completely fair" or "acceptable", so Jev's four-way answer is grouped the same way.
- **A famous paper.** These scenarios are textbook material in economics, and Jev may know the published results. Its answers still differ sharply from them, so it isn't simply recalling the paper.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
