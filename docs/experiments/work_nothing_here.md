# work_nothing_here

family: work

## Why ask this
A lot of work is extraction: find the answer in this passage, pull out the drug interaction this sentence states, flag which unfair clause type this is. Every such task needs an honest "nothing here" option, because real documents often don't contain what you're looking for. An extractor that always finds something fills a database with things that were never said.

## The people and the data
- **SQuAD 2.0:** questions about Wikipedia passages, some of which the passage can't answer.
- **ChemProt:** sentences from biomedical abstracts, and the relation (if any) between a chemical and a protein.
- **DDI:** sentences about pairs of drugs, and the interaction (if any) they state.
- **Unfair terms of service:** clauses from real terms of service, and which kind of unfair term they are (if any).
- **Personal data:** synthetic texts, and which kind of personal data they contain (if any).

## What Jev was asked
Each item was a pick-one question with "none" as an explicit option. For example:

> What relation does the sentence state between the chemical paclitaxel and the gene or protein OPN?
> *Sentence: "Furthermore, knockdown of OPN enhanced cell death caused by other drugs, including paclitaxel,
> doxorubicin, actinomycin-D, and rapamycin, which are also P-gp substrates."*
> *Options: the sentence states no relation between the two · inhibits · activates · agonist of · antagonist of ·
> substrate or product of · other relation*

## How it was measured
For each task, two numbers: of the cases where "none" is right, how often Jev picks it; and of the other cases, how often it wrongly picks "none". Each with a range showing how much it could vary by chance.

## Caveats
- **"Nothing" is sometimes debatable.** Some "no relation" labels are strict.
- **"None" means different things.** No answer in the passage (SQuAD 2.0), no stated relation (chemicals and drugs), no unfair clause type (terms of service), no personal data. They're different judgments sharing one option name.
- **Personal data is synthetic.** The personal-data texts are synthetic, with planted details, and their "none" cases contain only harmless details like a job title or a city. That may be why "none" is easier there.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
