# taste_enthusiast_leans

family: taste

## Why ask this
Enthusiast communities have tastes that outsiders don't share: board-game hobbyists chase the newest designs, beer reviewers prize strength and intensity. If Jev doesn't lean the same way, it tells us which kind of judge it is: a hobbyist or a well-read outsider.

## The people and the data
BoardGameGeek users, BeerAdvocate reviewers and MovieLens users, via public datasets of their ratings. For each pair of items, the audience's pick is the one most people who rated both preferred. We know each item's release year (from its title), its number of ratings, and each beer's alcohol by volume, so we can check how often each side picks the older game, the more-rated game or the weaker beer.

## What Jev was asked
Each pair as a simple choice:

> Which board game would you rather play?
> *Alhambra (2003) · Killer Bunnies and the Quest for the Magic Carrot (2002)*

Once for itself and once for "most people", each with the options in both orders.

## How we measured it
For each lean, the share of pairs where the audience picks that side, and the share where Jev does, each with a 90% interval. For example, among pairs of board games from different years: how often is the pick the older game?

## Caveats
- **Older and more-rated overlap.** Older board games have had more years to collect ratings, so "picks the older game" and "picks the more-rated game" are partly the same lean.
- **Some pairs couldn't be matched.** To match each option to its year or alcohol content we read the name and year printed in it. Pairs where that couldn't be done reliably were left out, more of them for beers.
- **Within-genre pairs.** Pairs were drawn within a board-game subdomain or a beer-style family, so the differences are within, not across, kinds.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
