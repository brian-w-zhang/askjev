# language_health_pairs

family: language · new questions: 150

## 1. Question
Given two health states, does Jev pick the one Americans value lower, and how much does that depend on how far apart they are?

The direct comparison is easier than putting a number on a state; if Jev still disagrees with people, it weighs pain, mobility and mood differently, not just reads the scale differently.

## 2. Sourcing
New questions (sources/health_states): 150 random pairs of EQ-5D-5L states, 50 each with a utility gap under 0.1, 0.1-0.3 and over 0.3 in the US value set (Pickard et al. 2019).

Sources: `health_states`

## 3. Collection
150 new questions, each asked with the states in both orders (averaged).

## 4. Scoring
Share where Jev's pick (averaged over both orders) is the state with the lower utility, by gap band with 90% bootstrap intervals; for misses, which dimension the state Jev called worse was worse on.

## 5. Visualization
Bars: agreement by gap band.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.008, top verdict `portrait`.

## Compared with
The US EQ-5D-5L value set (Pickard et al. 2019)

## Limits
Small gaps (under 0.1) are within the value set's own uncertainty.

Results: `data/analysis/experiments/language_health_pairs.json` (private). Code: `scripts/experiments/`.
