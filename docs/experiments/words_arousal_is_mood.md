# words_arousal_is_mood

family: words

## 1. Question
When Jev rates how calming or stirring a word feels, is it rating excitement, as people do, or just how pleasant the word is?

Psychologists separate valence (pleasant or not) from arousal (calm or exciting): 'cuddle' is pleasant and exciting, 'boredom' is unpleasant and calm. Mixing them up is a specific, checkable gap in how a model represents feeling.

## 2. Sourcing
Existing Glasgow Norms questions for the words rated on both pleasantness and calming/stirring (the same word, both questions, one sense). Enough: 468 words with both, and 1,457 arousal ratings overall.

Sources: `glasgow_norms`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Rank correlations among four numbers per word: Jev's and people's arousal, Jev's and people's valence. The telling pair: Jev's arousal against people's valence. The words with the largest gap between Jev's arousal and people's, each way, placed on the same 1-9 scale.

## 5. Visualization
A scatter of people's arousal (x) against Jev's (y), colored by people's pleasantness, with the largest misses labeled.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Glasgow Norms raters (Scott et al. 2019)

## Limits
Jev's arousal levels are described with examples ('Calming: it feels sleepy or soothing, like a quiet evening'), which may pull pleasant words toward the calm end. Mapping Jev's five levels onto 1-9 is linear and approximate.

Results: `data/analysis/experiments/words_arousal_is_mood.json` (private). Code: `scripts/experiments/`.
