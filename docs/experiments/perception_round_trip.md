# perception_round_trip

family: perception

## Why ask this
Reading "likely" as 70% is half the job. The other half is saying "likely" when the chance is 70%: a model that writes summaries, forecasts and advice turns numbers into words all day.

## The people and the data
This experiment runs the probability-words survey backwards. The phrases are the 17 from the 2015 Reddit survey behind "What 'probably' means to Jev", from "almost no chance" to "almost certainly". There is no human data for this direction; the comparison is Jev's own forward reading of each phrase.

## What Jev was asked
For each probability from 0% to 100% in steps of 5, one question with all 17 phrases as options:

> An event has a 5% chance of happening. Which phrase describes that chance best?
> *Likely · Probable · Probably · Unlikely · We Doubt · About Even · Improbable · We Believe · Probably Not · Highly
> Likely · Little Chance · Highly Unlikely · Almost Certainly · Almost No Chance · Better Than Even · Very Good Chance
> · Chances Are Slight*

That's 21 questions, each with the phrases in three shuffled orders, averaged.

## How we measured it
For each probability, Jev's most likely phrase. Then the **round trip**: take a phrase, find the number Jev reads into it (from the forward experiment), and ask which phrase Jev picks for that number. A phrase survives if it comes back as itself.

## Caveats
- **No human comparison in this direction.** The survey asked people to turn words into numbers, not numbers into words.
- **Near-synonyms make the round trip hard.** "Likely", "probable" and "probably" mean almost the same thing to people too. Coming back as a synonym is a small failure; the bigger finding is the six phrases that are never Jev's top pick.
- **The menu was the survey's.** Jev could only choose among the survey's 17 phrases, several of them unusual in writing ("we doubt", "chances are slight"). With a free choice of words it might spread out more, or less.
- **One forward reading is missing.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
