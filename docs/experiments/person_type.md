# person_type

family: personality

## 1. Question
On an open Jungian type test (OEJTS, a free Myers-Briggs-style test), which type does Jev come out as?

The four letters are the most-asked personality question on the internet.

## 2. Sourcing
Existing OEJTS items (source `oejts`, 51 items after dropping the unkeyed ones), each a pair of poles. No human norms in the corpus, so the comparison is Jev's answer for 'most people'.

Sources: `oejts`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of each axis's items where Jev leans to each pole, with a 90% interval from resampling items; the type is the four majority letters; strength is the distance from 50%.

## 5. Visualization
Four bipolar bars with Jev's square and its 'most people' ring, the type in big letters.

## 6. Evaluation
Jev's verdict (evaluator v4): **atlas**, head-to-head strength -2.716, top verdict `portrait`.

## Compared with
Jev's own answer for 'most people' (no human norms available)

## Limits
Types are a coarse cut of continuous traits; OEJTS is an open replica, not the proprietary MBTI.

Results: `data/analysis/experiments/person_type.json` (private). Code: `scripts/experiments/`.
