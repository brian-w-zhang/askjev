# work_evidence_retreat

family: work

## Why ask this
A lot of AI checking comes down to one question: does this evidence support the claim, contradict it, or not settle it? When a checker gets a clear case wrong, how it's wrong matters. Saying "can't tell" when the evidence actually supports a claim sends the case to a person, a cost of time. Saying "contradicts" when it supports, or the reverse, certifies something false.

## The people and the data
- **FEVER** and **VitaminC:** claims checked against Wikipedia sentences (VitaminC's come from real revisions of Wikipedia articles).
- **SciFact:** scientific claims checked against research abstracts.
- **MultiNLI** and **Adversarial NLI:** everyday sentence pairs, the second written by people trying to fool models.
- **ContractNLI:** statements about non-disclosure agreements.
- **Evidence Inference:** clinical-trial reports; does the treatment increase, decrease or not change an outcome?

## What Jev was asked
Each item was a three-way question over a source and a statement:

> Taking everything in the source as true, does the statement follow from it, contradict it, or neither?
> *Source: "Well, let's see, there's I guess one of the favorite author's of mine is Isaac Asimov who wrote some of
> the best science and science fiction that was ever written."*
> *Statement: "One of my favorite authors is Isaac Asimov."*
> *Options: follows · neither · contradicts*

## How we measured it
For each dataset we take the clear cases, where the answer is "supports" or "contradicts", and look at Jev's mistakes on them: what share went to "can't tell" (a retreat) versus the opposite verdict (a flip). We also check how often Jev correctly says "can't tell" when that's the answer.

## Caveats
- **"Can't tell" means different things.** Each dataset defines the middle answer its own way: not enough information (FEVER), no significant difference (clinical trials), not mentioned (contracts). A retreat in one isn't the same act as in another.
- **Where the labels come from.** Adversarial NLI statements were written by people trying to fool earlier models; the clinical-trial answers are kept only where every annotator agreed; ContractNLI covers 17 fixed statements about non-disclosure agreements. The datasets' hard cases differ, and so do their label errors.
- **Few errors in some sets.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
