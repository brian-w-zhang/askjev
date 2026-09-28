# judge_mixed_reviews

family: judge

## 1. Question
Reading a review, does Jev hear the complaints louder than the writer meant them?

Most real reviews mix praise and gripes. Whether a reader weights the gripes more is a negativity bias, and it changes summaries, routing, and any rating a model infers.

## 2. Sourcing
Existing Amazon reviews with their star rating (Jev reads the text and picks one of five described levels of satisfaction) and Steam reviews with the player's thumbs up or down. Enough: about 4,700.

Sources: `amazon_reviews`, `steam_reviews`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's mean level for each star rating; the share of 3-star reviews it reads as a let-down or a failure vs as pleased; on Steam, the share of thumbs-up reviews read as thumbs-down and the reverse.

## 5. Visualization
Dots per star rating: the star level (0-4) and Jev's mean reading of the same reviews.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.796, top verdict `portrait`.

## Compared with
The reviewers' own star ratings and thumbs

## Limits
A star rating is the writer's summary, not the only right reading of the text.

Results: `data/analysis/experiments/judge_mixed_reviews.json` (private). Code: `scripts/experiments/`.
