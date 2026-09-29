# taste_top_anime

family: taste

## Why ask this
Anime has a devoted fan culture with strong opinions about what's great, and "what should I watch next?" is a common thing to ask a model. Its answer depends on its own sense of which shows are worth your time.

A full ranking shows where that sense sits: on the fan consensus, on the films outsiders know (Studio Ghibli), or somewhere of its own.

## The people and the data
No people here: Jev against its own opinions. Adult-genre titles were left out. How Jev compares with MyAnimeList users is its own experiment.

## What Jev was asked
Every title one at a time, with five answers describing what you'd do:

> How much would you enjoy watching Nogizaka Haruka no Himitsu (TV series)?
> *You'd give up on it early · You'd finish it but forget it within a week · You'd enjoy it once and not rewatch it ·
> You'd recommend it to a friend · You'd rewatch it and count it among your favorites*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated titles then played a round-robin final: 276 games of "Which anime would you rather watch?", each asked with the titles in both orders.

## How it was measured
A title's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **Reputation or taste.** The winners are titles that appear on nearly every "best anime" list Jev could have read. A model that has read the rankings will tend to reproduce them, so this list can't tell Jev's taste apart from the fan consensus.
- **The catalog.** The anime come from a 2016 MyAnimeList dataset, titles with at least 300 ratings, so nothing after 2016 appears, and adult-genre titles were left out of the questions.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
