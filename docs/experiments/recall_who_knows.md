# recall_who_knows

family: recall

## Why ask this
Knowing a fact is one thing. Knowing that most people don't know it is what makes an explanation land: it tells you what to spell out and what to skip. A model that knows nearly everything may quietly assume everyone else does too, and pitch every answer too high.

## The people and the data
In 2012, psychologists asked about 670 US college students 299 general-knowledge questions ("What is the name of Batman's butler?") and recorded the share who came up with the answer unaided, with no choices to pick from (Tauber, Dunlosky, Rawson, Rhodes and Sitzman, 2013). The shares run from facts nearly everyone knows ("zebra", 93%) to ones almost nobody does. The per-question shares used here come from a public transcription of the paper's appendix, whose order matches the published ranking almost exactly.

## What Jev was asked
Each of the 299 questions, with the answer shown and twelve ranges to choose from:

> In a 2012 study, US college students were asked this question with no answer choices: "What is the name of the
> rubber object that is hit back and forth by hockey players?" (The answer is: Puck.) What share of the students came
> up with the answer?
> *Answers: 0-2% · 2-5% · 5-10% · 10-20% · 20-30% · ... · 90-100%*

The ranges are finer at the bottom, where most obscure facts sit. Each question was also asked with the ranges in three shuffled orders, and the answers averaged.

## How it was measured
Jev's estimate (the middle of each range, weighted by its probability) against the real share, ranked across all 299 questions and compared (a rank correlation: 1 means the same order). Then the average gap within each third of the questions, from rarely to usually recalled. As a check, the same ranking against a 2020 German version of the study.

## Caveats
- **One group of students, one year.** The shares come from about 670 US college students tested around 2012. Other people, places and years would know different things: in the 2020 German version of the study, far fewer people recalled "Mayberry" and far more recalled "Nero".
- **Recall is harder than recognition.** Students had to produce the answer with no choices. Many more would recognize "Nero" in a multiple-choice list. Jev was told the question was asked with no answer choices, but it may still be picturing a quiz.
- **Jev sees the answer.** Each question shows Jev the answer, so this measures its sense of how widely known a fact is, not whether it knows the fact itself.
- **A transcription of the published table.** The per-question shares come from a public transcription of the paper's appendix. Its order matches the published ranking almost exactly (as reprinted in a 2023 German update), but the individual numbers weren't checked against the original table.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
