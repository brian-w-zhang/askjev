# judge_essays

family: judge

## Why ask this
Automated essay scoring is used on children's writing at scale, for practice tests and sometimes for grades. A grader can be fair in one way and harsh in another: it can read ideas as well as a person does and still punish mechanics much harder.

That combination matters, because the students still learning to spell are exactly the ones a harsh grader would mark down. So we compared Jev with human graders on three separate parts of the same rubric.

## The people and the data
Essays from the Hewlett Foundation's public essay-scoring competition (ASAP, on Kaggle): 1,569 stories by seventh graders about a time they were patient, each scored by two trained human graders on four traits from 0 to 3. We use three traits (ideas, organization, and conventions: spelling, grammar, capitalization and punctuation), and only the scores both graders agreed on: 700 essays per trait.

## What Jev was asked
One question per essay and trait, with the graders' rubric rewritten as four described levels. For conventions:

> How well does the essay [essay] follow the conventions of written English (spelling, grammar, capitalization,
> punctuation)?
> *Errors are so frequent that the essay is hard to read · Frequent spelling, grammar, capitalization or
> punctuation errors distract the reader · There are some errors, but they rarely get in the way of reading ·
> Spelling, grammar, capitalization and punctuation are consistently correct for a seventh grader*

Jev was also told the essay was written by a seventh grader and that placeholders replaced names.

## How we measured it
For each trait, Jev's average score against the graders' average on the 0 to 3 scale, with a 90% range for the difference, and a rank correlation (1 = same order, 0 = no relation) to see whether Jev at least ranks the essays the way the graders do.

## Caveats
- **Placeholders that look like mistakes.** The essays were anonymized before release: names and some capitalized words were replaced with tags like @PERSON1 or @CAPS1. Jev was told so, but a page dotted with tags may still read as sloppy writing, which would hit the spelling and punctuation score hardest.
- **Graders grade for the grade.** The rubric's top level is "consistently correct for a seventh grader". Human graders apply that with a sense of what seventh graders write; Jev may be applying a stricter, adult standard despite the wording.
- **Only essays the two graders agreed on.** We kept essays where both graders gave the same score, which makes the graders' side clear but drops the essays where good graders disagree.
- **One prompt, one grade.** All essays answer one prompt (a story about being patient) from one grade, collected for a public scoring competition. Other ages or kinds of writing could behave differently.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
