# taste_top_film

family: taste

## Why ask this
If you asked a friend for their favorite film you'd get one answer, maybe with a pause. A model can be asked about thousands of films one at a time, which makes a real ranking possible, not just a gut pick. The interesting parts are what rises to the top, what sinks, and whether the top reflects anything beyond the most celebrated films on the internet.

## The people and the data
There are no people in this one: it's Jev against its own opinions. The films come from MovieLens, a long-running film-recommendation site run by the GroupLens research lab. (How Jev's taste compares with MovieLens users is its own experiment: "Jev's taste in films vs MovieLens users".)

## What Jev was asked
First, every film one at a time, with five answers that describe what you'd actually do:

> How much would you enjoy watching Hud (1963)?
> *You'd turn it off within the first twenty minutes · You'd finish it but forget it within a week · You'd enjoy it
> once and not seek it out again · You'd recommend it to a friend · You'd rewatch it and count it among your
> favorites*

Each film was asked twice, the second time with the answers in reverse order, and the two averaged.

Ratings like these crowd the top with near-ties, so the 24 highest-rated films then played a round-robin final: every film against every other, 276 games, each a simple choice, "Which film would you rather watch?", asked with the two titles in both orders.

## How we measured it
For the ratings, a film's score is where Jev's answer lands on the five levels, 0 (turn it off) to 4 (a favorite). For the final, each game gives the winner Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half. The order of the top ten comes from a standard way of ranking players from head-to-head results (a Bradley-Terry model); the win counts shown are the plain totals.

## Caveats
- **A list of famous films, judged by a model that has read about them.** A top ten led by The Shawshank Redemption and The Godfather looks a lot like the internet's consensus canon, so "Jev's taste" here is hard to separate from what it has read people say about these films.
- **The finalists were picked by Jev's own ratings.** A film it underrated one at a time never got the chance to win head to head.
- **Our answer wording.** We wrote the five answer levels ("You'd turn it off within the first twenty minutes" up to "You'd rewatch it and count it among your favorites"). The top level asks for a lot, which is part of why so many films tie near the top and a final was needed.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
