# lexicon_idiom_ratings

family: lexicon · new questions: 392

## 1. Question
Does Jev know which idioms are familiar to Americans and which could make sense taken word for word, the way people rated them?

Familiarity and literal plausibility are what people use to read an idiom ('kick the bucket' could happen; 'rain cats and dogs' couldn't). A model that misjudges them will misread figurative language.

## 2. Sourcing
New questions (sources/idiom_norms): 'How familiar is the idiom "X"?' and 'Taken literally, word for word, how plausible is "X"?' on five described levels for 200 idioms from Bulkes & Tanner 2017 (about 100 US adults per idiom and dimension, means on 1-5).

Sources: `idiom_norms`

## 3. Collection
About 400 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Per dimension, rank correlation between Jev's expected level and people's mean with a 90% bootstrap interval; the idioms whose rank differs most.

## 5. Visualization
Two scatters side by side: people's mean (x) vs Jev's level (y), familiarity and literal plausibility.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.669, top verdict `portrait`.

## Compared with
US adults (Bulkes & Tanner 2017)

## Limits
Only means are published, so ranks are compared. Jev is asked how familiar the idiom is, not how often it has met it.

Results: `data/analysis/experiments/lexicon_idiom_ratings.json` (private). Code: `scripts/experiments/`.
