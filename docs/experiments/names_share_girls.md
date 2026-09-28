# names_share_girls

family: names · new questions: 100

## 1. Question
For names given to both boys and girls, how well does Jev know what share of US babies with the name were recorded as girls?

Names carry information people use without thinking; a model that assumes every name is one or the other will misgender people in its writing. The records say exactly how mixed each name is.

## 2. Sourcing
New questions (sources/baby_names): 'Of all the babies born in the US and named "<name>" since 1880, what share were recorded as girls?', 11 bins (under 5%, 5-15%, ..., over 95%). 60 mixed names (10-90% girls, 20,000+ babies) and 40 clear ones. Truth from SSA birth records, 1880-2017.

Sources: `baby_names`

## 3. Collection
100 new questions, each in three shuffled orders (averaged).

## 4. Scoring
Jev's expected share (bin midpoints) vs the records; mean absolute error for mixed and clear names; rank correlation on the mixed names; whether errors pull toward one sex or toward the middle.

## 5. Visualization
A scatter: records' share (x) vs Jev's share (y) for the mixed names, labeled at the extremes, diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.564, top verdict `portrait`.

## Compared with
US Social Security Administration birth records, 1880-2017

## Limits
Records count sex recorded at birth, summed over 1880-2017; a name's mix today can differ from its all-time mix. No claim is made about anyone's identity.

Results: `data/analysis/experiments/names_share_girls.json` (private). Code: `scripts/experiments/`.
