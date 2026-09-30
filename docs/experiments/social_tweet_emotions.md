# social_tweet_emotions

family: social

## 1. Question
Given a short tweet and six emotions (joy, love, surprise, sadness, anger, fear), does Jev name the one its writer tagged, and which emotions does it mix up? And does it notice thanks in Reddit comments?

Coding the feeling in short texts is a staple of market research, support triage and social science. The mix-ups matter more than the average: an emotion Jev reliably folds into another disappears from whatever it summarizes.

## 2. Sourcing
Existing questions from two datasets: an emotion set of about 2,000 English tweets whose label comes from the emotion hashtag its writer used (so the label is the writer's own tag, not a reader's judgment), balanced across six emotions; and about 2,000 Reddit comments from GoEmotions, where raters marked whether a comment expresses gratitude (half do; the other half include other warm comments, so friendliness alone doesn't decide it).

Sources: `emotion`, `goemotions_gratitude`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For the tweets, the share of each emotion Jev names correctly and a table of what it names instead, with 90% bootstrap intervals. For the comments, the share of thankful ones it misses vs the share of others it calls thankful.

## 5. Visualization
A grid: the writer's emotion down the side, Jev's pick across the top, shaded by count.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
The writers' own hashtags (tweets) and raters' labels (Reddit comments)

## Limits
Hashtag labels are noisy: a writer who tags #love may be describing joy. The comparison is to the writer's tag, not to what other readers would say. Label descriptions were written for this project.

Results: `data/analysis/experiments/social_tweet_emotions.json` (private). Code: `scripts/experiments/`.
