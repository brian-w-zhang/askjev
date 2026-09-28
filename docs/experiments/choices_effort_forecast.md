# choices_effort_forecast

family: choices

## Why ask this
What gets people to work harder: a small bonus, a donation to charity, a deadline, a lottery, telling them their work matters? In a large experiment, the economists DellaVigna and Pope paid online workers to press two keys as fast as they could for ten minutes, each group under a different one-paragraph incentive. Before revealing the results, they asked 208 economists and psychologists to forecast them. The experts were good at the order, and underrated how well even tiny piece rates work.

People ask models this kind of question all the time: will a bonus help, will a leaderboard motivate my team? Here's a case where the answers are known, and expert forecasts too.

## The people and the data
The workers were recruited on Amazon Mechanical Turk, about 550 per treatment and 9,861 in all, each scoring a point for every "a" then "b" key press. We use the 15 treatments beyond the three benchmarks, with each treatment's actual average score and the 208 experts' average forecast, from the paper's own table.

## What Jev was asked
Jev got the same three benchmark results the experts got, then one treatment at a time:

> In an online experiment, workers on Amazon Mechanical Turk did a simple typing task for 10 minutes: pressing the
> "a" key and then the "b" key, scoring one point for each a-then-b pair. Everyone got the same base pay; groups
> differed only in one paragraph describing a bonus. Three groups' average scores were: "Your score will not affect
> your payment in any way": 1,521 points. "As a bonus, you will be paid an extra 1 cent for every 100 points that you
> score": 2,029 points. "As a bonus, you will be paid an extra 10 cents for every 100 points that you score": 2,175
> points.
>
> Another group's paragraph said: "As a bonus, you will be paid an extra 1 cent for every 1,000 points that you
> score." What was that group's average score?

The answers were 50-point ranges, from under 1,500 to 2,300 or more. Each was asked with the ranges shuffled.

## How we measured it
Jev's forecast is its expected score over the ranges. We compare it with the actual average score: the average error, and whether the treatments come out in the same order (rank correlation: 1 means the same order). The experts' average forecast is scored the same way.

## Caveats
- **A famous study.** The experiment and its results are published and widely discussed; Jev may have read about them. Its forecasts are far from the published numbers, so it doesn't seem to be recalling them.
- **The experts are an average.** We compare Jev with the average of 208 experts' forecasts. The paper found that the average expert forecast beats most individual experts, so the comparison sets a high bar.
- **Fifteen numbers.** There are only 15 treatments. The rank correlation and the average error each rest on 15 comparisons.
- **Answers in bins.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
