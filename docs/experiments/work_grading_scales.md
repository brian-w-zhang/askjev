# work_grading_scales

family: work

## Why ask this
A lot of work is grading on a scale: how relevant is this search result, how many stars would this review give, how good is this essay, how close are these two sentences in meaning. There are two ways to be useful at it. You can get the **order** right (this item is better than that one), which is enough for ranking. Or you can get the **level** right (this is a 3, not a 2), which is what you need for thresholds and grades.

We measured both, across 11 grading tasks, and looked for tasks where Jev's scale is shifted: consistently harsher or more generous than the people who wrote the labels.

## The people and the data


## What Jev was asked
Each item was one scale question with every grade written out as a situation. For an essay:

> How well is the essay organized?
> *Sentences and events are jumbled, with no order a reader can follow · Events are roughly in order, but the links
> between them are weak or missing and parts feel disjointed · Events follow a logical order from beginning to end,
> with a few abrupt jumps · The story moves clearly from beginning to end, with transitions linking each event*
> *(the essay follows, with a note that it was written by a seventh grader)*

Each task had 3 to 6 grades. Jev also answered with the grades in reverse order.

## How we measured it
Three numbers per task: how well Jev's grades order the items compared with the labels (rank correlation: 1 same order, 0 none); how often Jev's most likely grade is the exact one; and Jev's average grade against the labels' average, to spot a shifted scale.

## Caveats
- **Our level descriptions, their scales.** For each task we rewrote the dataset's grades as short descriptions of situations ("the story moves clearly from beginning to end, with transitions linking each event"). The original raters used their own rubrics. Exact-grade agreement depends on how well our wording matches their lines between grades.
- **Only essays both raters agreed on.** For the essays we kept only cases where the two human raters gave the same score, so the labels are the clearest ones. That makes the essay gap more notable, not less.
- **Different kinds of scales.** Some tasks are really about ordering (search relevance), others about absolute levels (a wine's score, a review's stars). Averaging across them is rough; the per-task numbers are the point.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
