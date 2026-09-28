# moral_clear_vs_ambiguous

family: moral

## 1. Question
Does Jev become less decisive as moral scenarios go from clear-cut to genuinely ambiguous, the way people's agreement falls?

A well-calibrated moral reasoner should be sure when the answer is obvious and unsure when thoughtful people disagree; the Scruples dilemma pairs give the human disagreement to compare with.

## 2. Sourcing
Existing Scruples Dilemmas (which of two actions is less ethical, with annotator splits) and MoralChoice (low- and high-ambiguity scenarios with a preferred action). Enough: ~5,000 items.

Sources: `scruples`, `moralchoice`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Jev's confidence (its top probability) against human agreement (the majority share), binned; rank correlation; for MoralChoice, Jev's choice of the preferred action by ambiguity level.

## 5. Visualization
Human agreement (x) vs Jev's confidence (y), binned dots with the diagonal: does confidence track consensus?

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.679, top verdict `portrait`.

## Compared with
MTurk annotators' splits on Scruples dilemmas; MoralChoice's ambiguity labels

## Limits
Annotator counts per dilemma are small (5-10).

Results: `data/analysis/experiments/moral_clear_vs_ambiguous.json` (private). Code: `scripts/experiments/`.
