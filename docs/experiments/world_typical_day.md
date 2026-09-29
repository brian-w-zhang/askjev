# world_typical_day

family: world

## Why ask this
Time-use diaries are the least flattering mirror of daily life. On a random day, most Americans don't work, most don't exercise, and TV takes more time than anything but sleep and work. Ask people what their day looks like and you get something closer to the brochure.

A model asked to picture "a day" has read a lot of brochures. Does it know the diary?

## The people and the data
The American Time Use Survey, run by the Bureau of Labor Statistics: Americans aged 15 and older record everything they did on one day, minute by minute. The comparison uses 181,335 diary days from 2003 to 2016 (public domain), weighted to represent the population, and for each of 20 activities the share of days falling in each time bin.

## What Jev was asked
One question per activity, framed exactly as the diaries measure it:

> Pick an American aged 15 or older at random, on a random day of the year. How much time did they spend relaxing and
> thinking, doing nothing in particular that day?
> *None at all · 1 to 29 minutes · 30 to 59 minutes · 1 to 2 hours · 2 to 3 hours · 3 to 5 hours · 5 to 8 hours · 8
> to 10 hours · 10 hours or more*

(In the diaries, 80% of days have none.) There was one such question for each of the 20 activities, each asked with the bins in shuffled orders and averaged.

## How it was measured
For each activity, the share of days Jev says have none of it against the diaries', and the average minutes (from the middle of each bin) against the diaries' weighted average. The analysis also checks how well Jev orders the activities by time spent (rank correlation: 1 same order, 0 no relation).

## Caveats
- **Narrow diary categories.** The diaries code each stretch of time as one main activity. "Relaxing and thinking" and "phone calls, mail and email" count only time coded as exactly that, so they're small in the diaries. Jev likely read them more broadly, which inflates the gap for those two.
- **The diaries are old.** They cover 2003 to 2016. Screen time has grown since, so Jev's higher computer figure is partly the world changing, not only Jev being wrong.
- **Coarse answers.** The share of days at zero is exact.
- **The question is about one day.** "A random American on a random day" includes weekends, holidays and people who don't work. That's the diaries' whole point, and where a picture of a typical weekday goes wrong.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
