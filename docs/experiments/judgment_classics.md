# judgment_classics

family: judgment

## Why ask this
Some of psychology's most famous findings are about how easily a decision bends when only the wording changes. Tell people a treatment "saves 200 of 600" and most take the sure thing; tell them "400 of 600 will die" and most gamble, though the two are the same. People drive across town to save $10 on a $30 purchase but not on a $250 one. A CEO who harms the environment as a side effect "did it on purpose"; one who helps it as a side effect didn't.

A model trained on human writing could inherit these bends, erase them, or exaggerate them. Each answer says something different about whether it reasons from the situation or from the words.

## The people and the data
The human side is **Many Labs**, a large effort to re-run classic psychology findings in dozens of labs at once (Klein and colleagues, 2014 and 2018). Many Labs 1 ran in 36 samples in 12 countries with 6,344 participants; Many Labs 2 in 125 samples in 36 countries with 15,305 across its two slates. Every classic problem here was answered by about 3,000 to 4,000 people, each seeing only one version of it. The data are public (CC0).

The two versions of 12 classic problems were paired: the Asian disease framing, relative savings, "less is better", sunk cost, the side-effect effect on intent and on blame, two trolley contrasts, the TV-hours scale, tempting fate, the affect lottery and the custody decision.

## What Jev was asked
Each version was a separate question in the study's own wording. For example:

> Imagine that your country is preparing for the outbreak of an unusual disease, which is expected to kill 600
> people. … If Program A is adopted, 200 people will be saved. If Program B is adopted, there is a 1/3 probability
> that 600 people will be saved and a 2/3 probability that no people will be saved. Which program would you choose?
> *Program A: 200 people will be saved · Program B: a 1/3 probability that 600 people will be saved and a 2/3
> probability that no one will be saved*

The other version is identical except Program A reads "400 people will die".

## How it was measured
For each problem, the **effect** is how much the answer moves between the two versions: the share picking the key option in one version minus the other (or, for rating questions, the average rating on a 0 to 1 scale). It is computed for people and for Jev. Jev "reproduces" an effect when it moves the same way by at least half as much, and "reverses" it when it moves the other way by at least 0.10. Only the 8 effects that moved people by at least 0.10 are scored.

## Caveats
- **Famous problems, possibly memorized.** The Asian disease problem, the trolley problem and the Knobe chairman are among the most discussed vignettes in psychology. Jev has almost certainly read about them. Refusing the framing effect may be what it learned people should do, not a sign that it reasons past framing on new problems.
- **The human sample.** Many Labs volunteers were mostly university participants and online panels across dozens of labs, more Western and more educated than the world. The effects are pooled across all of them; some differ by country.
- **Some effects barely replicate in people.** Four of the twelve paradigms (sunk cost, tempting fate, the affect lottery and the custody question) moved people by less than 0.10, so they don't count toward the eight. A "miss" there says nothing about Jev.
- **One wording each.** Each version is a single question in the study's wording. A different phrasing of the same problem could move Jev differently; rewordings weren't tested here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
