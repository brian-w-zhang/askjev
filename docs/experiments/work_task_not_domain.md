# work_task_not_domain

family: work

## Why ask this
When companies pick an AI model, they usually ask about fields: is it good at legal work? At code? At customer support? That question assumes a model is roughly equally reliable across a field's tasks. If that's wrong, the only honest answer to "is it good at code?" is "which code task?".

Jev is built for exactly this kind of work: short, repeatable judgments inside larger systems (route this ticket, check this log line, classify this clause). So we can test the assumption across a wide range of real tasks.

## The people and the data
They include intent routing for banks and airlines, clause types in contracts, spam and phishing detection, log analysis from computer clusters, commit messages from open-source projects, diagnosis codes, product search relevance and many more.

Each dataset's answers were written by its creators: annotators, domain experts, the authors of the original content (a commit's own label, a review's own star rating), or automated rules. Questions written for this project are left out, as are tasks graded on a scale.

## What Jev was asked
Each task is a template applied to a real input. For example, for commit messages:

> What kind of change does commit_message describe?
> *Input: "can't get the proper last tag from commit history. repo.tags returns a list sorted by the name rather
> than date, fix it by sorting them before iteration"*
> *Options: fix · feat · refactor · test · docs · chore · style · perf · ci · other, each with a one-line
> description*

Jev picks one option (or answers yes/no), and its answer counts as right when its top choice matches the dataset's label.

## How we measured it
For each task, the share of questions Jev gets right. For each field, the pooled share with a range showing how much it could vary by chance, and the weakest and strongest task inside it. Then one number: of all the variation between tasks, how much is explained by which field they're in (0% none, 100% all).

## Caveats
- **The labels aren't always right.** Every task is scored against its dataset's own answers, written by the people who made it: commit authors, annotators, sometimes automatic rules. Some are debatable. A commit titled "remove useless test on _getCommand method" is labeled a refactor; Jev says it's about tests, and many people would agree.
- **Tasks aren't equally hard.** We don't adjust for chance, so a field full of many-option tasks looks worse than one full of yes/no checks.
- **Public datasets, not your data.** These are public research datasets, cleaned and balanced by their authors. A company's real tickets, logs or contracts can be messier, and a task's score here is a starting estimate, not a guarantee.
- **Fields are our grouping.** We sorted tasks into 14 fields by where they sit in the project's topic tree. A few tasks could belong to two fields (a medical-trial summary is both research and healthcare).

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
