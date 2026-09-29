# self_could_vs_would

family: self

## Why ask this
Across tens of thousands of real questions, those starting "Can...?" get far more yeses from Jev than those starting "Will...?" (see "Can? Yes. Will? No."). But different questions start with different words for different reasons. Pairs of questions that ask the same thing with a different opening verb separate the word from the topic: whatever difference is left is the word.

The same thing happens in everyday use. Ask "Could you see yourself living abroad?" and "Would you live abroad?" and a careful person gives related but different answers. If a model's yes rises and falls with the verb more than the situation, anyone reading its answers to surveys, interviews or advice questions is partly reading the phrasing.

## The people and the data
There are no people here: the comparison is Jev against itself. The questions come from banks written for this project by Claude, and in every pair at least one comes from the banks about Jev itself (its habits, tastes and relationships). Where two questions ask nearly the same thing, the project's duplicate matching pairs them up. The chart shows the pairs of opening words with at least 15 examples.

## What Jev was asked
Each question on its own, never side by side:

> Would you date someone you met at a funeral?

and, separately:

> Could you fall for someone you met at a funeral?

## How it was measured
For each pair, the difference in Jev's probability of yes between the two wordings, oriented so a positive number means the first word gets more yes. Averaged per pair of opening words, with a range for chance variation.

## Caveats
- **Few pairs for the biggest effect.**
- **"Could" can honestly mean less.** "Could you fall for someone you met at a funeral?" asks whether it's possible; "Would you date them?" asks whether you'd do it. A careful reader should say yes more often to "could". The experiment measures the wording's effect whichever reading Jev takes.
- **Matched automatically.** The pairs come from the project's duplicate matching (similar meaning, confirmed by Jev), so some differ in a second word too ("date" vs "fall for").
- **Questions written by Claude.** The questions come from banks written for this project by Claude (Anthropic's model), so the pairs reflect one writer's habits of rephrasing.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
