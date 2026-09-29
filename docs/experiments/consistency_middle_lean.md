# consistency_middle_lean

family: consistency

## Why ask this
Anyone who has filled in a survey knows the middle option: "neither agree nor disagree", "sometimes", "it's fine". Asked how much it would enjoy a spot-the-difference puzzle, a person might say "I'd do one if it was lying around" because that's true, or because it's the easy box to tick. Jev picks the middle a lot, and the question is which of those two it is.

If Jev picks the middle on every scale, its ratings are blurred everywhere. If it picks the middle only for certain subjects, that's a stance: the ratings from those subjects say little, and the rest can be read at face value.

## The people and the data
Each is sorted by the kind of topic it sits under on the map, from taste and personality to values, perception and social norms.

## What Jev was asked
Rating questions with described levels, for example:

> How much would you enjoy working through a spot-the-difference puzzle?
> *You'd give up on it within minutes · You'd finish it but not pick up another · You'd do one when it happened to
> be lying around · You'd seek out a new one on your own · You'd do one every day and hunt for harder ones*

Each was also asked with the levels in reverse order.

## How it was measured
For each question, whether Jev's most likely answer is the middle level. Then the share of questions where it is, by kind of question (from the map's topics), with 90% intervals, and, on the datasets with people's ratings, the same share for the people.

## Caveats
- **Already known.** The middle habit itself isn't new: it shows in Jev's portrait on this site, and people show a milder version on surveys. It isn't on TypeSafe's list of Jev's known weaknesses. What's new here is where it switches on and off.
- **Scales aren't all alike.** The questions come from many sources with different answer wordings, and most have five levels. A middle level described as "neither" invites different answers from one described as a situation.
- **Kinds come from the map.** "Taste", "personality" and the other kinds come from the topic each question sits under on the site's map. Kinds and datasets overlap, so a kind's rate partly reflects which datasets feed it.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
