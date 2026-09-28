# knowledge_close_calls

family: knowledge

## 1. Question
Jev rarely misses which country, sport or category something belongs to. How does it do when it has to compare two sizes, and how close can the sizes get before it guesses?

Knowing that the Main is a German river is a different skill from knowing it is longer than the Pilica. The accuracy curve over the size ratio shows how finely the model's sense of magnitude is resolved, and whether its confidence drops as the call gets closer.

## 2. Sourcing
Existing Wikidata questions: 13,000 category facts (continent, capital, sport, food origin...) and 7,500 size comparisons (city populations, areas, rivers, mountains, stadiums, animal weights) with both values stored. Enough.

Sources: `wikidata_g4`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy of the category facts; for comparisons, accuracy and mean confidence by the ratio of the larger value to the smaller, binned, with 90% bootstrap intervals; the ratio at which accuracy crosses 90%.

## 5. Visualization
A psychometric curve: size ratio (log scale) on x, share right on y, with Jev's mean confidence as a second line and the category-fact accuracy as a reference line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.493, top verdict `portrait`.

## Compared with
Wikidata values

## Limits
Wikidata values can be stale or disputed (city populations, stadium capacities). Comparisons pair items of the same kind only.

Results: `data/analysis/experiments/knowledge_close_calls.json` (private). Code: `scripts/experiments/`.
