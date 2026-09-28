# taste_vs_audience_book

family: taste

## 1. Question
Does Jev like the books that Goodreads readers like, and where does it disagree most?

A real test of taste against a real crowd, not against Jev's own guess about people; the disagreements are the portrait.

## 2. Sourcing
Existing rating questions under Self > Lifestyle > Ratings > book_ratings, each with the real rating distribution of Goodreads readers (their ratings binned to the same five levels). Enough: thousands of items.

Sources: `taste_ratings`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Rank correlation (Spearman) between Jev's robust level and the audience's mean level, with a 90% bootstrap interval over items; the items with the largest rank disagreement in each direction. Ranks, not levels, because Jev's described levels and the audience's star ratings aren't the same scale.

## 5. Visualization
A scatter of audience rank vs Jev's rank, with the ten biggest disagreements labeled on each side.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.798, top verdict `portrait`.

## Compared with
Goodreads readers (their average rating of each item)

## Limits
Audiences rate what they chose to watch or drink; Jev rates everything. Rank comparisons only.

Results: `data/analysis/experiments/taste_vs_audience_book.json` (private). Code: `scripts/experiments/`.
