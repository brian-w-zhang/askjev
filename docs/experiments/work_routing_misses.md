# work_routing_misses

family: work

## 1. Question
When Jev sends a customer message to the wrong intent, how wrong is it: a neighbor of the right intent, or somewhere else entirely, and does a longer list of intents make it worse?

Routing is TypeSafe's bread-and-butter use case. A miss between 'order a physical card' and 'get a physical card' costs little; a miss to an unrelated team costs a lot, and a right answer in second place means a two-choice fallback would recover it.

## 2. Sourcing
Existing intent and topic routing questions from 13 public datasets (banking, assistants, complaints, support flows, tools, task types) with 7 to 77 options each. Enough: ~30,000 questions.

Sources: `banking77`, `hwu64_intents`, `massive_en`, `clinc150`, `snips_intents`, `multiwoz_domain`, `sgd_dialogue`, `cfpb_complaints`, `abcd_flows`, `airline_complaints`, `skill_select`, `math_routing`, `dolly_tasks`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per dataset: share right; among misses, the share where the right intent was Jev's second choice; the most frequent confusions. Across datasets, rank correlation between the number of options and the share right.

## 5. Visualization
Paired bars per dataset (ordered by number of options): share right, and the share of misses where the answer was second choice; the top confusions as labels.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.588, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
Datasets differ in how distinct their intents are; some labels are ambiguous (e.g. 'brainstorming' vs 'open question' in the Dolly task types).

Results: `data/analysis/experiments/work_routing_misses.json` (private). Code: `scripts/experiments/`.
