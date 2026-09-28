# knowledge_hidden_step_no

family: knowledge

## Why ask this
Some yes/no questions can be answered by recalling one fact ("Is East Timor the same as Timor-Leste?"). Others need a chain the question doesn't spell out ("Is chaff produced by hydropower?" needs knowing what chaff is and where it comes from). When the chain gets hard, a model can guess, or it can fall back on one answer. Which way it falls back is a habit worth knowing.

## The people and the data
StrategyQA (Geva et al. 2021; MIT) is 2,290 yes/no questions written so that each needs an implicit chain of facts; 1,923 are used here. For comparison, BoolQ and Natural Questions are yes/no questions about a single fact.

## What Jev was asked
Each as a single yes/no question:

> Would Dave Chappelle pray over a Quran?

## How it was measured


## Caveats
- **Yes/no answers are their own format.** TypeSafe documents that Jev's yes/no answers aren't directly comparable with its multiple-choice answers. All comparisons here stay within yes/no questions.
- **Questions without their passage.** BoolQ and Natural Questions come with a passage that contains the answer. They were asked without it, so they test memory, like the StrategyQA questions.
- **StrategyQA's own keys.** Some StrategyQA answers rest on an arguable chain of facts ("would Dave Chappelle pray over a Quran?"). A few "misses" are disagreements with the key.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
