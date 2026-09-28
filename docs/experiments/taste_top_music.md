# taste_top_music

family: taste

## Why ask this
Music taste is identity: what you'd play on a long drive says a lot about you. A model that has read about almost every album ever reviewed will have "opinions" that mostly mirror critics. The interesting question is where it lands when it has to choose, and whether its one-at-a-time ratings agree with its choices.

## The people and the data
No people here: Jev against its own opinions. Jev's guess of how most people would react was asked too, and is used in another experiment.

## What Jev was asked
Every entry one at a time, with five answers describing what you'd do:

> How would you react to an hour of Irish traditional music?
> *You'd turn it off within a minute · You'd sit through it only if someone else put it on · You'd leave it playing in
> the background without minding · You'd add a few tracks of it to your own playlists · You'd spend whole evenings
> digging deeper into it*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated entries then played a round-robin final: 276 games of "Which would you rather listen to?", each asked with the two names in both orders.

## How it was measured
An entry's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A list written by another AI.** There's no public catalog for "music you'd enjoy", so the list was written for this project by Claude: classic albums, genres and everyday sounds. What's on the list shapes what can win, and a list written by one model and judged by another may favor exactly the famous albums both have read the most about.
- **Albums against noises.** The list mixes records with sounds (a vuvuzela, a beginner's recorder, harsh noise). The bottom of the ranking is sounds, so the bottom tells you little about musical taste.
- **A shaky final.**
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
