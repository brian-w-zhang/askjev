# society_prestige_1965

family: society · new questions: 101

## 1. Question
For 102 occupations from the Pineo-Porter Canadian prestige survey, does Jev order jobs by standing the way Canadians did, and which jobs has it promoted or demoted?

The second classic prestige study, with a census record of each job's pay, schooling and share of women. It shows whether a model's picture of respectable work matches a mid-century public, and where it has moved.

## 2. Sourcing
New questions (sources/occupation_prestige): the same standing question with five described levels for the 102 occupations in Fox's carData `Prestige` data (one duplicate title dropped); the human side is the published mean prestige score.

Sources: `occupation_prestige`

## 3. Collection
101 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Rank correlation between Jev's expected level (base and reversed averaged) and the mean prestige score, with a 90% bootstrap interval; the occupations whose rank moves most; each side's rank correlation with 1971 income, years of education and share of women.

## 5. Visualization
A rank scatter: Canadians' rank (x) vs Jev's rank (y), with the ten largest moves labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.527, top verdict `portrait`.

## Compared with
Canadian adults in the 1965 national prestige survey (Pineo & Porter 1967)

## Limits
Mean scores only; survey from 1965, census from 1971. Titles are the census's (some dated).

Results: `data/analysis/experiments/society_prestige_1965.json` (private). Code: `scripts/experiments/`.
