# resemble_character

family: resemble

## Why ask this
The Open-Source Psychometrics Project's Statistical "Which Character" Personality Quiz is one of the internet's favorite personality tests: you rate yourself on pairs of words ("playful" or "serious"), and it tells you which fictional character's profile yours most resembles, based on how fans rated those characters on the same pairs.

It's a fun question to put to an AI, and a revealing one: the character Jev matches says what kind of personality its self-description adds up to.

## The people and the data
Two sets of ratings, both from the Open-Source Psychometrics Project. First, fans rating characters: between November 2019 and November 2023, visitors rated fictional characters on hundreds of word pairs, 77.4 million ratings in all.

## What Jev was asked
The quiz's self-report items, one word pair at a time:

> Which describes you better: "moody" or "stable"?
> *moody · stable*

## How it was measured
Jev's position on each pair is its probability for the second word, from 0 to 100, like the quiz's slider. For each character, the analysis computes the correlation between Jev's positions and the character's average positions across the shared pairs, which is how the quiz itself finds your match (1 means the same pattern, 0 no relation, -1 the opposite). Before comparing, it subtracts the average character's position on each pair, so traits nearly every character shares don't decide the match. Jev's answers for "most people" are matched the same way.

## Caveats
- **Two very different measurements.** Characters were rated by fans moving a slider between two words; Jev described itself by picking one of the two words, and its probability is used as its slider position. Jev's positions come out extreme (0 or 100 on many pairs), while character averages sit closer to the middle, so the match is about the pattern across pairs, not the size of each difference.
- **Jev describes itself.** Characters are described by the people watching them; Jev describes itself. A match says Jev's self-image has the same shape as a character's reputation, not that Jev behaves like them.
- **Pairs dropped.** Sexual, appearance, mental-health and slur-adjacent pairs were removed before any of this, and the political or religious pairs are hidden by a content filter, so the profile leaves out whole regions of personality.
- **Which characters.** The quiz's character list leans toward popular American and British TV, film and books, so "closest character" means closest among those.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
