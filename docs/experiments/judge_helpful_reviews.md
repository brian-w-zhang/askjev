# judge_helpful_reviews

family: judge

## 1. Question
Would Jev call an Amazon review helpful to shoppers, compared with how shoppers actually voted?

'Was this review helpful?' is a real crowd judgment of usefulness. A model that finds everything helpful is a poor filter, and generosity is a trait worth knowing in a judge.

## 2. Sourcing
Existing Amazon reviews (McAuley 5-core) with the helpful and unhelpful vote counts, 10 or more votes each. Enough: 2,500 reviews.

Sources: `amazon_helpful`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The share Jev calls helpful vs the share with a helpful majority; Jev's call binned by the share of shoppers voting helpful; rank correlation with the vote share.

## 5. Visualization
Binned dots: shoppers' helpful share (x) against the share Jev calls helpful (y).

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.846, top verdict `headline`.

## Compared with
Amazon shoppers who voted on each review (median about 15 votes)

## Limits
Votes pile up on early and visible reviews, not only useful ones.

Results: `data/analysis/experiments/judge_helpful_reviews.json` (private). Code: `scripts/experiments/`.
