# reasoning_beauty_contest

family: reasoning · new questions: 8

## 1. Question
In the game where everyone picks a number from 0 to 100 and the winner is closest to two-thirds of the average, what does Jev pick against lab students, newspaper readers and copies of itself, and how well does it predict each crowd's average?

The game theory answer is 0, but 0 never wins: winning means guessing how many steps of reasoning the others take. It is a clean test of whether a model reasons about people as they are or as a textbook says they should be.

## 2. Sourcing
New questions (sources/beauty_contest): the game against four crowds, three with published means (Nagel 1995 lab first rounds: 36.73 for two-thirds, 27.05 for one-half; Thaler's 1997 Financial Times contest: 18.91) and copies of Jev. For each, Jev's pick and its expected average, in 21 bins.

Sources: `beauty_contest`

## 3. Collection
8 new questions, each in three shuffled orders of the bins (averaged).

## 4. Scoring
Per crowd, the winning number (the fraction times the published mean) against Jev's median pick; Jev's expected average against the published mean; its pick against copies of itself (the equilibrium is 0).

## 5. Visualization
Dots per crowd: Jev's pick, the winning number (tick) and Jev's predicted average vs the real one.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.873, top verdict `portrait`.

## Compared with
Published crowd means (Nagel 1995; Thaler's 1997 Financial Times contest)

## Limits
Only means are published, so Jev's pick is scored against the winning number, not a full distribution. The newspaper contest ran in 1997; its readers may have known the game.

Results: `data/analysis/experiments/reasoning_beauty_contest.json` (private). Code: `scripts/experiments/`.
