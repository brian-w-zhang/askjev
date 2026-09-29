# world_ladder

family: world

## Why ask this
Every year the World Happiness Report ranks countries by how people there rate their own lives, and every year it has surprises: Costa Rica and Mexico near the top, rich East Asian countries in the middle. A model that assumes money buys happiness would miss exactly those.

It matters whenever a model writes or advises about a place: a travel piece, a report on a country's mood after a crisis, a student's essay. If its sense of how people feel comes from headlines, it will paint whole countries as gloomier, or cheerier, than the people there say they are.

## The people and the data
The Gallup World Poll asks people in each country every year to place their life on a ladder from 0 (the worst possible life for them) to 10 (the best). The World Happiness Report 2025 publishes each country's average over 2022-2024; this experiment uses those averages as published by Our World in Data (CC BY 4.0), for 145 countries.

## What Jev was asked
One question per country, describing the ladder in full:

> The Gallup World Poll asks people to imagine a ladder with steps numbered from 0 at the bottom, the worst possible
> life for them, to 10 at the top, the best possible life, and to say which step they stand on now. What was the
> average answer in Botswana in 2022-2024?
> *Below 3.0 · 3.0 to 3.5 · 3.5 to 4.0 · ... · 7.5 to 8.0 · 8.0 or above*

That's 146 new questions, each asked with the answer bins in three shuffled orders and averaged.

## How it was measured
Jev's estimate is the average of the bins' middles, weighted by how likely it rated each. It is compared with the published average: how well Jev orders the countries (a rank correlation: 1 same order, 0 no relation), the average miss in ladder steps, how often it picks the right half-point bin, and whether its misses line up with a country's wealth or region.

## Caveats
- **It may remember the rankings.** The World Happiness Report is published every year and widely covered. Jev may recall older editions better than the 2025 one used for scoring, which would explain misses where a country's rating moved sharply in recent years (Afghanistan's collapse, Botswana's fall).
- **Half-step answers.**
- **The truth has error too.** Each country's figure is a three-year average of Gallup samples, with sampling error of around 0.1.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
