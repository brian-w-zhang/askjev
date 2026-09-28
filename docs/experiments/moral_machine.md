# moral_machine

family: moral

## 1. Question
In the Moral Machine's self-driving-car dilemmas, which factors pull Jev toward sparing one side, and how does that compare with millions of players?

The largest study of machine ethics preferences (Awad et al. 2018, Nature) measured what people want a car to do; a model answering the same dilemmas shows which of those preferences it shares and which it drops.

## 2. Sourcing
Existing Moral Machine scenarios (26,020 shown dilemmas reconstructed from the study's data), each with the real players' split, for the world and 10 countries. Enough.

Sources: `moral_machine`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The study's own regression: for each factor, the change in the probability of sparing a side per unit difference (AMCE), fitted to Jev's probabilities and to players' shares; 90% intervals by bootstrap over scenarios. Countries compared by distance of their nine-factor profile to Jev's.

## 5. Visualization
Effect dot plot: one row per factor, players (diamond) and Jev (square) with intervals, zero line; the rows where Jev drops a human preference highlighted.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.165, top verdict `portrait`.

## Compared with
Moral Machine players worldwide (millions of decisions) and in 10 countries

## Limits
Players chose; Jev gives probabilities. The factor list is the study's; the scenarios are the study's templates, so wording effects are shared.

Results: `data/analysis/experiments/moral_machine.json` (private). Code: `scripts/experiments/`.
