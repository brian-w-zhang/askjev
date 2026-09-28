# taste_top_place

family: taste

## Why ask this
A dream destination says what someone values: nature or cities, adventure or ease, famous or undiscovered. For a model, it also shows how its sense of a place is built from travel writing, photos described in text, and news.

## The people and the data
No people here: Jev against its own opinions.

## What Jev was asked
Every place one at a time, with five answers describing what you'd do:

> How much would you enjoy a trip on a working cargo ship?
> *You'd cut it short and head home early · You'd get through it but never book another · You'd enjoy it if someone
> else planned it · You'd book one yourself · You'd make it a yearly habit*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated places then played a round-robin final: 276 games of "Which place would you rather visit?", each asked with the two names in both orders.

## How we measured it
A place's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A list written by another AI.** The landmarks, cities and natural wonders were written for this project by Claude. What's on the list shapes what can win, and famous postcard views are over-represented.
- **The bottom is about danger, not beauty.** The least favorite places are cities known for conflict or crime and an event where people get hurt. A trip's rating mixes appeal with safety, so the bottom reflects travel warnings more than taste, and it echoes how those places are written about in English.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
