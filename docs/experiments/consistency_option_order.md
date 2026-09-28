# consistency_option_order

family: consistency

## 1. Question
When the same options are listed in a different order, or a rating scale is turned upside down, does Jev's answer move more than it does when the question is simply asked again?

People and most language models favor whatever is listed first (or last). TypeSafe doesn't document position bias either way (docs/01-jev.md §6 lists it as open ground); a model that ignores order is safer to use for ranking and multiple choice.

## 2. Sourcing
Every pick-one question in the corpus was also asked with its options shuffled three times; two-option questions were asked reversed, in the original order, and reversed again, so the same request was sent twice. Every rating question was also asked with its levels reversed. Enough: 214,000 two-option questions, 160,000+ questions with three to six options, 168,000 rating questions.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Two-option questions: the mean change in the probability of one option (a) between the two identical reversed probes (the noise of asking again) and (b) between reversed and original order (noise plus any order effect); the first-slot boost is how much more probability an option gets when it is listed first. Larger menus: the same boost for the first slot, against the option's average over three orders. Rating questions: the shift in Jev's expected level when the scale is reversed, as a share of the scale's length. 90% intervals by bootstrap over questions.

## 5. Visualization
Three bars in probability points: asked again in the same order, asked again against the base probe, options reversed; with the first-slot boost as a dot at zero.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.301, top verdict `portrait`.

## Compared with
Jev itself, asked the same request twice (the noise floor)

## Limits
Only three orderings per question, one of them a repeat. The noise floor comes from two-option questions only. From outside it can't be told whether the model itself ignores order or the gateway normalizes the options before the model sees them; for a user the effect is the same.

Results: `data/analysis/experiments/consistency_option_order.json` (private). Code: `scripts/experiments/`.
