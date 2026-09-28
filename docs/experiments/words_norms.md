# words_norms

family: words

## Why ask this
Psychologists measure what words mean to people beyond their dictionary definitions: how pleasant a word feels, how exciting, how concrete, how big the thing it names is, how early children learn it, how familiar it is. These **word norms** are collected by asking many people to rate thousands of words, and they're used everywhere from memory research to building reading tests.

A language model learns words only from text. Where its ratings match people's, text carries that part of meaning; where they don't, something about how people experience words isn't written down.

## The people and the data
Two standard datasets:
- **The Glasgow Norms** (Scott and colleagues, 2019): 5,553 English words, each rated on nine dimensions by native English speakers from the University of Glasgow community, about 33 raters per word. The experiment uses six: pleasantness, excitement (arousal), age of learning, familiarity, size and imageability.
- **Brysbaert, Warriner and Kuperman's concreteness ratings** (2014), covering 39,954 English words on a scale from abstract to concrete.

## What Jev was asked
One question per word and dimension, with five described answers written for this project, for example:

> How calming or stirring does the word "link" feel to you?
> *Calming: it feels sleepy or soothing, like a quiet evening · Mostly calm: it stirs little, like an everyday
> object on a shelf · Neither: it is no more calming than stirring · Somewhat stirring: it raises interest or
> alertness, like good news or a warning sign · Intensely stirring: it jolts you awake, like danger, a thrill or a
> scream*

Each was also asked with the answers reversed, and the two are averaged.

## How it was measured
For each dimension, the analysis ranks the words by Jev's answer and by people's average, and compares the rankings (a rank correlation: 1 means the same order, 0 means no relation). Rankings make it possible to compare Jev's five described levels with people's numbered scales.

## Caveats
- **The project's wording, their scales.** People rated on numbered scales (1 to 9, 1 to 7, 1 to 5) with the studies' own instructions. The comparison uses rankings so the scales don't have to line up, but those examples can still lean an answer.
- **Averages only.** Jev is compared with each word's average rating. How much people disagreed about a word isn't used, so a word that splits people counts the same as one they agree on.
- **Two groups of raters.** Most dimensions come from the Glasgow Norms (native English speakers from the University of Glasgow community, about 33 per word); concreteness comes from a separate, much larger study. Different people, different years.
- **Common words.** The words are mostly familiar English words. Rare, technical or slang words may behave differently.
- **Some words hidden.** Words the content filter flagged as sexual, violent or political are hidden from the site and left out, which removes some of the most emotional words people rated.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
