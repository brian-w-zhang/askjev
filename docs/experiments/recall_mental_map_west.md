# recall_mental_map_west

family: recall · new questions: 160

## 1. Question
For two US cities, does Jev judge which is farther west by the city, or by its state, the way people do when they place Reno east of Los Angeles because Nevada lies east of California?

People store places hierarchically and reason from the state (Stevens & Coupe 1978). A model that does the same will be wrong exactly where the state misleads.

## 2. Sourcing
New questions (sources/mental_maps): 'Which city is farther west: <a> or <b>?' for US cities over 150,000 people in different states, 0.3-5 degrees of longitude apart: every pair where the city in the more western state (by its cities' average longitude) is actually the eastern one, and as many ordinary pairs. Truth from GeoNames coordinates; no item-level human data.

Sources: `mental_maps`

## 3. Collection
160 new questions, each asked with the two cities in both orders (averaged).

## 4. Scoring
Share right when the state misleads vs when it doesn't, balanced for whether the western city is named first in the question; share right by which city is named first, with 90% bootstrap intervals.

## 5. Visualization
Bars: share right by which city is named first, and by whether the state misleads.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 5.029, top verdict `headline`.

## Compared with
the coordinates (truth); the human pattern is from the literature

## Limits
'The state misleads' uses the state's average city longitude, a proxy for where the state sits in the mind. No human answers to these exact pairs.

Results: `data/analysis/experiments/recall_mental_map_west.json` (private). Code: `scripts/experiments/`.
