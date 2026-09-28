# knowledge_fame_online

family: knowledge

## 1. Question
Asked which of two people, athletes or internet phenomena is better known, how often does Jev pick the one the world actually looks up more, and is it as sure as it should be?

Fame is a fact about people's attention, not about the thing itself. A model trained on text has seen the famous more often, so it should know fame well; where it doesn't, its picture of what people care about is out of date or thin.

## 2. Sourcing
Existing questions: Pantheon historical figures and athletes (fame by the Historical Popularity Index: Wikipedia languages and page views; CC BY-SA 4.0) and Wikidata internet phenomena (fame by English Wikipedia page views 2023-2025; CC0). Politicians flagged political are left out. Enough: 7,000 pairs.

Sources: `pantheon_history`, `pantheon_sports`, `wikidata_memes`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy and mean confidence per domain with 90% bootstrap intervals; for memes, accuracy by how many times more views the better-known one had.

## 5. Visualization
Paired bars per domain: Jev's confidence vs its accuracy, so overconfidence shows as a gap.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Wikipedia attention (Pantheon HPI, page views)

## Limits
Page views are a proxy for fame and favor recent and English-language interest.

Results: `data/analysis/experiments/knowledge_fame_online.json` (private). Code: `scripts/experiments/`.
