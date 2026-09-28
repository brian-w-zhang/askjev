# reasoning_traps

family: reasoning · new questions: 37

## 1. Question
Does Jev avoid the famous reasoning traps (Linda, the taxi cab, Monty Hall, the birthday problem, the gambler's fallacy, the bat and the ball), and does it still avoid them when the story and numbers are new?

The famous versions are all over the internet, so a model can pass them from memory. Isomorphs with new stories separate reasoning from recall, and controls where the famous rule doesn't apply (a host who opens a door at random, a coin of unknown fairness) catch a model that applies the memorized answer everywhere.

## 2. Sourcing
New questions (sources/reasoning_traps): eight classic problems as published (seven shown; the screen hid Linda), plus 29 isomorphs and controls written for this project (26 and 3 shown), each with a right answer and, where one exists, the intuitive wrong answer (the lure). People's split exists only for Linda (85% of 142 chose the conjunction, Tversky & Kahneman 1983); the taxi cab's published median answer (80%) is in meta.

Sources: `reasoning_traps`

## 3. Collection
37 new questions, each asked as written, for 'most people', and with the options in three shuffled orders (averaged).

## 4. Scoring
Per trap family, the share right on the classic, on the new isomorphs and on the controls, and the share of the lure. For numeric answers (base rates, birthdays), right means Jev's median lands in the right bin or the one next to it.

## 5. Visualization
Paired bars per trap family: right on the classic vs right on the new versions, with the controls as dots.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.133, top verdict `portrait`.

## Compared with
the right answers; people's rate for Linda (Tversky & Kahneman 1983) and the taxi cab (median 80%)

## Limits
A handful of items per family: read the families as examples, not rates. The isomorphs were written for this project and labeled as such.

Results: `data/analysis/experiments/reasoning_traps.json` (private). Code: `scripts/experiments/`.
