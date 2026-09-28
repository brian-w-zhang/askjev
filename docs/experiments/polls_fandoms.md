# polls_fandoms

family: polls

## 1. Question
On polls inside hobby and fan subreddits (r/Berserk, r/Naruto, r/thebachelor, r/Kanye...), which communities' votes does Jev guess best?

A fandom's inside opinions ('best arc', 'worst contestant') are niche knowledge that shows up in training data unevenly. Where Jev can't beat chance, it doesn't know the community.

## 2. Sourcing
Existing polls from 30 hobby and fan subreddits with vote shares. Politics-tagged polls dropped. Enough for communities with 40+ polls.

Sources: `reddit_hobby_polls`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per community, share of polls where Jev's guess names the winner, and its lift over chance; overall rate with a 90% bootstrap interval.

## 5. Visualization
Ranked bars: communities by lift over chance, with the chance line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.613, top verdict `portrait`.

## Compared with
Voters in each subreddit's own polls

## Limits
Community sizes and poll styles differ; some polls are about events after Jev's training data.

Results: `data/analysis/experiments/polls_fandoms.json` (private). Code: `scripts/experiments/`.
