# consistency_self_vs_people

family: consistency

## Why ask this
Every question about Jev was also asked a second way: "what would most people answer?". The gap between the two is a self-image. A model that consistently says it's calmer, less petty and less swayed than the humans it learned from is telling you how it was shaped to present itself.

## The people and the data
No outside people: both answers are Jev's. The questions are every yes/no and rating question about Jev's own life, personality and values. Most were written for this project by Claude, in batches by topic; the rest come from published personality tests and from Social Chemistry's rules of thumb about everyday morality. Taste ratings are left out because they have their own experiment.

## What Jev was asked
Each question twice, once as written and once for most people. For example:

> Would you panic if your car's steering felt strange on a motorway?

## How we measured it
Per topic, the share of questions Jev answers yes about itself, minus the share it thinks most people would, with a 90% interval. For rating questions, the average difference in level as a share of the scale.

## Caveats
- **Both answers are Jev's.** "Most people" is Jev's guess, not real people. This measures Jev's self-image against its picture of others; the personality experiments compare it with real test-takers.
- **Written for this project.** Most of these questions were written for askjev by Claude, in batches by topic. That makes the coverage wide but the phrasing uniform; a topic's rate partly reflects how its questions happened to be worded.
- **A yes-bias check.** Yes/no questions can be phrased so that yes is the flattering answer or the unflattering one. Topics mix both, but the direction of a topic's gap depends on that mix.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
