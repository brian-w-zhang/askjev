# knowledge_calibration

family: knowledge

## Why ask this
A model that knows when it doesn't know is far more useful than one that is merely accurate. If an answer comes with "90% sure", you want it to be right about nine times in ten. TypeSafe doesn't publish calibration numbers for Jev, so this measures it directly, across every kind of fact question in the corpus.

## The people and the data
No people here: the comparison is the right answers. The questions come from 23 sources with answer keys: Wikidata facts (capitals, sports, sizes, dates), Pantheon (who's more famous), World Bank country comparisons, USDA nutrient comparisons, AnAge animal lifespans, school and professional exams, pub trivia, and yes/no reading and search questions.

## What Jev was asked
Each question is multiple choice, or yes/no. For example:

> Which option best completes this statement: "Older adults are able to improve their memories and reduce their
> anxiety about declining memory when ..."?
> *They simply learn a number of memory improvement techniques · They learn that many aspects of memory do not
> decline and some even get better · Older adults cannot do either of these · They learn about memory and aging
> and learn some techniques*

Jev returns a probability for every option; its confidence is the probability it puts on its top pick.

## How it was measured
The average distance between confidence and accuracy, weighted by how many questions sit in each band, is the calibration error: 0 is perfect.

## Caveats
- **Answer keys have errors.** Some of these datasets have wrong answer keys (the college virology exam questions are known for them). Every wrong key makes a correct, confident Jev look overconfident, so the overconfident sources may be partly key errors.
- **The mix sets the curve.** The overall average leans on those; the per-source gaps are the fairer comparison.
- **Multiple choice, not open answers.** Every question comes with options to pick from. Confidence on open questions, where Jev has to produce the answer, can behave very differently.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
