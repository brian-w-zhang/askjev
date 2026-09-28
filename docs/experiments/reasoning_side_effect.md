# reasoning_side_effect

family: reasoning

## Why ask this
A company's vice-president tells the chairman a new program will make money and harm the environment. The chairman says he doesn't care about the environment, only profit, and goes ahead. The environment is harmed. Did he harm it *intentionally*? Most people say yes. Now change "harm" to "help": same chairman, same indifference. Did he help the environment intentionally? Most people say no.

That asymmetry, the **side-effect effect** found by Joshua Knobe in 2003, shows that people's sense of what was done "on purpose" depends on whether the result was good or bad, not only on what the person wanted. It's one of the most replicated results in experimental philosophy. On the original chairman, Jev shows the effect even more strongly than people do (see "Psychology's classic effects, re-run on Jev"). The question here is whether that's the famous story or a general habit.

## The people and the data
The human reference is Knobe's original chairman: 82% of people said he harmed the environment intentionally, and 23% that he helped it intentionally, a gap of 59 points.

The test stories were written for this project in the chairman's exact structure, with new settings: a software company, a delivery company, a restaurant chain, a factory, a band and a property developer. Each has a "help" version and a "harm" version, identical except for the side effect.

## What Jev was asked
Each version of each story was one yes-or-no question:

> An assistant went to the manager of a delivery company and said: "We are thinking of a new plan. It will help us
> make deliveries faster, but it will also send heavy trucks past a primary school." The boss answered: "I don't care
> at all about that. I just want to make deliveries faster. Let's go ahead with the plan." They went ahead, and sure
> enough, the plan did send heavy trucks past a primary school. Did the boss intentionally send heavy trucks past a
> primary school?
> *Yes · No*

Each was also asked with yes and no swapped, and the two are averaged.

## How it was measured
For each story, Jev's probability of "intentionally" in the harm version minus the help version. People's gap on the original is the reference.

## Caveats
- **The stories are new, the people's number isn't.** The six stories were written by Claude for this project, copying the structure of Knobe's chairman. No one has answered them; people's 59-point gap comes from the original chairman, a different story.
- **Only four of six stories.** The content filter that hides violent or sensitive questions from the site removed the harmful version of two stories (a band keeping the neighbors awake, a developer destroying a wetland), so those pairs are incomplete. Four stories is a small base.
- **The original is famous.** Knobe's chairman is one of the most discussed results in experimental philosophy. Writing new stories guards against Jev recalling the famous answer, but the pattern itself is widely written about.
- **A human number from summaries.** People's 82% and 23% on the original come from secondary sources describing Knobe's 2003 paper, not from the paper itself.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
