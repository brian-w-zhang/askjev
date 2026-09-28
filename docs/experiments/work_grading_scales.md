# work_grading_scales

family: work

## 1. Question
When a work task asks for a level on a scale (a relevance grade, a star rating, an essay score), does Jev put items in the right order, hit the exact level, and use the scale the way the labels do?

Graded judgments are how models get used for ranking and review. Order right but levels off means it is useful for sorting and not for thresholds; a shifted scale means every threshold needs re-tuning.

## 2. Sourcing
Existing Score questions from 11 public labeled datasets with a graded answer (3-6 levels). Enough: ~17,000 questions.

Sources: `stsb_similarity`, `amazon_reviews`, `wine_notes`, `esco_titles`, `wands_relevance`, `wikibio_hallucination`, `djinni_recruitment`, `trec_covid`, `esci_rerank`, `helpsteer2`, `asap_essays`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per task: rank correlation between Jev's expected level and the label (90% bootstrap interval); share at the exact level and within one level (Jev's most likely level); mean level of Jev's most likely answer vs the labels'.

## 5. Visualization
A dot plot per task: rank correlation, with the exact-level share as a label; the essay task marked.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
each dataset's graded labels

## Limits
Level wordings are ours (described situations), the labels' scales were theirs; comparing mean levels assumes the mapping is fair.

Results: `data/analysis/experiments/work_grading_scales.json` (private). Code: `scripts/experiments/`.
