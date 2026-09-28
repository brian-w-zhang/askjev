# judge_top_grade

family: judge

## 1. Question
Asked to read how highly a critic rated a wine, how close two sentences are in meaning, or how satisfied a reviewer is, how often does Jev land on the top level compared with the real answer?

Reading a judgment off text is a common task (inferring ratings, grading, deduplication). If a reader shies away from the top of every scale, the best items blur into the very good ones.

## 2. Sourcing
Existing Score questions with a known level: wine critic notes (Wine Enthusiast points binned into 5 even groups), STS-B sentence pairs (6 levels of similarity from annotators' means), Amazon reviews (5 star levels) and seventh-grade essays (ASAP, 4 teacher score levels). Enough: about 7,400 items, the first three balanced by level.

Sources: `wine_notes`, `stsb_similarity`, `amazon_reviews`, `asap_essays`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The share of items whose true level is the top one, vs the share where Jev's most likely level is the top one; Jev's mean level for the top-level items; rank correlation per set.

## 5. Visualization
Paired bars per dataset: share at the top level, true vs Jev.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
The datasets' own levels (critic points, annotator means, stars, teacher scores)

## Limits
The levels are described situations written for Jev from each dataset's scale; bin edges are ours.

Results: `data/analysis/experiments/judge_top_grade.json` (private). Code: `scripts/experiments/`.
