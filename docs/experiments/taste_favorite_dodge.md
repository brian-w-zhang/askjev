# taste_favorite_dodge

family: taste

## 1. Question
When an r/polls question asks for a favorite and offers an escape option ('Other', 'None'), how often does Jev take the escape instead of naming a favorite, compared with the voters?

A favorites list is only as good as the model's willingness to name one. If Jev's own answer is 'Other' where people commit, its taste is partly a refusal to have one, and a poll or survey built on it would come back full of abstentions.

## 2. Sourcing
Existing r/polls questions with real vote shares (100+ votes) that offer an escape option (Other, Other (comment), None, Neither...). Favorites polls are those whose text asks for a favorite, best or preference: about 1,400; the other 4,200 escape-option polls are the comparison.

Sources: `reddit_polls`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of polls where the escape option is Jev's top pick, for its own answer and for its 'most people' guess, vs the share where it is the voters' top pick; the average weight on the escape option; 90% bootstrap intervals over polls.

## 5. Visualization
Paired bars: share of polls where the escape option comes first, voters vs Jev, for favorites polls and for other polls, with Jev's 'most people' guess as a third bar.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.4, top verdict `headline`.

## Compared with
r/polls voters (100+ per poll)

## Limits
Voters who pick 'Other' often name something in the comments; the poll counts only the click. Whether a poll asks for a favorite is matched from its wording.

Results: `data/analysis/experiments/taste_favorite_dodge.json` (private). Code: `scripts/experiments/`.
