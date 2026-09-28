# polls_cuisines

family: polls

## Why ask this
A model can know what people like without liking it itself. It can know that Americans love Italian and Mexican food and still, asked for its own taste, rank something else first. The gap between the two is worth seeing: it shows where Jev's "own" answers diverge from the crowd it can describe perfectly well.

Food is a good test, because FiveThirtyEight once ran a bracket-style survey of which world cuisines Americans like.

## The people and the data
FiveThirtyEight's **Food World Cup** (2014, run with SurveyMonkey): about 1,000 US adults rated 40 world cuisines, from Italian and Mexican to Ghanaian and Bosnian. From their ratings, about 790 head-to-heads, each with the share of respondents who preferred one cuisine to the other.

## What Jev was asked
Every head-to-head, twice: once for its own taste, and once for what it thinks most people would say.

> Which cuisine do you like more: American food or Ghanaian food?
> *American food · Ghanaian food*

## How it was measured
From each set of head-to-heads comes a ranking of the 40 cuisines (a standard model that turns many one-on-one wins into one order). Then three rankings are compared: Jev's own taste, its guess of Americans, and Americans' actual preferences, with rank correlations (1 = same order, 0 = no relation).

## Caveats
- **Americans in 2014.** The survey ran in 2014 with about 1,000 US adults; American tastes in food have changed since, especially toward cuisines that were less familiar then.
- **Many hadn't tried the food.** Respondents rated cuisines they may never have eaten, and a cuisine people don't know tends to lose. Jev has read about every one of them, which may explain some of its generosity toward less-familiar cuisines.
- **Rankings from pairs.** Both rankings are built from the same head-to-heads with a standard ranking model, so a cuisine's exact rank can shift by a few places with small changes in its matchups.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
