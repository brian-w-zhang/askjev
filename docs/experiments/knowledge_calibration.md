# knowledge_calibration

family: knowledge

## 1. Question
Across 120,000 questions with a known right answer, does Jev's confidence match how often it is right?

A model that knows when it doesn't know is far more useful than one that is merely accurate. TypeSafe publishes no calibration numbers (01-jev.md §6 lists this as open ground), so this is new.

## 2. Sourcing
Every shown fact question with a right answer across 23 sources (Wikidata, Pantheon, World Bank, USDA, AnAge, school and professional exams, trivia, yes/no reading questions). Enough: 120,000 questions.

Sources: `wikidata_g4`, `wikidata_companies`, `wikidata_memes`, `pantheon_history`, `pantheon_sports`, `worldbank_pairs`, `usda_nutrients`, `anage_pairs`, `mmlu`, `arc`, `sciq`, `openbookqa`, `medmcqa`, `head_qa`, `truthfulqa`, `uscis_civics`, `opentdb`, `strategyqa`, `boolq`, `hotpot_compare`, `natural_questions_yn`, `ham_radio_pools`, `uscg_mariner`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's probability on its top option, binned; in each bin, the share of questions it got right, with a 90% bootstrap interval. The gap between confidence and accuracy is summarized as the average absolute gap weighted by bin size (expected calibration error), and per source as mean confidence minus accuracy.

## 5. Visualization
A reliability diagram: confidence bins on x, accuracy on y, the diagonal as perfect calibration, dot size by count.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
the right answers (Wikidata, exam keys, dataset labels)

## Limits
Answer keys contain some errors (MMLU virology is known for them), which make Jev look overconfident. The mix of sources sets the overall curve; the per-source gaps are the fairer comparison.

Results: `data/analysis/experiments/knowledge_calibration.json` (private). Code: `scripts/experiments/`.
