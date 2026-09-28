# society_prestige_1947

family: society · new questions: 45

## 1. Question
For 45 jobs from the classic 1947 NORC prestige survey (physician, banker, carpenter, janitor, shoe shiner...), does Jev give each the standing Americans gave it, and is its ladder tied more to pay and schooling than theirs was?

The North-Hatt survey founded the study of occupational prestige; Duncan used it to show that standing follows education and income. A model's sense of which jobs are respected can be dated (1947 values) or modern, and it can lean on money more or less than people did.

## 2. Sourcing
New questions (sources/occupation_prestige): 'How would you rate the general standing of <a job> as a job?', the survey's five standings (poor to excellent) described, for Duncan's 45 occupations; the human side is the published percentage rating each job excellent or good.

Sources: `occupation_prestige`

## 3. Collection
45 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Jev's probability on 'good' or 'excellent' vs the percentage of 1947 raters; rank correlation; the jobs with the largest gaps; and the rank correlation of each side with the 1950 census shares of high income and high education in the job.

## 5. Visualization
A scatter: 1947 raters' share good or excellent (x) vs Jev's (y), labeled at the largest gaps, diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.928, top verdict `portrait`.

## Compared with
US adults in the 1947 NORC North-Hatt survey (Duncan 1961)

## Limits
The raters are from 1947 and some job titles are dated (streetcar motorman, soda fountain clerk); a gap can be Jev being modern rather than wrong. Only the published percentage exists, no distribution.

Results: `data/analysis/experiments/society_prestige_1947.json` (private). Code: `scripts/experiments/`.
