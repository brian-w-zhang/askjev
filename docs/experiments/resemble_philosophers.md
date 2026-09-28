# resemble_philosophers

family: resemble

## Why ask this
The PhilPapers Survey asks professional philosophers where they stand on the field's big questions: free will, the nature of consciousness, whether moral facts exist, the trolley problem, Newcomb's problem. It's the closest thing philosophy has to a census of expert opinion.

A model trained on their writing might echo the consensus, split the difference, or confidently take sides the profession rejects. Which one tells you what Jev does with contested ideas.

## The people and the data
The 2020 PhilPapers Survey (Bourget and Chalmers, 2023): the "target faculty", about 1,800 professional philosophers at leading departments, each saying which positions they accept or lean toward. We use the share choosing each position on the 100 main questions, 88 of them shown on the site.

## What Jev was asked
Each question as the survey frames it, with a short gloss of the positions:

> In Newcomb's problem, a highly reliable predictor has put $1,000,000 in an opaque box only if it predicted you
> would take just that box; a transparent box holds $1,000. Do you take one box or both boxes?
> *Take only the opaque box · Take both boxes · Another view: an alternative position, agnostic or undecided, no
> fact of the matter, or the question is too unclear to answer*

## How we measured it
After setting "another view" aside on both sides, we check whether Jev's top answer is the philosophers' most common named position, and how similar the two splits are. We then list the questions where Jev is most confident against the majority.

## Caveats
- **It may know the answers.** The PhilPapers surveys (2009 and 2020) are widely discussed, and their headline results appear in papers, blogs and encyclopedias. Agreeing with the majority may partly be recall of the survey, not reasoning to the same view.
- **"Other" is set aside.** Philosophers could answer "another view", "undecided" or "no fact of the matter", and many did. We remove that option on both sides before comparing, because it pools many different positions.
- **Glosses we wrote.** Each question carries a short gloss of the positions, written for this project so a non-specialist question makes sense. The philosophers answered the survey's terse labels, which experts read without help.
- **Topics left out.** A content filter hides the survey's political and religious questions (abortion, capital punishment, God and a few others), so this covers metaphysics, mind, knowledge, ethics and science, not religion or politics.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
