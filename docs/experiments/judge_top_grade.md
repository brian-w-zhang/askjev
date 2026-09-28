# judge_top_grade

family: judge

## Why ask this
A lot of everyday model work is reading a judgment off a piece of text: how highly did this critic rate the wine, how satisfied is this customer, how good is this essay, do these two sentences mean the same thing? The answer feeds rankings, dashboards and grades.

A reader who shies away from the top of every scale does quiet damage: the excellent blurs into the very good, and the best items never stand out. So the study checked how often Jev gives the top grade compared with how often it's actually deserved.

## The people and the data
Four datasets where the right level is known:
- **Wine Enthusiast tasting notes** with the critic's points (80 to 100), grouped into five bands.
- **Sentence pairs** from the STS Benchmark, with the average of five crowd ratings of how close in meaning they are.
- **Amazon reviews** with the writer's own 1 to 5 stars.
- **Seventh-grade essays** from a public essay-scoring competition, scored by two human graders who agreed.

About 7,400 items in all.

## What Jev was asked
Each dataset got its own question with described levels, the top level spelled out like the others. For the wine: "How highly does the critic rate the wine in [note]?", with only the tasting note shown (no price, grape or region). For sentence pairs: how close in meaning is the second sentence to the first, on six levels paraphrased from the dataset's own guidelines.

## How it was measured
For each dataset, the share of items that truly belong at the top level, against the share where Jev's most likely answer is the top level. The analysis also checks that Jev orders items sensibly overall (a rank correlation: 1 = same order, 0 = no relation), so the gap isn't just noise.

## Caveats
- **Project levels and cut-offs.** Each dataset's scale was turned into described levels (for wine, point bands like 94-100 for "top"), with descriptions written for this project. A top level described as "exceptional" invites caution; a different wording or cut could move the share.
- **Balanced on purpose.** The wine, sentence and review sets were sampled with about equal numbers at each level, so exactly a fifth or a sixth of items belong at the top. That's what makes the comparison clean, but it isn't how often the top grade is deserved in real life.
- **Essays overlap another experiment.** The essay part is the same data as "Jev grades seventh-graders' spelling harder than their human graders", seen from the top of the scale.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
