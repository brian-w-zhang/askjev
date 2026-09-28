# perception_crowd_of_100

family: perception · new questions: 600

## 1. Question
When 100 people read the same two sentences and split on whether the second follows, does Jev's probability look like the crowd's split, and does it side with the majority as often as a typical person does?

Most datasets give one 'right' label; ChaosNLI shows that many items have none. That makes it possible to ask a better question than accuracy: does the model know when people disagree?

## 2. Sourcing
New questions (sources/chaosnli): 600 items from ChaosNLI (Nie, Zhou & Bansal 2020), 300 each from SNLI and MNLI, sampled evenly across how split the 100 labels are. Options in plain words (the second sentence is true / might or might not be / is false, given the first).

Sources: `chaosnli`

## 3. Collection
600 new questions, each asked as written and with the three options in shuffled orders (averaged).

## 4. Scoring
Agreement with the crowd's majority, overall and by how split the crowd is (entropy terciles), against the typical person's agreement with the majority (the majority's share); rank correlation between Jev's confidence and the crowd's agreement; similarity of the distributions.

## 5. Visualization
Binned dots: the crowd's majority share (x) vs Jev's probability on that answer (y), with the diagonal and the typical person's agreement line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.303, top verdict `portrait`.

## Compared with
100 crowd workers per item (ChaosNLI)

## Limits
The options are paraphrased from the NLI labels; ChaosNLI's workers saw the standard labels.

Results: `data/analysis/experiments/perception_crowd_of_100.json` (private). Code: `scripts/experiments/`.
