# self_could_vs_would

family: self

## 1. Question
In pairs of questions that ask the same thing, does the verb they open with ('Could you…', 'Would you…', 'Do you…', 'Can…') change how often Jev says yes?

self_closed_questions found 'Can…?' questions get more yeses than 'Will…?' ones across different questions. Paired rewordings of the same question separate the verb from the topic: the difference is the word.

## 2. Sourcing
The same-polarity duplicate pairs as in self_reworded (yes/no, at least one from the self banks), grouped by the pair of opening words.

Sources: `g5_w1_lifestyle_love`, `g5_w5_self`, `g5_w9_self_b`, `g5_w9_self_c`, `g5_w10_self_personality`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each pair of opening words with 15+ pairs, the mean difference in Jev's probability of yes, with a 90% bootstrap interval over pairs.

## 5. Visualization
Dots with intervals, one row per pair of opening words, around zero.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.544, top verdict `headline`.

## Compared with
Jev's answer to the same question opened with a different verb

## Limits
Pairs are few for some verbs (the counts are shown). 'Could you date…' can honestly mean something milder than 'Would you date…'; the result measures the wording, whichever reading Jev takes.

Results: `data/analysis/experiments/self_could_vs_would.json` (private). Code: `scripts/experiments/`.
