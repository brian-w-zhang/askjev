# polls_would_you_rather

family: polls

## Why ask this
Would-you-rather questions are pure preference: there's no right answer, only what people would pick. The site either.io has collected votes on thousands of them, often more than a million votes per question, which makes the crowd's answer about as stable as a preference ever gets.

Where Jev agrees with a million people, it has absorbed ordinary taste. Where it confidently disagrees, the disagreement is a small, plain look at its quirks.

## The people and the data
Would-you-rather questions from either.io with their vote counts, from a public scrape of the site.

## What Jev was asked
Each dilemma exactly as the site words its two options:

> Which would you rather?
> *Ride in a hot air balloon · Ride in a hovercraft*

## How we measured it
How often Jev's own pick matches the majority, and the same for its guess of most people. Then the questions where Jev's probability is furthest from the vote share, among questions where voters were clear (60% or more one way).

## Caveats
- **A game site's voters.** The votes come from either.io, a would-you-rather game site. Voters are self-selected, anonymous, and often voting for fun; the numbers are enormous but the crowd is not a sample of anyone in particular.
- **Only popular questions.** We kept questions with at least 1,000 votes (the median question has over a million), which are the site's most-played ones. Sexual items are hidden by the content filter and some were removed.
- **A copy of the site's data.** The data is a public scrape of either.io published on Kaggle, and we use it for private research only.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
