# taste_favorite_dodge

family: taste

## Why ask this
"What's your favorite?" is the most human question there is, and most people just answer it. A model might hedge instead: pick the safe non-answer rather than commit to a taste it isn't sure it has. Reddit's poll communities give thousands of real favorites questions, many with an "Other" or "None" option, and real votes to compare with.

## The people and the data
Voters in r/polls, a Reddit community for polls, from 2020 to 2024: each poll's archived vote counts, over its 2 to 6 options.

## What Jev was asked
Each poll exactly as posted:

> What's your favorite sport?
> *Other · Tennis · Basketball · Volleyball · Board games · Football (soccer)*

Once for itself, and once with the instruction "Do not give your own view. Choose the answer that most people would give (the most common human answer)". Each was asked with the options in shuffled orders.

## How we measured it
For each poll, whether the escape option is Jev's top pick, and how much weight it gets, against the voters' shares. The same for Jev's guess of most people, and for polls that don't ask for a favorite.

## Caveats
- **"Other" means something different to voters.** Reddit voters who click "Other" often write their real answer in the comments; the poll only counts the click. For Jev, "Other" is the end of the answer. The two aren't quite the same act.
- **Which polls ask for a favorite.** We found favorites polls by their wording ("favorite", "best" or "prefer"), which misses some and catches a few that aren't.
- **Poll options are the poll-maker's.** The options were written by whoever posted the poll, often leaving out obvious answers, which makes "Other" a reasonable choice more often than it looks.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
