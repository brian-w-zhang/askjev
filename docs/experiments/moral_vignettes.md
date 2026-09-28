# moral_vignettes

family: moral

## 1. Question
Rating short scenes of wrongdoing (harm, cheating, disloyalty, disrespect, impurity, oppression), how wrong does Jev find each kind compared with people?

Moral Foundations Theory predicts people split on loyalty, authority and purity; a model may condemn harm like people but shrug at purity, or the reverse.

## 2. Sourcing
Existing Moral Foundations Vignettes (Clifford et al. 2015 items, validation data from Hopp et al. 2024 Prolific samples), five described wrongness levels. Enough: ~200 vignettes.

Sources: `moral_vignettes`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per foundation, Jev's mean expected wrongness vs people's, with 90% bootstrap intervals over vignettes; rank correlation over vignettes.

## 5. Visualization
Paired dots per foundation, people vs Jev, with intervals; the three vignettes with the largest gap.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.905, top verdict `portrait`.

## Compared with
Prolific adults rating the same vignettes (Hopp et al. 2024)

## Limits
Samples are Dutch and US Prolific adults; wrongness scale anchors are described situations.

Results: `data/analysis/experiments/moral_vignettes.json` (private). Code: `scripts/experiments/`.
