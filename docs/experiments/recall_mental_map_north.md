# recall_mental_map_north

family: recall

## Why ask this
Is Rome north or south of New York? People tend to guess south; it's actually slightly north. People's mental maps line Europe up with the US, when Europe sits well to the north; the psychologists Friedman and Brown documented the pattern in 2000. A model knows maps only through text. Whether it inherits the human distortion, or the coordinates, is a small window on how it stores geography.

## The people and the data
The truth comes from coordinates in GeoNames, an open geographic database. There are no human answers to these pairs; the human side is the published pattern.

## What Jev was asked
> Which city is farther north: Ottawa, Canada or Munich, Germany?
> *Answers: Ottawa, Canada · Munich, Germany*

Each question was also asked with the two answers in the other order, and the answers averaged.

## How it was measured
The share of pairs Jev gets right in each set. For the Europe-North America pairs, how often it picks the North American city, and its accuracy split by which city is really farther north: the human error predicts misses exactly when Europe is north. A check that the lean isn't just a preference for the city named first.

## Caveats
- **No human answers to these pairs.** The comparison with people is with a published pattern (people imagine Europe well south of where it is, Friedman and Brown, 2000), not with people answering these exact questions. No item-level human data was found.
- **The pairs were chosen to test the error.** The pairs are European and North American cities 0.5 to 6 degrees of latitude apart, where the error bites. Two thirds of those pairs have Europe north. Across every possible pair the error would matter less.
- **"Well-known" by population.** Cities were chosen by size (over 1.5 million people, or national capitals over 300,000) from the GeoNames database, so some are less familiar to English speakers than others.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
