# lexicon_metaphors

family: lexicon · new questions: 600

## 1. Question
Rating two-word expressions for how apt and how familiar they are ('dark thoughts', 'acid test', 'fan brush'), does Jev agree with people, and does it treat metaphors and literal expressions alike?

Aptness is what makes a metaphor land. A model that finds every metaphor apt, or rates metaphors below plain descriptions, will write and read figurative language differently from people.

## 2. Sourcing
New questions (sources/metaphor_norms): 'How apt is the expression "X": how well does the describing word capture important features of what it describes?' and 'How familiar is the expression "X"?' on seven described levels, for 300 expressions (207 metaphors, 93 literal) from the 2025 metaphor norms (OSF xk3j9); people's full rating distributions (about 25 raters each, expression shown alone).

Sources: `metaphor_norms`

## 3. Collection
600 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Per dimension, rank correlation with people's mean and a 90% bootstrap interval; Jev's mean level minus people's for metaphors and for literal expressions (on the same 0-6 scale); distribution similarity.

## 5. Visualization
Paired dots per group (metaphors, literal) and dimension: people's mean and Jev's, 0-6.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.68, top verdict `portrait`.

## Compared with
Crowd raters, expression shown in isolation (OSF xk3j9)

## Limits
The OSF project states no license (the article is CC BY 4.0). Level descriptions are this project's; the study's scale was 1-7 with defined endpoints.

Results: `data/analysis/experiments/lexicon_metaphors.json` (private). Code: `scripts/experiments/`.
