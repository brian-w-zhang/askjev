# words_sound_shapes

family: words

## 1. Question
Asked whether made-up words sound round or pointed, does Jev show the bouba/kiki effect people do, and how strongly?

Almost everyone, in almost every language, calls a round blob 'bouba' and a spiky shape 'kiki'. A model that has only read about it might reproduce the effect, flatten it, or exaggerate it.

## 2. Sourcing
Existing questions on 536 made-up words (McCormick et al. 2015; 'Does it sound more like a round shape or a pointed shape?', seven levels) with about 52 raters each, and the two classic bouba/kiki questions with the pooled answers from 25 language groups (Ćwiek et al. 2022). Enough.

Sources: `pseudoword_shapes`, `bouba_kiki`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Rank correlation over the 536 words between Jev's robust level and the raters' mean; the spread (standard deviation) of each side's ratings; for bouba and kiki, the share choosing the expected shape.

## 5. Visualization
A dumbbell per made-up word sorted by people's rating (people vs Jev), and the two classic words as paired bars.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
McCormick et al. 2015 raters; Ćwiek et al. 2022 participants in 25 language groups

## Limits
Jev reads the spelling and IPA; raters heard or read the words. The bouba/kiki questions are only two, so they illustrate rather than measure.

Results: `data/analysis/experiments/words_sound_shapes.json` (private). Code: `scripts/experiments/`.
