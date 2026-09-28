# taste_top_activity

family: taste

## Why ask this
How people like to spend an evening is personal: games, sport, crafts, social events. For a model, it shows which activities it treats as appealing when it can't actually do any of them, and whether it leans toward what gamers and critics praise.

## The people and the data
No people here: Jev against its own opinions. They mix video games (Hades, an evening playing Chrono Trigger), board and card games (bourré), sports (a bandy match), pastimes and events, from the cozy (Animal Crossing) to the extreme (hiking up an active volcano).

## What Jev was asked
Every entry one at a time, with five answers describing what you'd do:

> How much would you enjoy playing bourré?
> *You'd leave the table after one round · You'd finish the game but not ask for another · You'd play along when
> others set it up · You'd suggest it yourself on a game night · You'd seek out clubs or tournaments to play it*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated entries then played a round-robin final: 276 games of "Which would you rather play or do?", each asked with the two names in both orders.

## How it was measured
An entry's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A list written by another AI.** The video games, sports and pastimes were written for this project by Claude. What's on the list shapes what can win, and acclaimed recent video games are well represented.
- **Physical activities without a body.** Jev can't run stairs or ride a bull, so for physical activities it's judging how they're written about. Danger and discomfort dominate the bottom, which may reflect that more than taste.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
