# taste_top_nature

family: taste

## Why ask this
Asking what someone loves in nature is a gentle way into their temperament: big and awe-inspiring, small and cute, calm, wild. For a model, it also shows how it handles experiences it can never have: a smell, a storm, an animal up close.

## The people and the data
No people here: Jev against its own opinions.

## What Jev was asked
Every entry one at a time, with five answers describing what you'd do:

> How much would you enjoy spending a day on a jungle river?
> *You'd want to leave within the hour · You'd get through the day and not go back · You'd be glad you went · You'd go
> back and bring friends · You'd want to live near it*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated entries then played a round-robin final: 276 games of "Which would you rather see or experience?", each asked with the two names in both orders.

## How we measured it
An entry's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A list written by another AI.** The animals, sights, smells and weather were written for this project by Claude. What's on the list shapes what can win, and the list favors charismatic animals and famous sights.
- **Some items are scenes, some are names.** Some entries are bare names ("giant pandas"), others are phrased as moments ("witnessing a blue glacier ice cave"). A vivid scene may do better than a plain noun.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
