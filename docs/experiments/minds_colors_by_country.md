# minds_colors_by_country

family: minds

## Why ask this
Most color-feeling links are shared worldwide, but the details differ from country to country. Which country's details a model reproduces is a small test of whose culture its defaults come from.

Text on the internet is heavily English, so a model's associations might lean English-speaking even for something as basic as the color of relief. That lean would show up quietly in design advice, marketing copy or a story set in another country, where the "obvious" color for grief or love isn't the local one.

## The people and the data
For each of 20 feelings, every country has its own shares of how often the feeling was linked to each of 12 color terms. The participants were volunteers, not national samples.

## What Jev was asked
No new questions: this reuses Jev's answers to the 20 questions "Which color do you associate most with the feeling ...?" from the colors-of-feelings experiment, and compares them with each country's answers.

## How it was measured
For each country and each feeling, how similar Jev's colors are to that country's (a similarity score from 0 to 1, where 1 means identical shares), averaged over the 20 feelings. The analysis also estimates how much each country's score could move by chance (a 90% interval) to see which differences are real.

## Caveats
- **Small differences.** Countries mostly agree on colors and feelings, so the gaps between them are small. The top of the list is suggestive, not a clear ranking: more than half the countries can't be told apart from the leader.
- **Uneven country samples.** Some countries have several hundred participants, others under a hundred, and none is a national sample.
- **One pick versus many.** The similarity compares a sharp answer with a spread-out one, which keeps every score low.
- **English prompts.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
