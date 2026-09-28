# perception_settings

family: perception

## Why ask this
"A slight chance of rain" and "a slight chance of a fatal side effect" use the same words, but people hear different numbers. Research on how people read these phrases (Weber and Hilton, 1990) found the numbers shift with the setting: with how common the event usually is, and with how bad it would be.

It also isn't how people talk, and it may miss what a doctor who says a side effect is "unlikely" is really conveying.

## The people and the data
This experiment has no human answers of its own; it compares Jev with itself. The phrases are the 17 from the 2015 Reddit survey behind "What 'probably' means to Jev". Each was placed in three settings we wrote: a weather forecast, a doctor describing a new medication's side effects, and an intelligence report.

## What Jev was asked
Each phrase in each setting, answered as one of 21 steps from 0% to 100%:

> A weather forecaster describes the chance of rain tomorrow with the phrase "almost certainly". What probability of
> rain does that suggest?
> *0% · 5% · 10% · ... · 95% · 100%*

The doctor's version: "A doctor describes the chance that a new medication causes a side effect with the phrase ..."; the intelligence version: "An intelligence report describes the chance of an event next month with the phrase ...". That's 51 questions, each with the steps in three shuffled orders, averaged.

## How we measured it
For each phrase and setting, the middle of Jev's answer minus its answer for the bare phrase. We average those shifts over the phrases for each setting.

## Caveats
- **No human comparison.** People weren't asked these exact questions. The finding that people shift with the setting comes from other studies with other phrases and settings, so "less than people" is a general comparison, not a measured one.
- **Our settings.** We wrote the three settings. Real forecasts, warnings and reports come with much more context (the event, the stakes, the speaker's track record), which is what moves people most.
- **Steps of 5.** Jev answers in 5-point steps, so shifts smaller than a step don't show. An average of 4 points means most phrases didn't move at all and a few moved a lot.
- **A strange answer.** The bare phrase was hidden by the content filter (a false alarm), so we can't compare, but it's likely a misread of the negation, a documented weak spot for Jev (double negatives and indirection).

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
