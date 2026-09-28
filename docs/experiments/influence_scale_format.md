# influence_scale_format

family: influence

## Why ask this
Survey designers know the answer scale shapes the answer: add more levels, drop the labels, and people move (Schwarz, 1999). A model filling in questionnaires, or being evaluated with them, carries its own scale habits. If Jev's answers depend on how many boxes it's given, every rating it produces is partly an artifact of the form.

## The people and the data
The questions are 200 rules of thumb from Social Chemistry 101 (Forbes and colleagues, 2020), a dataset of everyday social norms written from Reddit and advice columns, each with a crowd annotator's estimate of how many people agree. They were drawn at random, and Jev's answers were compared across four formats of the same question.

## What Jev was asked
The same question on four scales: the original five described levels, three described levels, seven described levels, and five numbered levels with only the ends described. The seven-level version:

> How many people would agree: "It's good to help people learn about themselves"?
> *Practically no one agrees with it · Very few people agree with it · A minority of people agree with it · About
> half of people agree with it · A majority of people agree with it · Most people agree with it · Practically
> everyone agrees with it*

## How it was measured
For each format, the analysis places Jev's average answer on a 0-to-1 scale (the bottom level is 0, the top is 1), measures how much weight it puts on the top level, and checks whether it orders the 200 rules the same way as on the original scale (rank correlation: 1 same order, 0 no relation).

## Caveats
- **Scales aren't perfectly comparable.** Every scale is put on 0 to 1 to compare them, which assumes the levels are evenly spaced. "About half" is the middle of the 3-, 5- and 7-level versions, but the numbered version only describes its two ends.
- **The level wording was written for this project.** The Social Chemistry annotators saw the dataset's own five categories. The 3- and 7-level wordings were written for this test, and different words for the same step can shift answers on their own.
- **One kind of question.** All the questions ask how many people agree with a rule of thumb. Scales on taste, frequency or intensity could behave differently.
- **The annotators are few.** Each rule has one annotator's estimate on the original scale, so the human comparison is noisy rule by rule.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
