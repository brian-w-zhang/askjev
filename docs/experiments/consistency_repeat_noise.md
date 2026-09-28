# consistency_repeat_noise

family: consistency

## 1. Question
If the exact same request is sent twice, how much does Jev's answer change, and when does its top answer flip?

Every comparison on this site rests on a noise floor. Jev returns probabilities, not a sampled answer, so the question is whether those probabilities are fixed or wobble, and whether a wobble can change what it would pick.

## 2. Sourcing
Two-option questions whose reversed-order probe was sent twice as separate requests (answer.py asks reversed, original, reversed). Enough: 214,000 pairs of identical requests.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The absolute change in the probability of the same option between the two identical requests; the share of pairs where the favored option changes, by how far the first answer was from 50/50.

## 5. Visualization
Flip rate by distance from 50/50 (0-2, 2-5, 5-10, 10-20, 20-50 points), with the mean change above each bar.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.072, top verdict `portrait`.

## Compared with
Jev itself

## Limits
Probabilities come back rounded to whole points, so changes under one point are invisible. Two-option questions only.

Results: `data/analysis/experiments/consistency_repeat_noise.json` (private). Code: `scripts/experiments/`.
