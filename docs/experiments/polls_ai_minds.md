# polls_ai_minds

family: polls

## Why ask this
Whether AIs can think, feel or have wants of their own is one of the few questions where a model is both the subject and a witness. People's answers vary widely, and they're tracked every year by a survey built for exactly this.

So how does an AI answer questions about AI minds, compared with the public? Does it claim more for itself, or less?

## The people and the data
The **Artificial Intelligence, Morality, and Sentience (AIMS) survey** by the Sentience Institute: preregistered surveys of about 1,100 to 1,200 US adults per year, weighted to match the US census. We use the items about AI minds from the 2021 and 2023 waves and a 2023 supplement, about 30 items; attitude, policy and development-pace items are left out.

## What Jev was asked
The survey items as asked, with their answer scales. For example:

> To what extent did the robots and AIs that existed in 2021 have the capacity for experiencing emotions?
> *They have none of this capacity · They have a little of this capacity · They have a moderate amount of this
> capacity · They have a lot of this capacity · They fully have this capacity*

## How we measured it
We group the items into four kinds: feelings and experience today, thinking and reasoning today, having a will of its own, and whether AIs could ever be sentient. For each group, we compare the share of Jev's answer and of Americans' answers on the lowest option ("none", "no", "very unlikely").

## Caveats
- **An AI answering about AI.** Jev's answers about AI minds may reflect how models are trained to talk about themselves as much as any view it holds. That's part of the point, but it isn't a neutral witness.
- **Groups by keyword.** We sorted the survey's items into four groups (feelings, thinking, will, future sentience) by their wording. The "will of its own" group has only two items, so treat that number as rough.
- **Questions about past years.** Many items ask about "the robots and AIs that existed in 2021" or 2023. Jev answers about systems it may know only partly, and Americans answered at the time.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
