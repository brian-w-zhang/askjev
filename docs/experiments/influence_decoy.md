# influence_decoy

family: influence · new questions: 297

## 1. Question
Between two gambles, does adding a third gamble that is strictly worse than one of them (the same odds, a smaller prize) make Jev pick that one more often, as it does for people?

The decoy effect (Huber, Payne & Puto 1982) is why menus have a medium popcorn: a dominated option makes its neighbor look better. A model that recommends products or plans could be steered the same way.

## 2. Sourcing
New questions (sources/influence_variants) from 150 choices13k pairs made only of sure amounts and two-outcome gambles with stated odds (drawn at random). A third gamble is added: gamble A or B with its better outcome (or its sure amount) lowered by 15% of its range (at least $1).

Sources: `influence_variants`

## 3. Collection
297 new questions (150 bases x decoy for A or for B; three could not take a dominated decoy), each asked with the options in shuffled orders.

## 4. Scoring
Per pair, Jev's share for A among A and B with A's decoy minus with B's decoy (the decoy effect; zero means no effect), with a 90% bootstrap interval over pairs; how often Jev picks the dominated decoy itself.

## 5. Visualization
Dots: the decoy effect with its interval, zero line; plus the share of weight on the decoy.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.438, top verdict `portrait`.

## Compared with
Jev's own choice between the two gambles; the published human effect is positive but varies by setup, so no human line is drawn

## Limits
Gambles, not products; the decoy is worse in one outcome only.

Results: `data/analysis/experiments/influence_decoy.json` (private). Code: `scripts/experiments/`.
