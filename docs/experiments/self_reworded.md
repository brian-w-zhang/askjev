# self_reworded

family: self

## Why ask this
People rarely ask the same thing the same way twice. Asking a model the identical question again moves its answer by about a point (see "Ask Jev the same thing twice"). Rewording is the realistic test: how much of an answer is about the question, and how much is about its wording?

## The people and the data
There are no people here. When the project removed duplicate questions, it found pairs that ask the same thing in different words (matched automatically by similar meaning, then confirmed by Jev) and linked them.

## What Jev was asked
Each question on its own, never side by side, for example:

> Would you tell a teacher you were marked right on a question you got wrong?

and, as a separate question:

> If a teacher accidentally gives you full marks on a question you got wrong, should you point it out?

## How it was measured
For each pair, the gap between Jev's two probabilities of yes, and whether both land on the same side of 50%. The same among "firm" pairs, where both answers are at least 70/30. Compared with the noise from asking the identical request twice.

## Caveats
- **"Same question" is a judgment call.** The pairs were matched automatically (by similar meaning, then confirmed by Jev) when the project removed duplicates. Some differ in more than wording ("would you" vs "could you", "always" vs "sometimes"), so part of the 8-point gap is real difference in meaning.
- **Opposites set aside by a word list.** Pairs whose wording flips the sense ("fake" vs "real", any "not") were set aside, because opposite answers to opposite questions are consistent. The word list is imperfect: it catches some harmless rewordings and misses some flips.
- **Questions written by Claude.** At least one question in each pair comes from the banks written for this project by Claude (Anthropic's model). Rewordings by one writer may be closer than the ways different people would ask.
- **Hidden twins.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
