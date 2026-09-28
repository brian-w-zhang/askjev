# person_bigfive

family: personality

## 1. Question
Where do Jev's answers to the public 50-item Big Five test land among the 603,322 people who took it?

The most-used personality test on earth, with a huge real norm group: a direct placement, trait by trait.

## 2. Sourcing
Existing IPIP 50-item Big Five marker questions (source `ipip`), asked as written; the human reference is the IPIP-FFM open dataset (603,322 complete, one-per-IP respondents). Enough: all 50 items.

Sources: `ipip`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's expected answer per item on the test's 1-5 scale, keyed and summed per trait as for a person, placed as a percentile of the respondents' trait scores; 90% intervals from resampling the ten items; robustness from the reversed-scale answers and the 'most people' answers (which should land near 50th).

## 5. Visualization
Five percentile strips (0-100) with Jev's square, its 'most people' ring, and the interval.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.827, top verdict `portrait`.

## Compared with
603,322 people who took the IPIP-FFM test online (Open Psychometrics)

## Limits
People rate themselves generously and Jev rates in the middle; answering for 'most people' Jev lands near the middle too, so read the gap between the square and the ring, not only the percentile.

Results: `data/analysis/experiments/person_bigfive.json` (private). Code: `scripts/experiments/`.
