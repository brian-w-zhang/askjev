# judge_fake_reviews

family: judge

## 1. Question
Can Jev tell a real review from a fake one, when the fake was written by a person paid to invent a hotel stay, or by a text generator?

Deceptive reviews are a real market problem. Ott et al. 2011 found people barely beat chance on the hotel set and tend to believe what they read; a model might do the same, or better.

## 2. Sourcing
Existing Deceptive Opinion Spam items (Ott et al. 2011: 400 truthful and 400 invented Chicago hotel reviews, the invented ones written by paid MTurk workers) and a set of real vs machine-generated product reviews (Salminen et al. 2022). Enough: 2,760 reviews, balanced.

Sources: `op_spam_reviews`, `fake_reviews`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy against the labels, and the direction of errors: the share of fakes Jev accepts as real.

## 5. Visualization
Paired bars per dataset: the share of fakes Jev calls real, and the share of real reviews it calls fake.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
The datasets' labels; Ott et al. 2011's human judges as reference (near chance, trusting)

## Limits
The generated reviews come from an older text generator; newer ones would be harder.

Results: `data/analysis/experiments/judge_fake_reviews.json` (private). Code: `scripts/experiments/`.
