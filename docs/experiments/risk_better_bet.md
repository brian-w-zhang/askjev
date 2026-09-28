# risk_better_bet

family: risk

## Why ask this
Offer someone two gambles and the one with the better average payoff doesn't always win. People follow a better bet more often the bigger its edge, and when the edge is tiny they're close to a coin flip, swayed by how the options look. That curve, from indifferent to decisive, is one of the most measured patterns in decision science.

A model asked about money could sit anywhere on it: a cold calculator that always picks the higher average, a coin flipper, or something human-shaped. Where Jev lands says whether its sense of risk is people's sense of risk.

## The people and the data
The main comparison is **choices13k** (Peterson and colleagues, 2021, in Science), one of the largest datasets of risky choices. US workers on Amazon Mechanical Turk chose between pairs of gambles, and were paid a bonus of 10% of one outcome, so their choices had real, if small, consequences. We use the 1,928 problems where players got no feedback between rounds, about 15 to 18 people each.

## What Jev was asked
Each problem was one question with the two gambles written out in dollars, the way players saw them:

> Imagine you must play one of these two gambles once, for real money (wins are paid to you, losses come out of your
> pocket). Which do you choose: gamble_a or gamble_b?
> *gamble_a: $24 for sure · gamble_b: $19 with an 80% chance, $36 with a 10% chance, $38 with a 5% chance, $42 with
> a 2.5% chance, $50 with a 1.25% chance, $66 with a 0.625% chance, or $98 with a 0.625% chance*

## How we measured it
For every problem we compute the better gamble's **edge**: how much more it pays on average, as a share of its largest payoff. We sort problems into six bins by edge and, in each bin, compare how often Jev and people pick the better gamble. We also rank all problems by how strongly each side chose gamble B and compare the two rankings (rank correlation: 1 same order, 0 no relation), and count the problems where each side's majority picks the better gamble.

## Caveats
- **Small real stakes for people, none for Jev.** The choices13k players were paid a bonus of 10% of one outcome, so their money was real but small. Jev has no stake at all, so its choices are hypothetical by construction.
- **Few people per problem.** Each problem was played by about 15 to 18 workers, so a single problem's human share is noisy.
- **Numbers-heavy wording.** Some gambles list up to nine outcomes, several with odds under a tenth of a percent. Weighing that many percentages is arithmetic, a weak spot TypeSafe documents for Jev, so this is partly a test of reading numbers.
- **A second, different population.** The Wulff et al. problems come from many older studies pooled together, with real or hypothetical payoffs the transcripts don't distinguish. On those Jev falls further behind people, so the headline depends on which people you compare with.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
