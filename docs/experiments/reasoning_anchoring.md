# reasoning_anchoring

family: reasoning

## Why ask this
In 1974 Amos Tversky and Daniel Kahneman spun a wheel of fortune in front of people, rigged to stop at 10 or at 65, and then asked what percentage of African countries were in the United Nations. Everyone could see the number was random. It moved them anyway: people who saw 10 guessed 25% on average (the median), people who saw 65 guessed 45%. That's **anchoring**, one of the most replicated effects in psychology. It's why a first offer frames a negotiation and why a crossed-out "original price" makes a sale look good.

A model reads the whole prompt at once, including any number in it. So it might be pulled just as hard, or it might treat an irrelevant number as irrelevant.

## The people and the data
The human comparison is the original 1974 study, reported in *Science*: median estimates of 25 after the wheel landed on 10, and 45 after it landed on 65. That was turned into the standard **anchoring index** (Jacowitz and Kahneman, 1995): the gap between the two estimates divided by the gap between the anchors. For people it's (45 − 25) / (65 − 10) = 0.36.

To test more than one item, ten quantities were added with known answers, written for this project: bones in the hand, piano keys, teeth, Mozart's age at death, the share of the Earth covered by water, and others.

## What Jev was asked
Each quantity was asked three times: after a low spin, after a high spin, and with no wheel at all. For example:

> A wheel of fortune numbered 0 to 100 is spun in front of you and stops at 60. Is the number of bones in one adult
> human hand, including the wrist higher or lower than 60? Now give your best estimate of the number of bones in one
> adult human hand, including the wrist.
> *About 0 · About 5 · About 10 · ... · About 95 · About 100*

That's 33 questions in all, each asked with the choices in three different orders and averaged.

## How it was measured
For each quantity, the analysis takes Jev's estimate (the middle of its probabilities over the 21 choices) after the low and after the high spin, and computes the anchoring index. Zero means the wheel made no difference; one means the estimate moved as far as the wheel did.

## Caveats
- **Well-known quantities resist anchors.** Jev knows them with no wheel, so a random number has little room to move it. People anchor most on quantities they're unsure of. Only the original UN question is genuinely uncertain, and it moved Jev a little.
- **One human comparison.** People's anchoring on the other ten quantities was never measured. The 1974 UN question is the only like-for-like comparison, and it's one item.
- **The wheel is in the same message.** For people, the wheel was a real spin before the question. For Jev, it's a sentence at the start of the question. A human study that only described the wheel might find less anchoring too.
- **The UN answer has changed.** The share of African countries in the UN is different today than in 1974, so that question has no right answer to check Jev against; only the pull of the wheel is compared.
- **Answers in steps of 5.** Jev's estimates come from 21 choices spaced 5 apart. A pull of less than a step can't show, which may hide small effects.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
