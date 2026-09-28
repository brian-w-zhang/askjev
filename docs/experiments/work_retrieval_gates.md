# work_retrieval_gates

family: work

## 1. Question
Asked whether a retrieved passage answers a query or belongs in the context, which way does Jev err: letting in passages that don't help, or throwing out ones that do?

Retrieval pipelines use a cheap model as a gate before the expensive one. A generous gate wastes context; a strict one drops the evidence a multi-step question needs.

## 2. Sourcing
Existing yes/no questions from MS MARCO (web search passages vs real queries), HotpotQA (paragraphs needed for two-step questions vs distractors on the same topic) and QNLI (does a Wikipedia sentence answer the question).

Sources: `msmarco_relevance`, `hotpot_gating`, `qnli_gating`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per set, the share of useful passages Jev rejects and of useless passages it lets in, with 90% intervals.

## 5. Visualization
Paired bars per set: useful passages rejected vs useless ones let in.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.577, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
MS MARCO's labels mark the passage a human annotator used, so some unmarked passages do answer the query; that inflates its 'let in' rate.

Results: `data/analysis/experiments/work_retrieval_gates.json` (private). Code: `scripts/experiments/`.
