# influence_predict_self

family: influence · new questions: 250

## 1. Question
Asked which option 'an AI model named Jev' chose on a poll or would-you-rather question, does Jev predict the answer it actually gives when asked directly?

Self-knowledge is testable when the self answers the same questions: if Jev's picture of itself differs from what it does, its self-descriptions elsewhere (the portrait's personality tests) deserve less trust.

## 2. Sourcing
New questions (sources/influence_variants): 'An AI model named Jev was asked the question below. Which option did it choose?' wrapped around 150 Reddit polls and 100 either.io would-you-rather questions (drawn at random) that Jev had answered directly.

Sources: `influence_variants`

## 3. Collection
250 new questions, each asked with the options in shuffled orders.

## 4. Scoring
Share where the predicted option is Jev's own top answer, against the share where it is the real crowd's majority and Jev's guess for 'most people'; agreement split by how sure Jev's own answer was.

## 5. Visualization
Bars: the prediction matches Jev's own answer / Jev's guess for most people / the real majority.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.363, top verdict `portrait`.

## Compared with
Jev's direct answers, its 'most people' answers, and the real votes

## Limits
Jev may not know it is 'Jev'; the question names it but gives no other description.

Results: `data/analysis/experiments/influence_predict_self.json` (private). Code: `scripts/experiments/`.
