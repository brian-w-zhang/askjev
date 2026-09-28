# perception_adjectives

family: perception

## Why ask this
"Good", "great", "excellent": the same quality in stronger and stronger doses. People grade things this way all the time, in reviews ("decent" versus "outstanding"), feedback ("fine" versus "impressive") and hedges ("a bit worried" versus "alarmed"). The differences are subtle: is "dim" darker than "dark"? Is "pleased" happier than "content"?

A model that gets these orderings wrong misreads how strong a review, a complaint or a compliment really is.

## The people and the data
Researchers who build language tools have published ordered lists of adjectives for this purpose, and this experiment uses three of them, as collected by Cocos and colleagues (2018): lists ordered by linguists (de Melo and Bansal, 2013), a smaller set by Wilkinson and Oates (2016), and a set ordered by crowd workers (Cocos and colleagues). Each list is a scale from weakest to strongest, such as "plain < unattractive < ugly". Every pair of words on different rungs of the same scale is a question: 749 pairs in all.

## What Jev was asked
One question per pair, with the two words as the options:

> Which word expresses a stronger degree of the same quality: "attractive" or "gorgeous"?
> *attractive · gorgeous*

Every pair was asked twice, once with each word named first, and each of those with the options in both orders. That's 1,498 questions; the answer for a pair is the average.

## How it was measured
For each pair, Jev's probability for the word the list ranks stronger, averaged over both orders. A pair counts as right when that probability is above one half. The results are broken down by how far apart the words sit on their scale and by which word the question named first.

## Caveats
- **The answer key isn't always right.** The orderings come from three published lists, and they disagree with each other on some scales. Jev's most confident "mistakes" are all on one scale where the list ranks "gorgeous" and "lovely" below "beautiful" and "pretty", which most readers would call backwards; another list orders "warm < cold < freezing" on one scale. Some misses are the list's, not Jev's.
- **Naming a word first gives it a small handicap.** Jev leans toward the word named second. Every pair was asked both ways and averaged, so the headline isn't biased; the gap between the two orders shows how much the wording alone can move an answer.
- **Pairs, not ladders.** Jev only ever compares two words. Getting every pair right doesn't guarantee a consistent ladder of five, and "stronger degree of the same quality" is the project's wording, not the lists'.
- **English, and mostly common words.** The scales are English adjectives chosen by researchers, most of them common. Rare, technical or regional words aren't covered.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
