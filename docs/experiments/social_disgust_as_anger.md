# social_disgust_as_anger

family: social

## 1. Question
Across seven basic emotions in people's own stories, which does Jev recognize and which does it mistake for another?

ISEAR is the classic cross-cultural record of what makes people feel each emotion. The emotions a reader confuses show what it thinks each feeling is about; disgust at someone's behavior and anger at it sit close together.

## 2. Sourcing
Existing ISEAR questions (about 2,900 first-person stories from students in 37 countries, each written about one of seven emotions); Jev picks one of the seven. Enough: about 400 per emotion.

Sources: `isear`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The confusion table: for each emotion the writer named, the share Jev gives each label; the share right per emotion with 90% bootstrap intervals; how often Jev uses each label compared with writers.

## 5. Visualization
A heat table, writer's emotion (rows) by Jev's pick (columns), shares per row.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.677, top verdict `headline`.

## Compared with
The writers' own labels

## Limits
Stories are short and were translated; some were written in answer to a prompt for that emotion, so the label is what the writer was asked about.

Results: `data/analysis/experiments/social_disgust_as_anger.json` (private). Code: `scripts/experiments/`.
