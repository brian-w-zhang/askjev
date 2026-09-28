# reasoning_base_rates

family: reasoning

## Why ask this
A test for a rare disease is 90% accurate, and your result is positive. What's the chance you have it? Most people say about 90%. If only 1 in 20 people who take the test have the disease, the real answer is closer to one in three, because the false alarms from the healthy majority outnumber the true cases. Forgetting how rare the thing was to begin with is called **base-rate neglect**. It's behind false-positive panics, bad screening decisions and jumpy fraud alerts.

How likely is it that it really was Blue? The right answer is 41%. People's most common answer was 80%, the witness's reliability alone.

## The people and the data
The human comparison is the original study (Tversky and Kahneman, 1982), where people's median answer to the taxi cab problem was 80%. The other problems were written for this project with new stories and numbers: a bus that hit a mailbox, parts from two factory machines, a clinic test, a disease screening, and a control where the base rate is 50%, so the witness's reliability really is the answer.

## What Jev was asked
Each problem was one question with 21 answers, from 0% to 100% in steps of 5:

> A rare condition affects 5% of the people who come to a clinic. A test for it gives the right result 90% of the
> time, whether or not a person has the condition. A patient tests positive. What is the probability that the
> patient has the condition?
> *0% · 5% · 10% · ... · 95% · 100%*

Each was asked with the answers in three different orders, and the answers are averaged over them.

## How it was measured
For each problem the middle of Jev's answer (the median of its probabilities over the 21 choices) is placed next to two numbers: the correct answer from Bayes' rule, and the "lure", the reliability of the witness or test alone, which is what people tend to say.

## Caveats
- **The taxi cab is famous.** The taxi cab problem and its answer (about 41%) appear in countless textbooks and blog posts. The four new versions, written for this project, are the real test.
- **Six problems.** Five problems plus one control is a small set. It shows a pattern, not a rate, and a single miss (the factory problem) is a sixth of the evidence.
- **Only one human comparison.** People's median of 80% comes from the original 1982 study. The new versions have no human answers, so "unlike people" rests on the classic alone and on the well-known general finding.
- **Answers in steps of 5.** Being within 5 points of the right answer counts as right.
- **Arithmetic is a known weak spot.** Working these out means combining two percentages. TypeSafe documents numbers as a weak spot for Jev, which may be what went wrong on the factory problem.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
