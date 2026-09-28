# humor_three_crowds

family: humor

## 1. Question
Across three sets of human funniness ratings (classic jokes, edited news headlines, cartoon captions), where does Jev's sense of funny line up with people's?

Humor is one of the places a model's taste could be most different from ours; comparing three crowds separates 'can't rank jokes at all' from 'can rank some kinds of jokes'.

## 2. Sourcing
Existing rating questions with human rating distributions: Jester (100 classic jokes, thousands of ratings each), Humicroedit (4,383 news headlines with one word swapped for a joke, 5 judges each), and New Yorker contest captions (2,915, about 165 voters each). Enough.

Sources: `jester`, `humicroedit`, `caption_contest`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per set, rank correlation between Jev's robust level and the crowd's mean level, with a 90% bootstrap interval over items. Humicroedit's 5 judges make its crowd means noisy, which caps any correlation.

## 5. Visualization
Three dots with intervals, one per crowd, on a -1 to 1 scale.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.547, top verdict `portrait`.

## Compared with
Jester users, Humicroedit crowd judges (MTurk), New Yorker contest voters

## Limits
The sets differ in format and in how famous the jokes are: Jester's jokes circulate widely online, so Jev may know how they are received rather than find them funny.

Results: `data/analysis/experiments/humor_three_crowds.json` (private). Code: `scripts/experiments/`.
