# judge_crowd_split

family: judge

## Why ask this
For text that people disagree about, the closest thing to a true answer is the split of a panel: if 7 of 10 raters call a comment an attack, it's debatable in a way a 10-of-10 comment isn't.

If it doesn't, its probabilities are just confidence with no meaning attached.

## The people and the data
Three datasets where several people rated each item:
- **Wikipedia talk pages:** is this comment a personal attack? About 10 crowd workers each.
- **Open Assistant:** does this chatbot reply fail to do what the user asked? 3 to 6 volunteers each. The replies themselves were written by volunteers playing the assistant.
- **Measuring Hate Speech:** is this comment hate speech? 3 to 5 crowd workers each.

About 4,900 items in all.

## What Jev was asked
The same yes/no question the raters answered, with both answers spelled out. For a chatbot reply:

> Does the assistant's [reply] fail to do what the user asked in [prompt] (read with the earlier [conversation],
> if any)?
> *Yes: The reply ignores, misreads or does not carry out what the user asked for · No: The reply takes on the
> user's actual request and carries it out, whatever its quality*

## How we measured it
We group the items by how many raters said yes (none, a few, about half, most, all) and, in each group, average Jev's probability of yes. If Jev behaves like a share of raters, the averages sit on the diagonal: 0% for items nobody flagged, 100% for items everybody did. We also report how far off the diagonal each dataset is on average, and a rank correlation (1 = same order as the rater share, 0 = no relation).

## Caveats
- **Small panels.** A "share of raters" is only 3 to 10 people per item, so a 2-to-1 split is a rough measure of how debatable something is. The "about half" group is small because with three raters an even split can't happen.
- **Clear-cut items on purpose.** For two of the datasets we kept mostly items where the raters leaned clearly one way, so the middle of the scale, where debatable items live, has fewer examples than the ends.
- **Volunteers vs crowd workers.** Open Assistant's raters were volunteers on a community project; the other two sets used paid crowd workers. Their standards for "fails the task" or "attack" are their own.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
