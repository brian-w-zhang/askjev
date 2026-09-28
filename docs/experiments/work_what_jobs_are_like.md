# work_what_jobs_are_like

family: work

## Why ask this
People ask models about careers all the time: what's it like to be a nurse, is being a flight attendant stressful, would I be sitting all day as a web developer. The answer a model gives is its picture of the job. That picture could match what workers experience, or it could be the reputation of the job, the version from TV and headlines.

The US Department of Labor asks workers directly how often they face angry people, deadlines, weather, disease and more. So Jev's picture can be checked against the people doing the jobs.

## The people and the data
The comparison is **O*NET Work Context** (version 29.0), part of the US Department of Labor's occupational database. O*NET surveys people currently working in each occupation, asking how often each condition is part of their job, and publishes the share choosing each answer. The experiment used 12 conditions (dealing with angry people, conflict, working in the weather, time pressure, public speaking, email, exposure to disease, sitting, freedom to make decisions, how serious mistakes are, automation, competition) for 46 well-known occupations, from nurses and cashiers to air traffic controllers and roofers. The data are CC BY 4.0.

## What Jev was asked
Each pair was one question, with O*NET's own five answers:

> How often is a fast food worker exposed to diseases or infections at work?
> *Never · Once a year or more but not every month · Once a month or more but not every week · Once a week or more
> but not every day · Every day*

Jev also answered with the answers in reverse order, and the two are averaged.

## How it was measured
Each answer becomes a level from 0 (never, or the lowest) to 4 (every day, or the highest). For each condition, the analysis ranks the occupations by Jev's level and by the workers' average and compares the rankings (1 means the same order), and averages the gap between Jev and the workers, with a range showing how much it could vary by chance.

## Caveats
- **Who the workers are.** O*NET surveys a sample of people working in each occupation in the US, often a few dozen per job. Their answers describe US jobs at the time of the survey; a cashier's job in another country may differ.
- **Workers describe their own jobs.** Self-reports can understate hazards people have gotten used to, or overstate what feels important about their work. Jev's picture is closer to how a job is described from outside. The gap is between reputation and self-report, not between Jev and objective truth.
- **One typical worker vs a spread.** Jev answers about a typical member of each occupation; the survey spreads across many real workers, from quiet shifts to hectic ones. The comparison uses averages.
- **O*NET's wording.** The five answers are O*NET's own ("Once a week or more but not every day"), but the question sentences were written for this project around each O*NET item.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
