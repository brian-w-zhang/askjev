# words_funny

family: words · new questions: 599

## 1. Question
Rating single English words for how funny they are, does Jev find the same words funny as people do?

Jev can barely tell which joke or caption is funnier (humor family). Single words strip humor down to sound and meaning; if it can tell a funny word, the problem with jokes is elsewhere.

## 2. Sourcing
New questions (sources/humor_words): 'How funny is the word "<word>" on its own?', five described levels, for 600 of the 4,997 words in Engelthaler & Hills 2018, spread evenly over the range of people's ratings (1-5, about 35 raters per word).

Sources: `humor_words`

## 3. Collection
599 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Rank correlation between Jev's expected level (base and reversed averaged) and people's mean rating, with a 90% bootstrap interval; the words it finds much funnier or much less funny than people.

## 5. Visualization
A scatter: people's mean (x) vs Jev's level (y), with the biggest disagreements labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.196, top verdict `portrait`.

## Compared with
US adults rating the words (Engelthaler & Hills 2018)

## Limits
Only people's means are published, so the comparison is ranks, not distributions.

Results: `data/analysis/experiments/words_funny.json` (private). Code: `scripts/experiments/`.
