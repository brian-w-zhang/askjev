# work_names_in_tweets

family: work

## 1. Question
Given a name in a sentence, can Jev say what kind of thing it names, in edited news text and in tweets?

Entity typing feeds search, moderation and analytics. News names follow conventions; tweets name brands, products and groups in ways that break them.

## 2. Sourcing
Existing questions from CoNLL-2003 (news: person, organization, location, other) and WNUT-17 (tweets: person, location, group, corporation, product, creative work), balanced by type.

Sources: `entity_typing`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share right per type in each corpus, and the most common confusion for the weakest types.

## 5. Visualization
Bars per type, news and tweets.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.925, top verdict `portrait`.

## Compared with
each dataset's own labels

## Limits
WNUT-17 was built from rare and emerging names on purpose.

Results: `data/analysis/experiments/work_names_in_tweets.json` (private). Code: `scripts/experiments/`.
