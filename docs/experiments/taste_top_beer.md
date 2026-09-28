# taste_top_beer

family: taste

## Why ask this
Beer is a taste with strong tribes: hop lovers, stout people, Belgian loyalists, lager purists. Which tribe a model joins, and whether it reaches for the prestige bottles or the everyday ones, is a fun and telling read.

## The people and the data
No people here: Jev against its own opinions. How Jev compares with BeerAdvocate's reviewers is its own experiment.

## What Jev was asked
Every beer one at a time, with five answers describing what you'd do:

> How much would you enjoy drinking Maudite by Unibroue (Belgian Strong Dark Ale)?
> *You'd pour it out after a sip · You'd finish the glass but not order it again · You'd drink it again if it was
> what's on offer · You'd order it again by name · You'd seek it out and keep it stocked at home*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated beers then played a round-robin final: 276 games of "Which beer would you rather drink?", each asked with the names in both orders.

## How we measured it
A beer's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A model can't taste.** Jev has never had a drink. Its picks come from what's written about these beers: reviews, style guides, reputations. A Belgian classic with a famous name has a lot of admiring text behind it.
- **The catalog.** The beers are those with at least 100 reviews on BeerAdvocate between 1998 and 2012, a craft-beer enthusiast site, so the list is heavy on American craft and Belgian styles and stops in 2012.
- **The least consistent final.**
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
