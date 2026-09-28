# taste_choices_vs_ratings

family: taste

## Why ask this
There are two ways to find someone's favorite: ask them to rate things one at a time, or make them choose between pairs. People are known to give different answers to the two. For a model, it matters which one you trust: ask it "rate this" and "pick one" and you may get different favorites.

## The people and the data
No people here: this compares Jev with itself, across 12 taste domains (films, books, board games, anime, beers, music, foods, places, art, nature, activities, culture). In each domain, Jev's 24 top-rated items played every other in a round-robin final: 276 games per domain, 3,281 in all.

## What Jev was asked
The ratings asked one item at a time, with five described answers, for example "How much would you enjoy watching Hud (1963)?" from "You'd turn it off within the first twenty minutes" to "You'd rewatch it and count it among your favorites". The final asked two at a time:

> Which film would you rather watch?
> *The Shawshank Redemption (1994) · The Godfather (1972)*

Every head-to-head was asked with the two options in both orders.

## How it was measured
**Consistency:** take any three finalists A, B and C. If Jev prefers A to B and B to C, it should prefer A to C. A three-way comparison "goes in a circle" when it doesn't. A random tournament has 25% circles; a perfectly consistent chooser has none. **Agreement:** the 24 finalists are ranked by the head-to-head results and by their ratings, and the two orders are compared with a rank correlation.

## Caveats
- **The ratings can't separate near-ties.** The finalists all sit near the top of a five-level scale, so the ratings barely distinguish them; a low correlation partly says the ratings ran out of resolution, and the head-to-heads could still tell them apart.
- **Both formats are the project's.** The ratings use five answer descriptions written for this project; the head-to-heads are plain "which would you rather" choices. A different rating scale, with more or differently worded levels, might agree with the choices more.
- **The finalists came from the ratings.** Only each domain's 24 top-rated items were compared head to head, so this says nothing about disagreements lower down the list.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
