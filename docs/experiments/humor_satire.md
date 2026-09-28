# humor_satire

family: humor

## 1. Question
Shown a headline from The Onion or a real news site, how often does Jev mistake satire for news, or news for satire?

Satire works by reporting the absurd with a straight face; a model that reads literally (a weakness TypeSafe documents, 01-jev §6.1) should miss some of it. The misses show which jokes are too deadpan.

## 2. Sourcing
Existing questions ('Is `headline` sarcastic?') on the News Headlines Dataset for Sarcasm Detection (Misra 2019): Onion headlines are satire, HuffPost headlines are not. Enough: 1,206 headlines.

Sources: `sarcasm_headlines`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of Onion headlines Jev calls straight news, share of real headlines it calls satire, each with a 90% bootstrap interval; accuracy by Jev's confidence.

## 5. Visualization
A 2x2 table (real source vs Jev's call) with the share in each cell, and the misses listed.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
the headline's real source (The Onion or HuffPost)

## Limits
Literal reading is a documented Jev weakness (01-jev §6.1); this puts a number on it for satire. Some HuffPost headlines are themselves wry, and the dataset is from 2014-2018.

Results: `data/analysis/experiments/humor_satire.json` (private). Code: `scripts/experiments/`.
