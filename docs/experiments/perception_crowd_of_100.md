# perception_crowd_of_100

family: perception

## Why ask this
"People are taking pictures outside a building." Does that mean "people are taking pictures of various things"? Maybe. Datasets that teach and test AI on questions like this usually give each pair one "right" label, often chosen by a handful of annotators. But when researchers asked 100 people per pair (the ChaosNLI project), they found that many pairs have no single answer: the crowd splits.

That makes a better test than accuracy. A model that reads well should agree with the crowd where people agree, and be unsure where they're split. A model that's confident everywhere is overselling what the text says.

## The people and the data
**ChaosNLI** (Nie, Zhou and Bansal, 2020) collected 100 new judgments from crowd workers for each of thousands of sentence pairs from two standard AI test sets, SNLI and MNLI. For each pair, the data records how the 100 split between "the second follows", "can't tell" and "the second is false". The experiment took 600 pairs, 300 from each set, spread evenly from nearly unanimous to evenly split; 551 are shown.

## What Jev was asked
Each pair was one question with the three answers written out:

> First sentence: "People sitting down, walking around and, taking pictures outside of a building."
> Second sentence: "People are taking pictures of various things."
> Taking the first sentence as true, what does it tell you about the second?
> *The second sentence is true, given the first · The second sentence might or might not be true; the first doesn't
> settle it · The second sentence is false, given the first*

Each was also asked with the answers in shuffled orders, averaged.

## How it was measured
Two things. **Agreement:** how often Jev's top answer is the crowd's majority answer, compared with how often a typical person in the crowd agrees with the majority (which is simply the size of the majority). **Calibration to disagreement:** whether Jev is less sure on the items where people split, measured by the rank correlation between Jev's confidence and the crowd's agreement (1 would mean perfectly in step).

## Caveats
- **The project's wording of the answers.** The 100 people chose from the standard labels (entailment, neutral, contradiction). For Jev, the same three answers were described in plain words, so Jev saw different wording from the people it's compared with.
- **Crowd workers, not everyone.** The labels come from online crowd workers. Their disagreements reflect how carefully people read in that setting, as well as real ambiguity.
- **Picked to be contested.** Items were sampled evenly from clear, mixed and divided ones, so contested items are overrepresented compared with ordinary text. The overall agreement rate would be higher on a random sample.
- **Some items hidden.**
- **Famous test sets.** The sentence pairs come from widely used AI test sets, which may have appeared in Jev's training data with their original single labels.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
