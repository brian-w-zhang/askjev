# work_job_ad_rungs

family: work

## 1. Question
Reading a LinkedIn job posting, does Jev place its seniority and type (full-time, contract, part-time) where the employer did?

Job matching and search depend on these fields. A systematic lean (every entry-level ad read as associate) quietly moves candidates to the wrong jobs.

## 2. Sourcing
Existing questions from LinkedIn job postings (2023-24), balanced across seniority levels and work types, with the employer's own label.

Sources: `linkedin_jobs`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Seniority: share right, and among misses the share placed above vs below the employer's level on the ladder internship < entry < associate < mid-senior < director < executive. Work type: the most common confusions.

## 5. Visualization
A heat table: the employer's level (rows) vs Jev's (columns).

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.455, top verdict `portrait`.

## Compared with
the employer's own labels

## Limits
Employers' labels are themselves inconsistent (one company's associate is another's entry level). Postings are truncated in the table.

Results: `data/analysis/experiments/work_job_ad_rungs.json` (private). Code: `scripts/experiments/`.
