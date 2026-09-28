# reasoning_traps

family: reasoning

## Why ask this
A handful of puzzles made psychology famous by catching almost everyone. In the **Linda problem**, most people judge "a bank teller who is active in the feminist movement" more likely than "a bank teller", which can't be true. In the **taxi cab problem**, people ignore how rare blue taxis are. In **Monty Hall**, almost everyone refuses to switch doors, and switching wins two times in three. In the **bat and ball**, the answer "10 cents" jumps to mind and is wrong.

A language model has read these puzzles, and their answers, thousands of times. So passing them says little. The real question is whether it still avoids the trap when the story and the numbers are new, and whether it knows when the famous rule *doesn't* apply.

## The people and the data
There are six families of traps: the conjunction fallacy (Linda), base-rate neglect (the taxi cab), Monty Hall, the birthday problem, the gambler's fallacy, and the "cognitive reflection" puzzles (bat and ball, lily pads, widgets). The classics are transcribed from the papers that made them famous (Tversky and Kahneman, Frederick, vos Savant's Parade column).

The only human split for a trap family is Linda's (the taxi cab's 80% is a median answer, not a split): 85% of 142 University of British Columbia students chose the wrong, more detailed answer. For the other traps the comparison is the right answer.

## What Jev was asked
Each puzzle was one multiple-choice question with its answers laid out, for example:

> Maria studied at a music conservatory, practices the violin every day and spends her holidays at music festivals.
> Which is more probable?
> *Maria works in a bank · Maria works in a bank and plays in an amateur orchestra*

Every question was asked with the answers in three different orders, and the answer is the average over those, so the position of the right answer can't drive it.

## How it was measured
For each trap, the analysis compares how often Jev picks the right answer on the famous version, on the new versions, and on the controls, and how often it picks the tempting wrong answer. For number answers, "right" means within one step (5 points) of the correct value.

## Caveats
- **The famous versions may be memorized.** The classic puzzles are all over the internet, with their answers. Getting them right can be recall, not reasoning. That's why the new versions exist, and why the gap between the two columns matters more than the first column.
- **The new versions were written for this project.** The 26 new versions and 3 controls were written by Claude for this project, with the same structure as the classics but new stories and numbers. They have no human data, and a different writer would have produced different traps.
- **Linda is missing.** The original Linda problem was hidden by the content filter that keeps political and sensitive questions off the site (Linda is described as active in social-justice causes). So people's famous result, 85% of 142 students falling for it, has no Jev answer next to it. The six Linda-style versions stand in for it.
- **Numbers are a known weak spot.** Several traps need arithmetic (the birthday problem, the bat and ball). TypeSafe documents counting and raw numbers as a weak spot for Jev, so a miss on those can be arithmetic, not a fallen-for trap.
- **A handful per trap.** Each trap has 3 to 6 new versions.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
