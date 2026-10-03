# work_sure_and_wrong

family: work

## Why ask this
A model that is weak on a task is easy to work with if it says so: a system can send its unsure answers to a person and trust the rest. The dangerous edge is the task where the model is often wrong and just as sure as when it's right, because nothing in its answer warns you.

TypeSafe describes Jev as calibrated and lists the kinds of input that trip it (numbers, dates, long context, option order), but publishes no per-task numbers. So which work tasks hide their misses behind a confident answer is open.

## The people and the data
Each dataset's answers come from its creators. Questions written for this project (TypeSafe-style) are left out, since their answers are the author's.

## What Jev was asked
Each task's own question, as a yes/no check or a pick from a list, for example:

> Do these two pieces of code implement the same functionality? *Both methods do the same job · The methods do different jobs*

> What kind of change does this commit message describe? *fix · feat · docs · ci · …*

## How it was measured
For every task: the share Jev got right (its most likely answer matches the dataset's), its average confidence (the probability it put on that answer) and the chance level (one over the number of options). The **gap** is confidence minus share right, with a 90% interval from resampling the task's questions. A gap near 0 means its confidence can be taken at face value on that task; a wide gap means it claims far more than it delivers.

## Caveats
- **Wrong labels widen the gap.** Every task is scored against its dataset's own answers. Where those labels are noisy (emotions in tweets, commit types), part of the gap is the label's error, not Jev's.
- **Confidence as reported.** Confidence is Jev's probability on its own top answer, as TypeSafe's API returns it, averaged over the task.
- **Chance differs by task.** The gap doesn't depend on chance, but how bad a share right is does, so each task's chance level is shown.
- **Public datasets.** These are public research datasets. On a company's own data, which tasks hide their misses has to be checked again.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
