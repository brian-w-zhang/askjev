# social_shame_as_guilt

family: social

## 1. Question
When people describe a time they felt ashamed, does Jev name shame, or does it call it guilt?

Psychologists separate the two: guilt is about something you did, shame is about who you are. A reader that folds shame into guilt misses the more painful feeling, and the confusion should run one way only.

## 2. Sourcing
Existing questions from two datasets where the writer named their own feeling: ISEAR (people in 37 countries describing a time they felt one of seven emotions, guilt and shame among them) and EmpatheticDialogues (short situations written under one of 32 emotion labels, 'ashamed' and 'guilty' among them). Jev picks one emotion from the dataset's list. Enough: about 400 shame and 400 guilt stories in ISEAR, about 90 of each in EmpatheticDialogues.

Sources: `isear`, `empathetic_dialogues`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each dataset, the share of shame stories Jev calls guilt and the share of guilt stories it calls shame, with 90% bootstrap intervals over stories; the gap between the two directions is the finding.

## 5. Visualization
Paired bars per dataset: shame read as guilt vs guilt read as shame.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.797, top verdict `portrait`.

## Compared with
The writers' own labels for their feelings

## Limits
The writer's label is one person's word for a mixed feeling; ISEAR stories were translated and shortened. Jev sees only the list of emotions the dataset offers.

Results: `data/analysis/experiments/social_shame_as_guilt.json` (private). Code: `scripts/experiments/`.
