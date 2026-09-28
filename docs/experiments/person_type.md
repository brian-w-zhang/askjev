# person_type

family: personality

## Why ask this
Four letters are the most-asked personality question on the internet: people put them in dating profiles and job interviews. Asking a model for its letters is a light question, but it has a sharper twin: when Jev answers the same test "as most people would", does it come out the same type? If not, the gap is how it thinks it differs from people.

## The people and the data
The test is the Open Extended Jungian Type Scales (OEJTS 1.2), published by Open Psychometrics under a non-commercial Creative Commons license. It sorts people on the four Myers-Briggs pairs: introvert or extravert, sensing or intuition, thinking or feeling, judging or perceiving. The site hasn't released response data, so there are no real people here, only Jev and Jev's guess about most people.

## What Jev was asked
Each statement pair is one question, with the two sides as the options:

> Which describes you better?
> *Likes to perform in front of other people · Avoids public speaking*

That's 51 pairs: the 32 scored pairs of the test plus pairs from its development appendix that separate one letter cleanly. Each was also asked for "most people", and with the two options in both orders.

## How it was measured
For each letter pair, the analysis counts the share of statements where Jev leans toward each side, and resamples the statements to get a 90% interval. The type is the side it leans to on each pair; the strength is how far from an even split the lean is.

## Caveats
- **No real people to compare with.** The test's authors haven't published response data, so the only comparison here is Jev's own guess about most people. Nothing on this page says how Jev compares with the people who actually take the test.
- **An open copy, not the MBTI.** The Open Extended Jungian Type Scales is a free research version of the idea behind the Myers-Briggs, not the official test. Types also cut continuous traits into two boxes each, so a slight lean and a strong one get the same letter.
- **Some statements were adapted.** Besides the 32 scored statements of the published test, pairs were added from the test's development appendix, and a few were rewritten so each side reads on its own ("loves it" became "loves being photographed").
- **A model describing itself.** "Likes to perform in front of other people" versus "avoids public speaking" is a question about a life Jev doesn't have; the answer shows how it presents itself.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
