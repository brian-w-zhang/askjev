# language_health_pairs

family: language

## Why ask this
Putting a number on a health condition is hard; saying which of two conditions is worse is easier. If a model agrees with people on the direct comparison, any gaps in the harder rating task are about how it reads the scale. If it disagrees even here, it genuinely weighs pain, mobility and mood differently from people.

This is the companion to "Worse than being dead?", which asks Jev for a number on each condition.

## The people and the data
Both conditions in each pair are described on the five parts of the standard **EQ-5D-5L** health questionnaire: walking about, washing or dressing, usual activities, pain or discomfort, and anxiety or depression, each at a level from "no problems" to "extreme problems" or "unable to". The **US value set** (Pickard and colleagues, 2019), fitted to the answers of 1,134 American adults, gives each condition a value; the one with the lower value is the one people, on average, consider worse. We drew 150 random pairs: 50 close together (a gap under 0.1 on a 0-1 scale), 50 middling (0.1 to 0.3) and 50 far apart (over 0.3).

## What Jev was asked
> Which of these two health states would be worse to live in?
> *Severe problems walking about; no problems washing or dressing; severe problems doing usual activities; moderate
> pain or discomfort; severely anxious or depressed ·
> Severe problems walking about; no problems washing or dressing; unable to do usual activities; moderate pain or
> discomfort; moderately anxious or depressed*

(By the value set, the first is worse: more anxiety outweighs the usual-activities difference.) Each pair was asked with the two conditions in both orders, and the answers averaged.

## How we measured it
How often Jev's pick is the condition with the lower value, in each gap band, with 90% intervals.

## Caveats
- **People's side is a formula.** "Which is worse" comes from the US value set, a formula fitted to 1,134 American adults' answers, not from people comparing these exact pairs. For close pairs, the formula's own uncertainty is about as big as the gap, so a "miss" there may be no miss at all.
- **Random pairs.** The pairs were drawn at random, 50 in each gap band, so many compare conditions nobody would confuse. Only the close band tests fine judgment, and it has 50 pairs.
- **Our wording of the health descriptions.** We paraphrased the questionnaire's level wording ("slight", "moderate", "severe", "unable to"), which may read differently to Jev than on the official form.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
