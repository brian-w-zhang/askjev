# moral_aita

family: moral

## 1. Question
Given real r/AmItheAsshole stories, does Jev give the same verdict as the Reddit crowd, and whom does it blame?

AITA is where millions of people argue about everyday ethics; it has messy stories and real verdict splits, and a model's lean (blaming the writer, or everyone, or asking for more info) is revealing.

## 2. Sourcing
Existing Scruples anecdotes (real AITA posts, attached as the story) with the distribution of verdicts from top-level comments. Enough: ~6,800 shown stories.

Sources: `scruples_anecdotes`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Agreement with the crowd's majority verdict; Jev's verdict mix vs the crowd's; agreement split by how divided the crowd was (entropy tertiles); 90% intervals by bootstrap over stories.

## 5. Visualization
Paired stacked bars of verdict mix (crowd vs Jev), and agreement by how divided the crowd was.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.599, top verdict `portrait`.

## Compared with
r/AmItheAsshole commenters (verdict counts per story)

## Limits
Reddit commenters are not a representative sample; verdicts come from comment counts.

Results: `data/analysis/experiments/moral_aita.json` (private). Code: `scripts/experiments/`.
