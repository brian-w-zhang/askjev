# work_legal_misses_present

family: work

## Why ask this
In legal review, the two kinds of mistake cost very different amounts. Missing a clause that's really there (an uncapped liability, a most-favored-nation promise) can sink a deal or a lawsuit. Flagging a clause that isn't there costs a lawyer a minute to dismiss.

So before trusting a model with contract or case review, you want to know not just how often it's right, but which way it's wrong.

## The people and the data
The tasks come from **LegalBench** (Guha and colleagues, 2023), a collection of legal reasoning tasks written and labeled by lawyers and law students, plus **CaseHOLD** (Zheng and colleagues, 2021):
- From the Contract Understanding Atticus Dataset.
- **Overruling:** does this sentence from a court opinion overrule an earlier case?
- **Privacy-policy practices:** does this passage of a privacy policy describe a given data practice?
- **Legal area, definitions and consumer contracts:** tagging legal questions posted online by area, spotting definitions in opinions, and yes/no questions about terms of service.
- **Case holdings (CaseHOLD):** is this the real holding of the case cited in a court opinion?

## What Jev was asked
Each item was a yes/no question over the text, with the provision or practice described. For example:

> Does this contract clause contain the kind of provision described?
> *Clause: "The license hereby granted shall be exclusive as to the products described in subparagraphs 2.(a)(1)
> and (2) of this Agreement, but nonexclusive as to all other products covered by this Agreement."*
> *Provision: Competitive restriction exception: does the clause mention exceptions or carve-outs to …*

## How it was measured
For each task, two rates: **misses**, the share of real cases Jev says no to, and **false alarms**, the share of absent cases it says yes to, each with a range showing how much it could vary by chance.

## Caveats
- **Short excerpts.** The contract provisions are judged from a single clause, not the whole agreement. Some provisions only make sense in context (an expiration date that refers to a term defined elsewhere), which inflates misses for those types.
- **Expert labels, one reading.** The labels come from lawyers, law students and legal annotators in the original datasets. Contract language is often ambiguous; a "miss" can be a defensible narrow reading.
- **Balanced by design.** Most tasks are about half yes and half no. In real contracts most clauses don't contain a given provision, so a model that under-flags would look better on real documents than here, and its misses would be harder to spot.
- **Some provision types are small.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
