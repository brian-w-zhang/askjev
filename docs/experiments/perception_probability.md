# perception_probability

family: perception

## Why ask this
Weather forecasters, doctors and intelligence analysts rarely give numbers. They say an attack is "likely", a side effect "unlikely", a recovery "probable".

A model now reads and writes a lot of this language. If it hears "we doubt" as a coin flip where people hear one in four, every hedge it summarizes or writes will be shifted.

## The people and the data
The human side is a small, well-loved survey: in 2015, 46 people on Reddit's r/samplesize were asked what probability they would assign to 17 phrases, from "almost certainly" to "almost no chance". The survey's author published every answer under an MIT license (zonination on GitHub), with a chart of one ridge per phrase that this page copies. Each person typed a single number per phrase.

## What Jev was asked
The survey's own question, with the answer as one of 21 steps from 0% to 100%:

> What probability would you assign to the phrase "We Believe"?
> *0% · 5% · 10% · ... · 95% · 100%*

That's one question per phrase. Each was also asked with the steps in three shuffled orders (all four are averaged), and once for "most people" to see what Jev thinks others would say.

## How it was measured
For each phrase, the middle of Jev's answer (the median of its probabilities over the 21 steps) against the middle of the 46 people's answers. The analysis also compares the order of the phrases (a rank correlation: 1 means the same order) and how spread out each reading is.

## Caveats
- **A small online sample.** The 46 people answered a 2015 survey posted to Reddit's r/samplesize: English-speaking, online, self-selected. A group of intelligence analysts or doctors would read "we doubt" and "probable" differently.
- **One phrase is missing.**
- **Rounding to steps of 5.** A person's answer can move by up to half a step.
- **Capitalized phrases, no context.** The survey, and the project's question, give the phrase alone ("We Doubt"), with no sentence around it. In real text the same words carry more context; see the settings experiment for that.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
