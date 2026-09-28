# words_norms

family: words

## 1. Question
Rating thousands of English words on the dimensions psycholinguists norm (pleasantness, excitement, age of learning, familiarity, size, imageability, concreteness), where does Jev agree with people?

Word norms are how psychology measures what words mean to people beyond their definitions. A model learns words only from text, so the dimensions it gets right and wrong show what text does and doesn't carry.

## 2. Sourcing
Existing rating questions built from the Glasgow Norms (Scott et al. 2019, 5,553 words rated on 1-9 or 1-7 scales) and the Brysbaert et al. 2014 concreteness ratings (1-5), with each word's human mean. Enough: about 1,000-2,000 words per dimension, 11,857 ratings.

Sources: `glasgow_norms`, `concreteness`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per dimension, rank correlation between Jev's robust level and the human mean, with a 90% bootstrap interval over words. Ranks because Jev's five described levels and the norms' numeric scales differ.

## 5. Visualization
Dots with intervals, one row per dimension, sorted by agreement.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.154, top verdict `portrait`.

## Compared with
Glasgow Norms raters (UK students, about 30 per word per scale); Brysbaert et al. 2014 raters (US, MTurk)

## Limits
Jev's scales use described levels written for this project ('Calming: it feels sleepy or soothing'), not the norms' numbered anchors, so part of any gap is wording. Human means only; no per-rater spread.

Results: `data/analysis/experiments/words_norms.json` (private). Code: `scripts/experiments/`.
