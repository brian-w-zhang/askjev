# taste_vs_audience_film

family: taste

## Why ask this
Most of what Jev says about taste can only be checked against itself. Films are different: MovieLens, a recommendation site run by the GroupLens research lab, has millions of real ratings.

## The people and the data
MovieLens users: people who signed up to a free film-recommendation site and rated films they'd seen, between 1995 and 2023. For each film we use the distribution of its ratings, turned into the same five levels Jev answers on.

## What Jev was asked
Every film one at a time:

> How much would you enjoy watching Hud (1963)?
> *You'd turn it off within the first twenty minutes · You'd finish it but forget it within a week · You'd enjoy it
> once and not seek it out again · You'd recommend it to a friend · You'd rewatch it and count it among your
> favorites*

Each was also asked with the answers in reverse order, and the two averaged. Jev never saw the MovieLens ratings.

## How we measured it
Ranks rather than levels, because Jev's described levels and people's stars aren't the same scale. The biggest disagreements are the films whose two ranks are furthest apart.

## Caveats
- **Fans rate what they chose to watch.** MovieLens users rate films they picked, and people pick films they expect to like, so a niche documentary gets rated mostly by its fans. Jev rates every film cold. That alone pushes some niche titles higher for the audience.
- **Stars squeezed into five levels.** The bins are our choice, so we compare ranks, not levels.
- **A famous-film list.** Its rating may track what critics wrote as much as anything else.
- **Reputations change.** MovieLens ratings span 1995 to 2023, but what's written about a film or its star keeps changing. One possible reason Jev rates Bill Cosby's stand-up film so low is what has been written about Cosby since; we can't test that here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
