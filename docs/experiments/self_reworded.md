# self_reworded

family: self

## 1. Question
When the same yes/no question is asked twice in different words ('Do you like to return to the same vacation spot?' / 'Do you tend to go back to the same places for vacation?'), does Jev give the same answer?

Asking the identical request twice moves Jev by about a point (consistency_repeat_noise). Rewording is the realistic case: people never ask the same way twice. The gap between the two is how much of an answer is the wording.

## 2. Sourcing
Existing pairs the pipeline's dedupe stage linked as duplicates (question_links), where both are yes/no and at least one comes from the self banks written for this project (g5_*). The duplicate side is hidden from the map but was asked. Pairs whose polarity words differ ('fake' vs 'real', 'wrong' vs 'okay', any negation) are set aside, because opposite answers to opposite questions are consistent.

Sources: `g5_w1_lifestyle_love`, `g5_w5_self`, `g5_w9_self_b`, `g5_w9_self_c`, `g5_w10_self_personality`, `g5_p6_personality`, `g5_self_lifestyle_traits`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per pair, the difference between Jev's two probabilities of yes; the share of pairs answered on the same side of 50%; the same among pairs where both answers are firm (70/30 or more); correlation across pairs; compared with the repeat noise of identical requests.

## 5. Visualization
A scatter of the two probabilities, one dot per pair, with the diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.257, top verdict `portrait`.

## Compared with
Jev asked the identical request twice (consistency_repeat_noise)

## Limits
Duplicates are the dedupe stage's judgment (embedding similarity plus Jev's confirmation), so some pairs differ in meaning ('would you' vs 'could you', 'always' vs 'sometimes'); the polarity filter is a word list and misses some flips. The pairs with the largest gaps are listed as found, not hand-picked.

Results: `data/analysis/experiments/self_reworded.json` (private). Code: `scripts/experiments/`.
