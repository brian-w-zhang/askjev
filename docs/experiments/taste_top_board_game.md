# taste_top_board_game

family: taste

## Why ask this
Board games are social, so a favorite says what kind of evening you want: a clever party game, a long strategy session, a two-player duel. With thousands of games rated one at a time and a final among the best, it's possible to see what Jev reaches for, and whether the ratings and the final agree.

## The people and the data
No people here: Jev against its own opinions. How Jev's taste compares with BoardGameGeek users is its own experiment.

## What Jev was asked
Every game one at a time, with five answers describing what you'd do:

> How much would you enjoy playing Medina (2001)?
> *You'd want to quit before the first game ended · You'd play one game and never ask for it again · You'd play it
> again if someone else suggested it · You'd suggest it yourself at the next game night · You'd want to own it and
> play it again and again*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated games then played a round-robin final: 276 games of "Which board game would you rather play?", each asked with the names in both orders.

## How it was measured
A game's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A game with nobody at the table.** The question asks how much "you" would enjoy playing, with no group, no rules explanation and no table time. Famous, easy-to-picture games like Codenames and Carcassonne, which Jev has read the most about, likely gain from that.
- **The catalog.** The games are those with at least 500 ratings on BoardGameGeek, the main hobby site, so the list is the hobby's catalog, heavy on designer games.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
