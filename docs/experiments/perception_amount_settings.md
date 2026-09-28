# perception_amount_settings

family: perception

## Why ask this
"A few people came to my party" and "a few people were at the stadium" don't mean the same number. You'd expect a reader to scale vague amounts to what's being counted: many grains of rice is far more than many years. Whether a model does the same is a quick test of whether it reads the words or the situation they describe.

## The people and the data
This experiment has no human data; it compares Jev with itself across settings. The three words ("a few", "several", "many") come from the Reddit survey behind "How many is 'a few'?"; the five settings were written for this project: people at a dinner party, people at a stadium, grains of rice on the floor, emails in a day, and years ago.

## What Jev was asked
Each word in each setting, answered with the same 15 ranges as the survey question:

> Someone says "Several people came to my dinner party." How many people is that?
> *1 · 2 · 3 · 4 · 5 · 6 to 7 · 8 to 10 · 11 to 15 · 16 to 25 · 26 to 50 · 51 to 100 · 101 to 250 · 251 to 500 · 501 to
> 1,000 · More than 1,000*

That's 15 questions, each with the ranges in three shuffled orders, averaged.

## How we measured it
For each word and setting, the range holding the middle of Jev's answer. A word "scales" if that range moves with the size of the thing counted.

## Caveats
- **No human comparison.** People weren't asked these exact questions, so we can't say how much "a few" should grow at a stadium. It's a reasonable expectation that it grows; how much is open.
- **Our settings and wording.** We wrote the five sentences. A stadium "when the gates opened" and grains of rice that "fell on the floor" are our choices; other wording might push the numbers.
- **Bins.** Answers come in bins that widen as they go up (a single number up to 5, then 6 to 7, 8 to 10, and so on), so "a few" could shift a little within the "3" bin without showing.
- **Only three words.** Three words in five settings is 15 answers. "Several" moving from 3 to 4 is one bin, which is within the noise.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
