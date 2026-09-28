# knowledge_what_came_first

family: knowledge

## 1. Question
Asked which of two things came first (games, software, companies, memes, historical events), how close in time can they be before Jev loses track, and does that depend on what they are?

Knowing roughly when things happened is a sign of how densely a kind of thing is covered in what the model learned. Holding the gap in years fixed shows which worlds it knows in fine detail.

## 2. Sourcing
Existing Wikidata 'which came first' questions with both years stored: video games, software and products, companies, historical states and events, births, and internet memes. Enough: 9,000 pairs.

Sources: `wikidata_g4`, `wikidata_memes`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy by the gap in years (binned), and, for pairs 1-5 years apart, accuracy per kind of thing with 90% bootstrap intervals.

## 5. Visualization
Dots: accuracy on close pairs (1-5 years apart) per kind of thing, with the overall curve by gap as an inset.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.621, top verdict `portrait`.

## Compared with
Wikidata dates (release, founding, inception)

## Limits
TypeSafe documents weak date comparison (01-jev.md §6.3) when dates are given in the question; here the dates are recalled, not given, so this measures memory of when things happened. Wikidata dates can be disputed for memes and old states.

Results: `data/analysis/experiments/knowledge_what_came_first.json` (private). Code: `scripts/experiments/`.
