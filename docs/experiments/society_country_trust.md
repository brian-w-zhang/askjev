# society_country_trust

family: society

## Why ask this
Do most people in a country think others can be trusted? The answer ranges from a few percent to over 70%, and it's one of the most studied numbers in social science.

A model's guess about trust in a place reveals whether it knows the world country by country, or projects one middling picture onto all of them.

## The people and the data
The **World Values Survey** and the **European Values Study** interview representative samples of adults in dozens of countries every few years. One question asks whether "most people can be trusted" or "you need to be very careful in dealing with people". The measure is the share choosing "can be trusted", as compiled by Our World in Data from the combined surveys, at each country's latest survey since 2010.

## What Jev was asked
> In the 2022 World Values Survey or European Values Study in China, what share of people answered "most people can
> be trusted" (rather than "you need to be very careful in dealing with people")?
> *0% · 5% · 10% · ... · 95% · 100%*

## How it was measured
Jev's median guess against the published share for each country: how far off on average, in which direction, how widely its guesses spread compared with the real shares, and whether it ranks the countries in the same order (rank correlation: 1 means the same order).

## Caveats
- **Different years.** Each country's figure is from its latest survey since 2010, so years differ, and the question names the year. Trust can shift with events between surveys.
- **A known quirk of the question.** The survey question is a blunt either-or ("most people can be trusted" or "you need to be very careful"), and countries may read it differently. Some surprises in the real data, like China's high share, may reflect how the question is understood as much as how much people trust each other.
- **One number per country.** The published share has a sampling error of a few points, so small misses (under 5 points) mean little.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
