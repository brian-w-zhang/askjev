# polls_reddit

family: polls

## 1. Question
Across 50,000 r/polls questions (bath or shower, cats or dogs, favorite season), how often does Jev guess which option most voters picked, and on what topics does it read them worst?

r/polls is the largest open record of everyday preferences with real vote counts. Reading a crowd well on one topic and badly on another shows where a model's picture of ordinary people is thin.

## 2. Sourcing
Existing r/polls questions with their vote shares, placed across about 120 topics in the tree. Political and religious topics are dropped. Enough: about 49,000 polls.

Sources: `reddit_polls`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of polls where Jev's guess of most people names the voters' winner, against the chance rate (1 / number of options); the same for polls with a clear winner (a 20-point margin); per topic with 40+ polls, the lift over chance; Jev's own answer alongside.

## 5. Visualization
Dot plot of the lift over chance per topic, top and bottom ten, with the overall rate as a line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.663, top verdict `portrait`.

## Compared with
r/polls voters (vote shares per poll)

## Limits
Redditors who vote in polls are young and online, not 'most people'. Many polls have joke options.

Results: `data/analysis/experiments/polls_reddit.json` (private). Code: `scripts/experiments/`.
