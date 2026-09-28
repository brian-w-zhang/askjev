# risk_prospect_theory

family: risk

## Why ask this
In 1979 Daniel Kahneman and Amos Tversky showed that people treat gains and losses differently. They play safe with gains and take risks to avoid losses. This "reflection effect" is the heart of prospect theory, one of the most influential ideas in economics.

People increasingly ask models what to do about money: take the settlement or go to court, lock in a rate or wait. Whether a model has people's risk instincts, the opposite ones, or none, shapes that advice.

## The people and the data
In 2020 Ruggeri and colleagues re-ran the original prospect-theory problems with 4,098 people in 19 countries, using the original structure with amounts converted to local currency. This experiment uses their published answers, pooled across countries. The data are public on OSF for research use.

This experiment pairs 17 of their gamble choices by hand into 8 classic effects, each a pair that differs in one way: gains vs losses, a certain outcome vs the same odds scaled down, a one-stage vs a two-stage game, one big prize vs split prizes, and a pure framing change where the final amounts are identical.

## What Jev was asked
Each choice was its own question, in the US version's wording:

> Which would you prefer: an 80% chance of gaining $8,000 (20% chance of $0), or $6,000 for sure?
> *A 100% guarantee of gaining $6,000 · An 80% chance of gaining $8,000 (20% chance of $0)*

## How it was measured
For each effect, the analysis takes the share choosing the key option in one version minus the other, for people and for Jev. It also checks, on the 6 choices where the two options have different averages, how often each side's majority picks the option that pays more on average.

## Caveats
- **Hypothetical money.** Nobody in the study won or lost real money, and neither did Jev. That's standard for these problems, but choices with real stakes can differ.
- **Jev reading numbers.** Every problem is a comparison of percentages and dollar amounts. Reading and weighing raw numbers is a limit TypeSafe already documents for Jev, so part of any gap may be arithmetic rather than attitude to risk.
- **Countries pooled.** The 19 countries are pooled into one "people" number. A single country's pattern could sit closer to or further from Jev's.
- **Textbook problems.** These are the original 1979 problems, discussed in countless economics courses. A model may have read that people "should" maximize expected value and answer that way, which is itself a finding about its advice, not necessarily about how it handles new risks.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
