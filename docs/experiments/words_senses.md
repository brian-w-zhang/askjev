# words_senses

family: words

## 1. Question
Asked how much it experiences each word through sight, hearing, touch, taste and smell, does Jev give the sensory profile people give?

The Lancaster Sensorimotor Norms record how people experience 40,000 words through each sense. A model has no senses; which sense it misjudges most says something about what text leaves out.

## 2. Sourcing
Existing Lancaster questions ('How much do you experience "<word>" by <sense>?', five described levels), about 1,980 words per sense, each with the human mean on the norms' 0-5 scale; plus 1,131 'Through which sense do you mostly experience ...' questions and 2,840 'which of two words ... more through <sense>' pairs with answers from the norms. Enough.

Sources: `lancaster`, `lancaster_modality`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per sense: rank correlation with the human mean, and the mean rating on a common 0-5 scale (Jev's level x 5/4), with 90% bootstrap intervals. For the dominant-sense questions, a confusion table of Jev's answer against the norms' dominant sense.

## 5. Visualization
Paired bars per sense: people's mean vs Jev's mean on 0-5, with the rank correlation printed per row.

## 6. Evaluation
Jev's verdict (evaluator v3): **keep**, head-to-head strength 3.378, top verdict `portrait`.

## Compared with
Lancaster Sensorimotor Norms raters (Lynott et al. 2020, US and UK, MTurk and Prolific)

## Limits
The 0-5 mapping is approximate (Jev's levels are described in words, people's are numbered); the gap for sight is large enough that the conclusion doesn't depend on it, and the rank correlation, which doesn't use the mapping, points the same way.

Results: `data/analysis/experiments/words_senses.json` (private). Code: `scripts/experiments/`.
