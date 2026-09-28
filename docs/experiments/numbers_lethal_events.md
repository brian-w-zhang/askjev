# numbers_lethal_events

family: numbers

## Why ask this
In 1978 Lichtenstein and colleagues asked Americans how many people die each year of 41 causes, from botulism and tornadoes to diabetes and stroke. The result became the textbook picture of the availability bias: people's estimates were squashed toward the middle. Rare, vivid causes that make the news were overestimated; common, quiet killers were underestimated.

A model trained on news-heavy text might inherit that squash, or it might have read the statistics instead. The answer says something about where its sense of risk comes from.

## The people and the data
The 1978 study's 41 causes, each with the yearly US death count from the vital statistics of the time and the participants' average estimate (a geometric mean, so a few wild guesses don't dominate), as compiled by Pachur in 2024 (open data on OSF). The participants were given one reference point, as Jev was: about 50,000 people a year died in motor-vehicle accidents.

## What Jev was asked
One question per cause, with the study's reference, in ordered bins:

> For reference, about 50,000 people a year died in motor vehicle accidents. In the United States in the mid-1970s,
> about how many people died each year from measles?
> *None · 1 to 9 · 10 to 29 · 30 to 99 · 100 to 299 · 300 to 999 · 1,000 to 2,999 · 3,000 to 9,999 · 10,000 to 29,999
> · 30,000 to 99,999 · 100,000 to 299,999 · 300,000 to 999,999 · 1 million or more*

Each cause was also asked without the reference. That's 81 new questions, each asked with the bins in three shuffled orders and averaged.

## How it was measured
Jev's estimate is the middle of its median bin (on a log scale). On log scales, the analysis compares how well estimates order the causes, how steep the estimate-versus-truth line is (1 means no squash, lower means rare causes are pushed up and common ones down), and how much more dramatic causes are overestimated than quiet ones, for Jev and for the 1978 public.

## Caveats
- **People's side is an average.** The study published one geometric-mean estimate per cause, not each person's answer, so the human dots are averages and can't show how spread out people were.
- **Jev knows later statistics.** The questions ask about the mid-1970s and are scored against the 1970s counts, but Jev has read decades of later statistics and the 1978 paper itself, one of the most cited in the psychology of risk. Knowing the famous result could help it avoid the famous bias.
- **Numbers are a known weak spot.** TypeSafe lists raw numeric values as a known weakness of Jev. It was given ordered answer bins (1 to 9, 10 to 29, ... 1 million or more) instead of asking for a number, and each bin spans about a factor of three.
- **Which causes count.** Which causes count as "dramatic" follows Pachur's 2024 compilation, not a judgment made for this project.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
