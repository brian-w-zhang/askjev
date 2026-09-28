# consistency_repeat_noise

family: consistency

## Why ask this
Every comparison on this site rests on a question: how much would Jev's answer change if you just asked again? Many chatbots answer differently each time. Jev returns probabilities rather than a sampled answer, so the question is whether those probabilities are fixed, or wobble, and whether a wobble can change what it would pick.

## The people and the data
No people; Jev against itself. Every two-option question in the corpus was sent in the reversed order twice, as two separate requests at different times.

## What Jev was asked
Any two-option question, twice. For example:

> Which country is larger by area: Liberia or Japan?
> *Japan · Liberia*

(Jev leaned only slightly toward Japan: right, but a near toss-up on a question it should have been sure of.)

## How we measured it
The absolute change in the probability of the same option between the two identical requests, and the share of pairs where the favored option switched, grouped by how far the first answer was from 50/50.

## Caveats
- **Rounded probabilities.** Jev's probabilities come back rounded to whole points, so changes under a point are invisible, and a split a point either side of even can flip on rounding alone.
- **Two-option questions only.** The repeated requests exist only for two-option questions, so the noise on longer lists and ratings is assumed, not measured, to be similar.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
