# resemble_americans

family: resemble

## Why ask this
The General Social Survey has asked Americans the same questions about their lives and attitudes since 1972. That makes it a way to ask not just "how much does Jev sound like Americans?" but "like Americans of when?" A model trained on decades of text might carry an older average, or the most recent one.

That matters for anyone using a model to stand in for the public, in market research or survey drafts: a picture of Americans from thirty years ago would get today's answers wrong in ways that look plausible.

## The people and the data
The General Social Survey interviews a fresh national sample of US adults every year or two. The data is its 1972-2024 cumulative file from NORC at the University of Chicago, weighted as the survey recommends. Each question is compared only across its own two years, so the "earlier" Americans for one question may be from the 1970s and for another from the 2000s.

## What Jev was asked
The GSS questions as the codebook words them, with their answer categories:

> All things considered, how satisfied are you with your family life?
> *Completely satisfied · Very satisfied · Fairly satisfied · Neither satisfied nor dissatisfied · Fairly
> dissatisfied · Very dissatisfied · Completely dissatisfied*

Each question was also asked with the options in shuffled orders, and Jev's answers were averaged over the orders.

## How it was measured
For each question, Jev's spread of answers is compared with each year's Americans, from 0 (nothing in common) to 1 (identical), and the analysis notes which year it lands closer to. If Jev carried no era at all, it would land closer to the later year about half the time. A 90% range comes from resampling the questions.

## Caveats
- **A small lean on a thin margin.**
- **Answering about a life it doesn't have.** Many GSS questions ask about the respondent's own family, job and happiness.
- **Survey years differ.** The two years of a question can differ in how it was fielded (in person, online, a different sample frame), so some of the "era" gap is method, not opinion.
- **Politics removed.** The GSS's political items (party, voting, abortion, guns, immigration, spending and more) were never asked, and religion and sexual morality are hidden by a content filter.
- **Wording from the codebook.** Question wording was rebuilt from the GSS codebooks; answers that respondents volunteer ("don't know", "can't choose") were dropped from both sides.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
