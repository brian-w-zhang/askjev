# numbers_crowd_same_mistakes

family: numbers

## Why ask this
If a model's numbers come from how people talk about things, its errors should look like people's errors: too high where people guess too high, too low where they guess too low. If its numbers come from reference facts, its errors should have nothing to do with the crowd's. The same questions that test the wisdom of crowds can tell which it is.

## The people and the data


## What Jev was asked
The same questions, in the same ordered ranges, for example:

> How many Kenyas fit into the continental U.S.?
> *Under 1.5 · 1.5 to 3 · ... · 150 to 300 · 300 or more*

The crowd's median guess and Jev's answer both fell below the true range, a shared miss. This experiment looks at the same answers from a different angle.

## How we measured it
For every question, the direction and size of the miss in answer ranges, for Jev and for the crowd's median. Then: how closely the two sets of misses line up across questions (rank correlation: 1 same pattern, 0 unrelated), and, on the questions the crowd gets wrong, how often Jev is wrong the same way, right, or wrong the other way.

## Caveats
- **Direction, not size.** Errors are counted in answer ranges, whose width differs by domain, so we compare directions (too high or too low) rather than sizes.
- **A small set of misses.** 88 questions where the crowd's median misses, across eight domains; the shares move by several points with a handful of questions.
- **The same caveats as the crowd test.** About 500 US online participants per question in February 2017; seven questions hidden by a content filter; and for Jev many of these are facts it has read rather than estimates.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
