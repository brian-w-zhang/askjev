# taste_vs_audience_beer

family: taste

## Why ask this
Beer enthusiasts have strong shared tastes, hoppy IPAs among their favorites. Comparing Jev with BeerAdvocate's reviewers shows whether a model shares the enthusiasts' palate, or has a style bias of its own.

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
