# taste_self_vs_guess

family: taste

## 1. Question
In which kinds of things does Jev rate itself differently from how it thinks most people would?

The gap between 'I'd like this' and 'most people would like this' is how a model separates itself from the crowd; the domains and items where it's largest say what it thinks is distinctive about itself.

## 2. Sourcing
Every rating question in the 12 taste domains, asked for Jev and again for 'most people' (the human frame every question carries). Enough: ~20,000 items.

Sources: `taste_ratings`, `g5_w13_ratings`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per domain, mean of (Jev's level minus its level for most people), with a 90% bootstrap interval over items; the items with the largest gap either way.

## 5. Visualization
A dot plot, one row per domain, with the gap and its interval; top items per side as labels.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Jev's own guess about most people (not real people; the audience experiments do that)

## Limits
Both sides are Jev's answers; this is self-image, not a comparison with a crowd.

Results: `data/analysis/experiments/taste_self_vs_guess.json` (private). Code: `scripts/experiments/`.
