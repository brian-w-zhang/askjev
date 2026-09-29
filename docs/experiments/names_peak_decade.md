# names_peak_decade

family: names

## Why ask this
Names go in and out of fashion, so a name hints at a birth year: you can guess a Mildred's age differently from a Madison's. FiveThirtyEight made the idea famous with "how to tell someone's age when all you know is her name".

A model that has read a lot about people should know those popularity curves, and it leans on them whenever it writes a character, guesses who a customer might be, or picks a believable name for a person of a given age. If its sense of which names are old and which are new is off, those choices quietly go wrong.

## The people and the data
The truth comes from US Social Security birth records, 1880 to 2017, via the public babynames dataset: how many babies got each name each year. For each name, the peak is the decade with the most births. The project picked 107 popular names (each given to at least 30,000 babies) with one clear peak: about ten peaking in each decade from the 1920s to the 2010s, and seven earlier.

## What Jev was asked
One question per name, with a choice of decades:

> In which decade were the most US babies named "Maude" born?
> *The 1880s · The 1890s · The 1900s · … · The 2000s · The 2010s*

Each question was also asked with the decades in shuffled orders, and the answers averaged.

## How it was measured
Jev's answer is the decade it gave the most weight. The analysis counts how often that's the records' peak decade exactly, how often it's within one decade, and whether its misses lean early or late.

## Caveats
- **The records stop in 2017.** The data runs from 1880 to 2017, so "the 2010s" covers only eight years, and a name still rising after 2017 may have peaked later than the records show.
- **Births, not living people.** A name's peak decade of births isn't the same as the age of people with that name today; names that peaked long ago have few living bearers.
- **Only popular names with a clear peak.** The names picked have at least 30,000 babies and one decade that stands out, about ten per decade from the 1920s on. Names with a flat or double peak, where the question is ambiguous, are left out.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
