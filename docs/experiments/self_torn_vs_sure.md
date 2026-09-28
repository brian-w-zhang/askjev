# self_torn_vs_sure

family: self

## Why ask this
With no right answer at stake, how firmly someone answers shows where they have settled views. Ask a person their favorite food and they'll answer at once; ask a hard ethical question and they'll hedge. A model might have it the other way around: rehearsed on how to behave, blank on what it likes.

## The people and the data
There are no people here. The questions come from banks written for this project about Jev itself (its personality, habits, relationships, tastes, values and way of thinking), grouped by topic on our question map.

## What Jev was asked
Questions about itself, in the second person, for example:

> Which describes how you'd react to a newly opened road?
> *Answers: use it · wonder what it will change*

> Do you think the fear of death gets smaller with age? *(yes/no)*

Every question was also asked the other way round, "what would most people say?", so the same measure can be taken for Jev's picture of people.

## How we measured it
For each answer, how far Jev's top choice is above an even split, scaled so 0 is a coin toss and 1 is certain.

## Caveats
- **The questions were written by Claude.** Every question here was written for this project by Claude (Anthropic's model), topic by topic, and checked by Jev for clarity. That makes the topics comparable, but it also means the questions reflect how one model imagines a personality quiz. A topic can look "torn" partly because its questions were harder to answer cleanly.
- **Sure isn't right.** There's no right answer to "which would you pick?", so this measures how committed Jev is, not whether it's correct. A confident answer about its dark side is a stance, not a fact.
- **Topics come from our map.** Topics are branches of this project's question map, each with at least 500 questions, so their boundaries are ours, and some mix very different questions.
- **Two kinds of questions pooled.** Yes/no questions and two-or-more-option picks are pooled after rescaling confidence so a coin toss is 0 for each. A pick among five options and a yes/no aren't perfectly comparable.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
