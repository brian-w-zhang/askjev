# knowledge_pop_trivia

family: knowledge

## 1. Question
On pub-quiz trivia, which categories does Jev know and which does it miss, and does it find the questions people rated hard harder?

Trivia spans the whole of general culture in one format, so category differences are about knowledge, not question style; the human difficulty ratings give an outside check.

## 2. Sourcing
Existing Open Trivia Database questions (CC BY-SA 4.0) with their category and the contributor's difficulty rating. Enough: 2,800 questions, categories with 40+ questions shown.

Sources: `opentdb`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy per category with 90% bootstrap intervals; accuracy by the easy/medium/hard rating.

## 5. Visualization
Ranked dots: one row per category, with the difficulty ratings as a small three-bar inset.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.164, top verdict `portrait`.

## Compared with
Open Trivia DB answer keys and difficulty ratings

## Limits
Difficulty is one contributor's rating; categories are the database's.

Results: `data/analysis/experiments/knowledge_pop_trivia.json` (private). Code: `scripts/experiments/`.
