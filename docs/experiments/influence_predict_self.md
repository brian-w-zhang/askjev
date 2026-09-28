# influence_predict_self

family: influence

## Why ask this
The portrait asks Jev a lot of questions about itself: its personality, its tastes, its habits. Those answers are only worth something if Jev's picture of itself matches what it actually does. Self-knowledge is testable when the "self" can answer the same question directly: ask it what it would choose, then ask it to choose.

## The people and the data
Jev against itself, with the real votes as a reference.

## What Jev was asked
Each question was wrapped in a description of Jev being asked it:

> An AI model named Jev was asked the question below. Which option did it choose?
>
> Question: Would you rather never hiccup, never itch or never sneeze again?
> *never itch · never hiccup · never sneeze*

That's 250 new questions, each asked with the options in shuffled orders and averaged.

## How we measured it
We compare Jev's predicted option with three things: its own top answer when asked the question directly, its answer for "most people", and the real voters' majority. We also split the questions by how sure Jev's own direct answer was.

## Caveats
- **Does it know it's Jev?.** The question names "an AI model named Jev" with no other description. Jev may not recognize itself in that name, in which case this measures how well it predicts a generic AI, which happens to be itself.
- **Taste questions only.** All the questions are polls and would-you-rather dilemmas, where Jev's own answers are often close calls. Self- prediction on facts or on its personality items wasn't tested.
- **Who voted.** The crowd comparison uses r/polls and either.io voters, self-selected online audiences.
- **Small set.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
