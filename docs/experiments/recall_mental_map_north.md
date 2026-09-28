# recall_mental_map_north

family: recall · new questions: 362

## 1. Question
Asked which of two cities on different continents is farther north, does Jev share people's classic error of placing Europe too far south of North America?

People's mental maps line Europe up with the US (Rome level with Washington), when Europe actually sits well north (Friedman & Brown 2000). A model reads maps only through text; whether it inherits the human distortion is a small window on how it stores geography.

## 2. Sourcing
New questions (sources/mental_maps): 'Which city is farther north: <a> or <b>?' for well-known cities (over 1.5 million people, or national capitals), from GeoNames coordinates: European vs North American pairs 0.5-6 degrees apart, pairs across other regions, and US pairs as a control. Truth only: no item-level human answers exist for these pairs.

Sources: `mental_maps`

## 3. Collection
362 new questions, each asked with the two cities in both orders (averaged).

## 4. Scoring
For Europe-North America pairs, how often Jev picks the North American city, and the share right when the European city is the northern one vs when it isn't (the human error predicts misses when Europe is north); a check that this isn't a lean toward the city named first; US pairs as a control.

## 5. Visualization
Bars: share right per set, and for Europe-North America split by which side is north.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.659, top verdict `headline`.

## Compared with
the coordinates (truth); the human pattern is from the literature, not item-level data

## Limits
No human answers to these exact pairs, so the comparison with people is with the published pattern, not a rate. Cities are identified by name and country (US: state).

Results: `data/analysis/experiments/recall_mental_map_north.json` (private). Code: `scripts/experiments/`.
