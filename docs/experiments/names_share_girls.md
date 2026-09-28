# names_share_girls

family: names

## Why ask this
A first name carries information people use without thinking. A model that writes about people, or reads about them, does the same. For names given to both boys and girls, the question is whether it knows how mixed a name really is, or flattens it into "a boy's name" and "a girl's name".

## The people and the data
The truth comes from US Social Security birth records, 1880 to 2017, via the public babynames dataset: for every name given to five or more babies in a year, how many were recorded as boys and as girls. We chose 60 names with mixed records (between 10% and 90% girls, and at least 20,000 babies), plus 40 names that are clearly one or the other, as a check.

## What Jev was asked
One question per name, with eleven answers from "Under 5%" to "Over 95%" in 10-point steps:

> Of all the babies born in the US and named "Dee" since 1880, what share were recorded as girls?
> *Under 5% · 5-15% · 15-25% · 25-35% · 35-45% · 45-55% · 55-65% · 65-75% · 75-85% · 85-95% · Over 95%*

Each question was also asked with the answers in shuffled orders, and the answers averaged.

## How we measured it
Jev's estimate is the average of the bins it chose, weighted by its probabilities, using each bin's middle.

## Caveats
- **All-time records, not today.** The question asks about every baby since 1880, and names change sides over time. If Jev answers for how a name is used today, or reads Ollie and Robbie as nicknames for Oliver and Robert, it will miss the records' long history, which may explain its biggest misses.
- **Sex recorded at birth.** US Social Security records count sex recorded at birth, and only names given to five or more babies in a year. They say nothing about anyone's identity, and the question says "recorded as girls" for that reason.
- **Answers in bins.** We turn its answer into one number using the middle of each bin, which rounds a little toward the middle for the lowest and highest bins.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
