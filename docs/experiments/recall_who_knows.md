# recall_who_knows

family: recall · new questions: 299

## 1. Question
Shown a general-knowledge question and its answer, can Jev tell what share of US college students came up with that answer unaided, from 'zebra' (93%) to facts almost nobody recalls?

Knowing a fact is one thing; knowing that most people don't is what makes an explanation pitched right. A model that knows everything may assume everyone does.

## 2. Sourcing
New questions (sources/recall_norms): the 299 questions of Tauber et al. 2013, each shown with its answer, asking what share of the students recalled it, in 12 bins (0-2%, 2-5%, 5-10%, then 10-point steps). Truth: the share of about 670 US college students who recalled it with no answer choices. The per-item shares are a public transcription of the paper's table, checked against the German update's reprint of the ranks (Spearman 0.99).

Sources: `recall_norms`

## 3. Collection
299 new questions, each asked as written, for 'most people', and with the bins in three shuffled orders (averaged).

## 4. Scoring
Jev's expected share (bin midpoints) vs the real share: rank correlation with a 90% bootstrap interval; mean gap by third of the real share (rarely, sometimes, usually recalled); the questions with the largest gaps each way. As a check, the rank correlation with the German 2020 shares for the same questions.

## 5. Visualization
A scatter: real share (x) vs Jev's estimate (y), diagonal, the largest misses labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.114, top verdict `portrait`.

## Compared with
US college students, 2012 (Tauber et al. 2013)

## Limits
The students are one population (US college students, 2012); 'recall' means producing the answer with no options, which is harder than recognizing it. The answer is shown to Jev, so this measures its sense of how common the knowledge is, not its knowledge.

Results: `data/analysis/experiments/recall_who_knows.json` (private). Code: `scripts/experiments/`.
