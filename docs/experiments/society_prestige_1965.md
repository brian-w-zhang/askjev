# society_prestige_1965

family: society

## Why ask this
The second classic study of job prestige, after an American one in 1947, asked Canadians in 1965 to rate the standing of about a hundred occupations. Paired with census records of each job's pay, schooling and share of women, it shows what a mid-century public's ladder of respectable work was built on.

Comparing Jev with it shows two things: which jobs Jev has promoted or demoted relative to that public, and whether its sense of standing rests on money, on education, or on something else.

## The people and the data
**Pineo and Porter's** national survey of Canadian adults (1965, published 1967) gave each of 102 occupations a mean prestige score. The version used here, John Fox's Prestige data for the R statistics language, adds 1971 census figures for each occupation: average income, average years of education, and the share of women.

## What Jev was asked
> How would you rate the general standing of firefighters as a job?
> *Poor standing: most people look down on this job · Somewhat below average standing · Average standing: an
> ordinary, respectable job · Good standing: people think well of someone who does it · Excellent standing: one of
> the most respected jobs there is*

Each occupation was asked as written, for "most people", and with the levels reversed; the two orders are averaged.

## How it was measured
Whether Jev ranks the occupations in the same order as the 1965 scores (rank correlation: 1 means the same order), the occupations whose rank moves most, and how closely each side's ranking follows the jobs' income, education and share of women.

## Caveats
- **A 1965 public, a 1971 census.** The prestige scores are from a Canadian survey in 1965 and the pay, schooling and gender figures from the 1971 census. Several of the jobs have changed beyond recognition since: a 1965 "computer operator" ran machines, a typist typed for a living. A gap can be Jev being modern.
- **The jobs Jev demotes are mostly women's jobs.** That could be a lean against women's work or simply that those clerical jobs have lost standing since; this data can't separate the two.
- **Averages only.** The survey published a mean prestige score per job, not full answers, so the comparison is of rankings. Jev was asked with five described levels of "general standing", the wording of the older American survey.
- **Some jobs hidden.** A content filter hid 2 of the 101 occupations from the site.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
