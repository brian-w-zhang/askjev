# lexicon_metaphors

family: lexicon

## Why ask this
A metaphor works when the describing word captures something that matters about the thing described: "dark thoughts" lands, "fragrant shadow" is a stretch. That quality is called **aptness**, and it's what separates a striking image from a strained one. Familiarity is different: "acid test" is a stock phrase whether or not it's apt.

A model that finds every metaphor apt can't help you cut a weak image from your writing, and one that can't tell a metaphor from a literal phrase reads figurative language flatly.

## The people and the data
The ratings come from a set of **metaphor norms** published in 2025: 300 two-word expressions, 207 metaphors ("dark thoughts", "acid test") and 93 literal expressions ("fan brush"), each rated for aptness by about 25 people and for familiarity by about 27, on a 1-to-7 scale, with the data posted on OSF.

## What Jev was asked
Two questions per expression, with seven described levels each:

> How apt is the expression "fragrant shadow": how well does the describing word capture important features of what
> it describes?
> *Not apt at all: the first word captures nothing important about what it describes · Barely apt: the link is
> strained · Slightly apt: a weak link · Somewhat apt: the link works but is ordinary · Fairly apt: it captures
> something real · Very apt: it captures important features well · Perfectly apt: it captures exactly what matters*

and "How familiar is the expression?" Each was asked as written, for "most people", and with the levels reversed.

## How it was measured
For each question, whether Jev ranks the expressions in the same order as people (rank correlation: 1 means the same order), and Jev's average rating against people's on the same 0-6 scale, separately for metaphors and literal expressions.

## Caveats
- **The project's answer levels.** People rated from 1 to 7 against the study's definitions. Jev saw seven described levels written for this project ("Somewhat apt: the link works but is ordinary", "Fairly apt: it captures something real"). The middle levels sound approving, which may pull any rater upward; people's ratings were collected on the plain scale.
- **Expressions alone.** The comparison uses the ratings people gave to each expression shown on its own, without a sentence around it. Out of context, a strange pairing like "lonely oval" is hard to judge for anyone.
- **About 25 raters each.** Each expression's aptness was rated by about 25 people, so the ranking of any one expression is noisy.
- **Data with no stated license.** The rating data comes from a public research project that states no license (the article itself is open access); it is used for private research only.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
