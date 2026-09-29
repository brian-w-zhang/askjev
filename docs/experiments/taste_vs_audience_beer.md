# taste_vs_audience_beer

family: taste

## Why ask this
Ask a model which beer to bring to a party, or to describe what a brewery's best bottles are, and it answers from what it has read, not from a glass. Beer enthusiasts have strong shared tastes, and a reviewing site like BeerAdvocate records them beer by beer.

Comparing Jev with those reviewers shows whether its sense of a good beer matches the people who drink and rate them, or whether it carries a style bias of its own that would quietly shape every recommendation it makes.

## The people and the data
BeerAdvocate reviewers, via 1.59 million reviews collected by McAuley, Leskovec and Jurafsky from 1998 to 2012. For each beer, the study uses the spread of its reviewers' overall scores, sorted into the same five levels Jev answers on.

## What Jev was asked
Every beer one at a time:

> How much would you enjoy drinking Maudite by Unibroue (Belgian Strong Dark Ale)?
> *You'd pour it out after a sip · You'd finish the glass but not order it again · You'd drink it again if it was what's
> on offer · You'd order it again by name · You'd seek it out and keep it stocked at home*

Each was also asked with the answers reversed, and the two averaged. Jev never saw the reviews.

## How it was measured
Ranks, because the scales differ.

## Caveats
- **A craft-beer crowd from 1998 to 2012.** BeerAdvocate reviewers are craft-beer enthusiasts, and the reviews stop in 2012. A different crowd, or a later one, might rate hoppy beers very differently.
- **Small audiences for some beers.**
- **A model can't taste.** Jev has never had a drink; its ratings reflect how beers and styles are written about.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
