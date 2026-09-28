# reading_event_appraisals

family: reading · new questions: 600

## 1. Question
From someone's account of an event in their life, how well does Jev judge how pleasant and sudden it was and who was responsible, compared with the writer's own ratings and with other readers'?

Appraisal theory says emotions come from how we judge events (was it my fault? did it come out of the blue?). Whether a model infers those judgments like the person who lived them, or like an outside reader, says what it is modeling when it reads about people.

## 2. Sourcing
New questions (sources/crowd_envent): for 150 of the texts, four of the study's appraisal questions (pleasantness, suddenness, the writer's own responsibility, someone else's), each on the study's 1 'not at all' to 5 'extremely' scale.

Sources: `crowd_envent`

## 3. Collection
600 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Per appraisal, rank correlation with the writer's own rating for Jev (expected level, base and reversed averaged) and for the readers' mean; the mean gap from the writer's rating (does Jev assume more responsibility, less pleasantness?), with 90% bootstrap intervals over texts.

## 5. Visualization
Dots per appraisal: rank correlation with the writer, Jev vs readers.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.769, top verdict `portrait`.

## Compared with
the writers' own appraisal ratings, and 5 readers per text

## Limits
Writers were Prolific workers in the UK and US writing about their own lives in 2021; readers saw the text with the emotion words hidden, as Jev does. Five readers per text, so a reader majority can be 3 of 5. The level labels paraphrase the study's 1-5 scale.

Results: `data/analysis/experiments/reading_event_appraisals.json` (private). Code: `scripts/experiments/`.
