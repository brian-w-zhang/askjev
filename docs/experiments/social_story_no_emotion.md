# social_story_no_emotion

family: social

## Why ask this
Most of reading a story is filling in what isn't said. "Joan lived next to a dumpster. She never thought much about it until one particular day." Nobody says how Joan feels, but a reader starts guessing: dread, disgust, curiosity.

A reader that often answers "no clear emotion" is being literal where people infer. That's fine in a contract and a problem in a conversation, where most feelings are implied.

## The people and the data
**StoryCommonsense** (Rashkin and colleagues, 2018): five-sentence everyday stories, annotated line by line for each character's feelings by three crowd workers each, using Plutchik's eight basic emotions (joy, trust, fear, surprise, sadness, disgust, anger, anticipation) plus "no clear emotion".

## What Jev was asked
The story up to the line in question, and the nine answers:

> Which emotion best describes the feelings of Joan at the end of [story]?
> *joy or happiness · fear or worry · anger or annoyance · trust or acceptance · disgust · sadness · surprise ·
> anticipation, looking forward to something · no clear emotion*

## How it was measured
The share of all answers that went to each of the nine options, for Jev and for the annotators. Then the story lines where at least two of three annotators named the same real emotion: how often does Jev still say "no clear emotion"?

## Caveats
- **Annotators were asked to find a feeling.** The annotators' task was to label each character's emotion, which may have pushed them away from "none". The gap is partly Jev being literal and partly annotators reading feelings in.
- **Writers themselves sometimes feel nothing.** Where the storyteller's own feeling is known, "nothing much" is a real answer: in another experiment ("Does Jev read the writer, or the other readers?"), Jev's "no particular emotion" matches writers who felt nothing more often than other readers do.
- **A known tendency.** Reading text literally, and not inferring what isn't stated, is on TypeSafe's own list of Jev's known weak spots. This experiment measures how large it is on stories; it isn't a new discovery.
- **Stories cut off mid-way.** Each question shows the story only up to the line being annotated, as the annotators saw it. Early lines carry little emotional information, which invites "no clear emotion".

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
