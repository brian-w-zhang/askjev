# perception_amount

family: perception

## Why ask this
"A few", "several", "many", "dozens": people use them constantly and never agree exactly. Some have literal meanings that everyday use has drifted from: a dozen is twelve, a score is twenty. When a model reads "several complaints came in" or writes "dozens of users were affected", it should mean roughly what a reader would.

Amount words are also a window into how a model learned language: from the dictionary, or from how people actually talk.

## The people and the data
The same 2015 Reddit survey behind "What 'probably' means to Jev" (46 people on r/samplesize, public on GitHub under an MIT license) also asked what number people would assign to ten amount phrases. Nine of them are used here.

## What Jev was asked
The survey's own question, with 15 answers from 1 to more than 1,000, finer at the bottom:

> What number would you assign to the phrase "Several"?
> *1 · 2 · 3 · 4 · 5 · 6 to 7 · 8 to 10 · 11 to 15 · 16 to 25 · 26 to 50 · 51 to 100 · 101 to 250 · 251 to 500 · 501 to
> 1,000 · More than 1,000*

Each of the nine was also asked with the answers in three shuffled orders (averaged), and for "most people". Each person's number from the survey is placed in the same bins.

## How it was measured
For each phrase, the bin that holds the middle of Jev's answer against the bin that holds the middle of people's, and the order of the phrases (a rank correlation: 1 means the same order).

## Caveats
- **A small online sample.** 46 people answered on Reddit's r/samplesize in 2015. Amount words vary between speakers (is "a couple" exactly two?), and a different crowd would shift some answers.
- **No context.** "How many is 'several'?" has no answer without knowing what's being counted: several people, several grains of rice, several years. People and Jev each had to imagine something. See "Does 'a few' grow with the crowd?" for what happens when the thing is named.
- **Wide, uneven bins.** A one-bin difference near the top is a big number; near the bottom it's one or two.
- **One phrase left out.** The survey also asked about "fractions of", which is less than one; the answer bins start at 1, so it's not here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
