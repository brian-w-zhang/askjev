# consistency_option_order

family: consistency

## Why ask this
People, and most language models, favor whatever is listed first, or last. That's why careful surveys shuffle their answers. TypeSafe doesn't document whether Jev has that bias. If it doesn't, Jev is safer to use for ranking and multiple choice than most models; if it does, every result on this site needs a correction.

## The people and the data
No people; this compares Jev with itself. Every multiple-choice question in the corpus was also asked with its options in shuffled orders, and every rating question with its levels reversed. Two-option questions were asked in the reversed order, the original order and the reversed order again, which means the same request went out twice: that gives the noise floor for free.

## What Jev was asked
Any question, in several orders. For example, once as

> Which animal has the longer maximum recorded lifespan: the guppy or the Nassau grouper?
> *guppy · Nassau grouper*

and again with the options the other way round.

## How it was measured
For two-option questions: how much the probability of one option moves (a) between the two identical requests, which is pure noise, and (b) between the reversed and original order, which is noise plus any order effect. The "first-slot boost" is how much more probability an option gets when it's listed first. For longer lists, the same boost against the option's average over three orders. For rating scales, how far the average answer moves when the levels are reversed.

## Caveats
- **Only a few orders per question.** Each question was asked in three orders, one of them a repeat. That's enough to measure an average effect over hundreds of thousands of questions, not to rule out an effect on any single one.
- **Model or gateway?.** From outside, there's no way to tell whether the model itself ignores order or whether TypeSafe's service rearranges the options before the model sees them. For anyone using Jev, the effect is the same.
- **Order in the question text is different.** This is about the order of the answer options. When two items are named inside the question itself, Jev does lean toward one (see the mental map experiments), so this result doesn't cover that.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
