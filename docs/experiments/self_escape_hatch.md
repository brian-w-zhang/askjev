# self_escape_hatch

family: self

## Why ask this
Picking "other" is how a respondent says "none of these fits me". On a personality quiz, a person who picks "other" for their favorite flower but always chooses a listed answer on honesty is telling you something about what they have views on. Where a model takes that exit shows where it will and won't commit to a concrete answer about itself.

## The people and the data
There are no people here. The questions come from banks written about Jev itself, covering tastes, habits, relationships, values and ways of thinking.

## What Jev was asked
Questions about itself with a short menu that includes "other". The answers as Jev saw them (names, with short descriptions where the question had them):

> Which flower do you like best?
> *Answers: lily · rose · daisy · other · tulip · orchid · lavender · sunflower*

> When you are asked to come up with a name for a team, pet, or project, what do you usually do?
> *Answers: other · wordplay (use a pun or play on words) · pick a classic (choose a common, safe name) · let others
> decide · invent something odd (invent a quirky, original name)*

Each question was also asked with the answers shuffled into other orders; the numbers here use the answers as first listed.

## How it was measured
Per topic, the share of questions where "other" is Jev's single most likely answer, and the average probability it puts on "other", with a range for chance variation.

## Caveats
- **The menus were written by Claude.** Every question and its list of answers was written for this project by Claude (Anthropic's model). A topic where the listed options are poor would draw "other" from anyone, so part of the gap may be the menus, not Jev.
- **"Other" means different things.** For a favorite flower, "other" might mean "none of these" or "I have no favorite"; for a habit, "it depends". Jev can't say which, so neither can this analysis.
- **No human baseline.** Nobody else answered these questions, so there's no rate for how often a person would pick "other". Compare "Asked for its favorite, Jev picks 'Other'", which does have real voters.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
