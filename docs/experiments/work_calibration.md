# work_calibration

family: work

## Why ask this
A model's confidence is only useful if you can take it at face value. If "90% sure" means right 90% of the time, a system can act on the sure answers automatically and send the unsure ones to a person. If "99% sure" is often wrong, that shortcut breaks, and it breaks silently.

TypeSafe publishes no calibration numbers for Jev. Work tasks with a right answer make it possible to measure it directly, and to compare Jev's two main question types: yes/no checks and picking one option from a list.

## The people and the data
There are no people here, only answers. Each dataset's answers come from its creators (annotators, experts, or the original authors).

## What Jev was asked
Two kinds of questions. A yes/no check, for example:

> Is the HDFS log for this block anomalous? *(shortened; the log itself comes with the question)*

And a pick-one question over a menu, for example:

> What kind of change does this commit message describe? *fix · feat · refactor · test · docs · chore · style · perf
> · ci · other*

For each, Jev returns a probability for every answer. Its confidence is the probability on the answer it ranks first.

## How it was measured
**Overconfidence** is the average confidence minus the share right: 0 is perfectly honest, positive means Jev claims more than it delivers. It also looks at the share right when Jev is at least 95% sure, field by field.

## Caveats
- **Wrong labels cap the top.** Every task is scored against its dataset's own answers, and some of those are wrong. When Jev is 99% sure and "wrong", some of those cases are label errors, so the true calibration at the top is somewhat better than it looks.
- **Two kinds of questions, two kinds of tasks.** Yes/no and pick-one questions come from different tasks (checks vs classification), so part of the gap may be the tasks, not the question format.
- **Confidence as reported.** Jev's probability on its top answer is used as its confidence, as returned by TypeSafe's API. Probabilities are rounded to whole points, which is why so many list picks show exactly 100%.
- **Public datasets.** These are public research datasets. On a company's own data, the relationship between confidence and accuracy has to be checked again.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
