# words_iconicity

family: words

## 1. Question
Asked how much a word sounds like what it means, does Jev hear the same links people do?

Iconicity (the 'buzz' in buzz) is a live topic in the science of language: people hear some of it in ordinary words too. A model that only reads text never hears words at all.

## 2. Sourcing
Existing questions ('How much does the word "<word>" sound like what it means?', seven described levels) on 2,488 words from Winter et al. 2023, each with about 10 raters' individual ratings. Enough.

Sources: `iconicity_ratings`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Rank correlation between Jev's robust level and the raters' mean, with a 90% bootstrap interval; mean level for each side on the 1-7 scale; the share of words each side puts in the bottom two levels; the largest gaps each way.

## 5. Visualization
A scatter of raters' mean (x) against Jev's (y) with the onomatopoeia labeled and the biggest misses marked.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.111, top verdict `portrait`.

## Compared with
Winter et al. 2023 raters (US English speakers, about 10 per word)

## Limits
Ten raters per word leaves each word's mean noisy, which caps the correlation. Jev can't hear; it answers from what text says about words. The two words named in the result are hand-picked from the ten largest gaps among words the raters agreed on.

Results: `data/analysis/experiments/words_iconicity.json` (private). Code: `scripts/experiments/`.
