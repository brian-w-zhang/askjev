# numbers_crowd_wisdom

family: numbers

## Why ask this
The wisdom of crowds says that the median of many independent guesses beats almost every individual guesser: ask 500 people how far Houston is from Atlanta and the middle answer is closer than most of them. A language model has read what everyone has written. Is it one more guesser, or already a crowd?

## The people and the data
A large 2019 study by Simoiu and colleagues at Stanford, which ran estimation questions on about 500 people each in February 2017 (public data, MIT license). We use its eight text-only domains, 20 questions each: celebrities' ages, distances between US cities, dates in US history, GDP per person, how many of one country fit into the continental US, calories in foods, appliance wattage and country populations.

## What Jev was asked
Each question as the study asked it, with ordered answer ranges fixed per domain:

> How many Kenyas fit into the continental U.S.?
> *Under 1.5 · 1.5 to 3 · 3 to 5 · 5 to 8 · 8 to 12 · 12 to 20 · 20 to 30 · 30 to 50 · 50 to 80 · 80 to 150 · 150 to 300 ·
> 300 or more*

(The answer is in the 12 to 20 range. Jev's middle answer fell lower, in 3 to 5; the crowd's most common range was 5 to 8.) That's 160 new questions, each asked with the ranges in three shuffled orders and averaged.

## How we measured it
Per domain and overall: how often Jev's middle answer is the right range, how often the crowd's median guess is, and how often an individual person's guess is (the typical person). We also measure how many ranges off each is.

## Caveats
- **Knowing vs estimating.** For people these were estimates; for Jev many are facts it has read (a country's population, a celebrity's birth year). Beating the crowd there is closer to recall than to judgment.
- **A pinned date.** People answered in February 2017. Questions that depend on the date (ages, populations, GDP) are pinned to 2016 or February 2017 in the wording, and Jev has to answer as of then.
- **Ranges, not numbers.** Every answer, people's and Jev's, is put into fixed ranges per domain (about 20-50% wide), so "right" means the right range.
- **Who guessed.** The guessers were about 500 US online participants per question, recruited for the study, not a national sample.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
