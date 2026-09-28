# society_prestige_1947

family: society

## Why ask this
Which jobs does society respect? In 1947 the National Opinion Research Center asked Americans to rate the "general standing" of dozens of occupations, from physician and banker to janitor and shoe shiner. The survey founded the study of occupational prestige; the sociologist Otis Dudley Duncan later used it to show that a job's standing closely follows how much education and income go with it.

A model has its own picture of which work is respected, which shows up in career advice, stories and small talk. Comparing it with a mid-century public shows where it agrees, where it is more modern, and whether its ladder is built on money or on schooling.

## The people and the data
The comparison is **Duncan's 45 occupations** from the 1947 NORC survey (often called the North-Hatt study), as published in Duncan's 1961 work: for each job, the share of American adults who rated its standing good or excellent, with 1950 census figures on how many people in the job had high incomes and high education.

## What Jev was asked
> How would you rate the general standing of a contractor as a job?
> *Poor standing: most people look down on this job · Somewhat below average standing · Average standing: an
> ordinary, respectable job · Good standing: people think well of someone who does it · Excellent standing: one of
> the most respected jobs there is*

Each job was asked as written, for "most people", and with the levels reversed.

## How it was measured
For each job, Jev's probability on "good" or "excellent" against the 1947 share. The analysis compares the order of jobs (rank correlation: 1 means the same order) and lists the biggest gaps. Then it checks whether each side's ladder follows the jobs' income and education in the 1950 census.

## Caveats
- **A 1947 public.** The ratings are from Americans in 1947. Jev answers today, so a gap can mean Jev is modern, not wrong: skilled trades have gained respect and some jobs, like "soda fountain clerk", barely exist.
- **One respondent against a crowd.** The 1947 figure is the share of many people; Jev's is one respondent's probability, which tends to be more extreme (0% or 100%) than any crowd's share.
- **Only the published share.** The study's full answers are lost; what survives is the share rating each job good or excellent. The five described levels were written around the survey's own words (poor to excellent standing).
- **Some jobs hidden.** A content filter hid 2 of the 45 jobs from the site.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
