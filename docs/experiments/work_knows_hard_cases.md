# work_knows_hard_cases

family: work

## Why ask this
The most useful thing a model doing checks can know is when it doesn't know. If its confidence drops on the cases a careful person would also find hard, a system can send exactly those to a human and trust the rest. If it's just as sure on hard cases as on easy ones, every answer needs checking.

Public datasets rarely say which cases are borderline. The work cases written for this project do.

## The people and the data
There are no human raters here. The experiment compares four groups of work cases:

## What Jev was asked
Each case was a yes/no or pick-one question over a written input. For example, a know-your-customer check:

> Does the application contain everything the policy requires before this account can be opened?
> *Every item the policy requires for this customer type is present and consistent · At least one required item is
> missing, expired or inconsistent*
> *(the policy and the application follow: required photo ID, proof of address within 3 months, tax ID; the
> applicant's documents)*

## How it was measured
For each group, two numbers: how often Jev's top answer matches the label, and how often it put 95% or more on its answer. Each comes with a range showing how much it could vary by chance, and yes/no is split from pick-one questions.

## Caveats
- **Written for this project, by Claude.** The clear and borderline cases were written for this project by Claude (Anthropic's model) subagents, in TypeSafe's style, with a label and a "borderline" flag set at writing time. They are synthetic: tidier than real inputs, and one author's idea of what's hard. The labels are that author's judgment, not independent ground truth.
- **The writer knew which were hard.** The author marked cases borderline while writing them, so borderline cases may carry tells (hedged wording, conflicting details) that make them look hard. Jev's lower confidence could partly be reading those tells.
- **Few docs examples.**
- **Public data is a different mix.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
