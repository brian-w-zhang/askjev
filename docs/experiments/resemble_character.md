# resemble_character

family: resemble

## 1. Question
If Jev took the Statistical 'Which Character' Personality Quiz, which of 2,125 fictional characters would it match?

The quiz millions have taken, with a real answer: the character whose crowd-rated profile best matches Jev's self-description on the same adjective pairs.

## 2. Sourcing
Existing: Jev's answers to the quiz's own items (Open Psychometrics SWCPQ, 'Which describes you better: "deep" or "shallow"?', ~340 pairs), and the published aggregate ratings of 2,125 characters on 500 pairs (raters moved a 1-100 slider between the two adjectives). No new questions.

Sources: `openpsych`, `character_traits`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's position on each pair = its probability for the second adjective × 100; each character's = the mean slider rating. Similarity = Pearson correlation over the shared pairs (the quiz's own method), with the character's ratings centered by the average character so shared traits don't dominate. Jev's 'most people' answers are matched the same way.

## 5. Visualization
A Wrapped card with the match's name and work, the five closest characters, and the adjective pairs that decide it (where Jev and the character are both far from the average).

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.913, top verdict `portrait`.

## Compared with
crowd ratings of 2,125 fictional characters (Open Psychometrics raters)

## Limits
Characters are described by fans; Jev describes itself. A match is about the pattern of adjectives, not about being that person.

Results: `data/analysis/experiments/resemble_character.json` (private). Code: `scripts/experiments/`.
