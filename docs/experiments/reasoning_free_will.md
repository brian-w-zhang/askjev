# reasoning_free_will

family: reasoning

## Why ask this
If everything you do was fully caused by what happened before, down to the beginning of the universe, can you be blamed for anything? Philosophers have argued this for centuries. In the 2000s, experimental philosophers asked ordinary people, and found a split. Described abstractly, most people say no: in a determined universe, nobody is fully responsible. Told a vivid story about a particular person doing something wrong, many say yes, that person is responsible anyway.

That split between principle and case says a lot about how someone weighs rules against gut reactions. A model trained on philosophy might follow the principle every time, or it might react to the story like people do.

## The people and the data
The stories and people's answers come from two well-known studies:
- **Nichols and Knobe (2007):** a universe where everything is caused by what came before, described in detail, then either an abstract question (can anyone be fully responsible?) or a specific person (Mark, who cheats on his taxes as he has many times before). In the abstract, 14% said yes; for Mark, 23% said it's possible he's fully responsible.
- **Nahmias and colleagues (2005):** a supercomputer that predicts everything with perfect accuracy, including that Jeremy will rob a bank years before he's born. 76% said Jeremy robs the bank of his own free will.

## What Jev was asked
The studies' stories, word for word, each ending in a yes-or-no question:

> Imagine a universe (Universe A) in which everything that happens is completely caused by whatever happened before
> it. [...] In Universe A, as he has done many times in the past, Mark arranges to cheat on his taxes. Is it possible
> that Mark is fully morally responsible for cheating on his taxes?
> *Yes · No*

Each was also asked with yes and no swapped, and for "most people"; the numbers here are Jev's own answer, averaged over both orders.

## How it was measured
Jev's probability of "yes" on each story, next to the share of people in the original study who said yes.

## Caveats
- **The most important story is missing.** Nichols and Knobe's headline case is Bill, who murders his family in a determined universe; most people say he's fully responsible (72% in the study), reversing their abstract answer. The content filter that hides violent questions from the site removed it, so the contrast the study is known for can't be tested here. That leaves three stories, not four.
- **One of the numbers is secondhand.** The 76% for Jeremy comes from secondary summaries of Nahmias and colleagues' study, not from reading the paper itself; the 23% for Mark comes from a published critique quoting the paper's table.
- **Wording from different studies.** The stories are the studies' own, but they come from two different papers with different descriptions of determinism (a caused universe versus a perfect predicting supercomputer). The framing, not just the case, may move the answers, for people and for Jev.
- **Yes or no only.** People in these studies answered one way or the other; Jev's answer is a probability of yes. A low probability is a firm no, but it isn't the same kind of number as a share of people saying yes.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
