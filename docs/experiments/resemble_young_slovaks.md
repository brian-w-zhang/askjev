# resemble_young_slovaks

family: resemble

## Why ask this
Most comparisons between AI models and people use opinion polls. This one uses a single real survey of ordinary life, with hundreds of questions nobody would put in a poll: how afraid are you of spiders, how much do you enjoy swing and jazz, do you save money, do you lie. The questions where Jev is sure and people aren't show what kind of "person" it presents.

## The people and the data
The Young People Survey (Miroslav Sabo, published on Kaggle in 2016, public domain): 1,010 people aged 15 to 30, surveyed in 2013 by students at Comenius University in Bratislava, answering about 150 items about music, films, hobbies, fears, health habits, personality and spending. Each question here comes with the share of respondents at each answer.

## What Jev was asked
The survey's questions, as Choice or five-level ratings:

> Do you lie to others?
> *I never lie · I sometimes lie · Only to avoid hurting someone · Every time it suits me*

## How we measured it
We also list the questions where Jev's top answer is furthest from what they chose.

## Caveats
- **One small, specific group.** About a thousand people aged 15 to 30, surveyed in Slovakia in 2013 by students of Comenius University in Bratislava. It's one country, one age group and one year, not a national sample.
- **Translated.** The survey was run in Slovak and published in English; the wording Jev saw is the English version, with its typos fixed.
- **A virtuous self-image.** Jev's biggest breaks are all questions about honesty and conduct (lying, cheating). Its answers there are what a model tuned to be honest would say about itself, which says more about its self-presentation than its habits.
- **Nothing to compare the score with.** It's comparable only loosely with the other resemblance experiments, which use different questions.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
