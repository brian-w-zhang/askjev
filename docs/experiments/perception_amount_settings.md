# perception_amount_settings

family: perception · new questions: 15

## 1. Question
Does 'a few', 'several' or 'many' mean a bigger number to Jev when the thing counted is bigger (a stadium crowd vs a dinner party, grains of rice vs years)?

People scale vague amounts to what's being counted (many grains of rice is more than many years). Whether a model does is a simple test of whether it reads words or situations.

## 2. Sourcing
New questions (sources/perception_words): the three words in five settings, e.g. 'Someone says "A few people were at the stadium when the gates opened." How many people is that?', same 15 bins. No human data for the settings.

Sources: `perception_words`

## 3. Collection
15 new questions, each in three shuffled orders (averaged).

## 4. Scoring
Per word and setting, the bin of Jev's median; the range from the smallest to the largest setting.

## 5. Visualization
Small multiples: one panel per word, the five settings as dots on the log axis.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.731, top verdict `portrait`.

## Compared with
Jev's own reading across settings; no human data here

## Limits
Jev only. The settings were chosen to differ in scale by orders of magnitude.

Results: `data/analysis/experiments/perception_amount_settings.json` (private). Code: `scripts/experiments/`.
