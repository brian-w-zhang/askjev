# risk_ambiguity

family: risk

## Why ask this
This "ambiguity aversion" is one of the most studied quirks of human choice.

A model that talks people through decisions (a job offer with an unclear bonus, a new product with no track record) could amplify that caution or correct it. Here we can see which way Jev leans, and how that compares with people who were playing for real.

## The people and the data
The comparison comes from **choices13k** (Peterson and colleagues, 2021, in Science), a very large dataset of risky choices. US workers on Amazon Mechanical Turk chose between pairs of gambles five times each and were paid a bonus from one outcome, so their choices counted. In 452 of the problems, one gamble listed its possible payoffs but not their odds. About 15 to 18 people played each.

On average those players weren't ambiguity-averse at all: they took the unknown gamble 57% of the time.

## What Jev was asked
Each problem was one question with both gambles written out as the players saw them, the unknown one flagged in words:

> Imagine you must play one of these two gambles once, for real money (wins are paid to you, losses come out of your
> pocket). Which do you choose: gamble_a or gamble_b?
> *gamble_a: $27 with a 90% chance, or -$5 with a 10% chance · gamble_b: one of these amounts: $22, $26.5 or $27.5,
> with probabilities you are not told*

## How we measured it
For each problem, the share of Jev's answer on the unknown gamble, and the share of players' trials on it.

## Caveats
- **Not pure ambiguity.** The unknown gamble still lists its possible payoffs, so part of each choice is about amounts, not odds. We split the problems by whether the unknown gamble could beat the known one; Jev shies away in every group.
- **Small real stakes.** The players were US workers on Mechanical Turk, paid a bonus of 10% of one outcome, about 15 to 18 per problem. Real but small money.
- **The wording was ours.** The phrase "with probabilities you are not told" is our rendering of the study's hidden-odds display. A different phrasing, like "odds unknown", might read as more or less ominous.
- **Jev answers each problem fresh.** Players chose five times per problem; Jev answers once, as a probability over the two options. The human share is the share of trials, so the two aren't exactly the same kind of number.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
