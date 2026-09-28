# taste_vs_audience_anime

family: taste

## Why ask this
Anime fans rate a lot and argue about it more. Comparing Jev with MyAnimeList, the biggest fan database, shows whether a model's sense of good anime matches the people who watch it, and where it doesn't.

## The people and the data
MyAnimeList users, via a public dataset from 2016 of their 1-to-10 ratings. For each title we use the distribution of its ratings, set on the same five levels Jev answers on.

## What Jev was asked
Every title one at a time:

> How much would you enjoy watching Nogizaka Haruka no Himitsu (TV series)?
> *You'd give up on it early · You'd finish it but forget it within a week · You'd enjoy it once and not rewatch it ·
> You'd recommend it to a friend · You'd rewatch it and count it among your favorites*

Each was also asked with the answers reversed, and the two averaged. Jev never saw the MyAnimeList ratings.

## How we measured it
Ranks, because the scales differ.

## Caveats
- **Fans rate what they chose to watch.** MyAnimeList users rate shows they chose, and later seasons of a series are rated almost only by people who loved the earlier ones. That's likely why sixth seasons score so well with their audience.
- **Ratings squeezed into five levels.** MyAnimeList ratings run 1 to 10; we binned them onto our five described levels. We compare ranks, not levels.
- **A 2016 catalog.** The ratings come from a 2016 dataset of titles with at least 300 ratings, so recent anime isn't here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
