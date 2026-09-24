# Dedupe quality (300 labeled Quora pairs: 150 duplicates, 150 hard non-duplicates)

| method | threshold | precision | recall | F1 |
|---|---|---|---|---|
| Jev Noul | 0.5 | 0.59 | 0.80 | 0.68 |
| Jev Noul | 0.7 | 0.63 | 0.69 | 0.66 |
| Jev Noul | 0.9 | 0.61 | 0.40 | 0.48 |
| embedding cosine | 0.85 | 0.45 | 0.83 | 0.59 |
| embedding cosine | 0.9 | 0.38 | 0.62 | 0.47 |
| embedding cosine | 0.95 | 0.37 | 0.32 | 0.34 |
| cosine ≥ 0.8 AND Jev ≥ 0.7 (the ask flow) | – | 0.62 | 0.67 | 0.65 |

Question: `askjev.dedupe.same_question` (a contrastive true/false variant measured worse: F1 0.54). Quora's duplicate labels mean 'same intent',
which is looser than our 'any answer to one answers the other', so some label disagreement is expected.
