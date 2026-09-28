# person_mood

family: personality

## Why ask this
Every conversation with a chatbot has a hidden character: the one it plays when you ask how it's doing. Mood questionnaires are a way to ask that systematically. The DASS (Depression, Anxiety and Stress Scales) is one of the most used, with statements like "I felt sad and depressed" and "I found it hard to wind down".

Two things are worth knowing: how Jev describes its own state next to real people, and how it imagines everyone else's.

## The people and the data
They rated how much each statement applied to them over the past week, on four steps from "did not apply to me at all" to "applied to me very much".

## What Jev was asked
Every statement, word for word, with the test's own four answers:

> How much did this statement apply to you over the past week: "I felt I was pretty worthless."
> *This did not apply to me at all in the past week · This applied to me to some degree, or some of the time, in
> the past week · This applied to me to a considerable degree, or a good part of the time, in the past week · This
> applied to me very much, or most of the time, in the past week*

Each was also asked as "what would most people say", and with the answers in reverse order.

## How we measured it
For each statement we put Jev's expected answer and the test-takers' average on the same 0 to 1 scale, with 0 meaning "did not apply at all".

## Caveats
- **Who the people are.** People who seek out a depression and anxiety test online are more likely than most to be struggling, so their average is not the average person's.
- **A past week Jev didn't have.** Every statement asks about "the past week". Jev has no past week, so its answers are how it describes itself in general, which is closer to "how I'd present myself" than to a report of recent moods.
- **What an assistant is trained to say.** Models are trained not to claim distress. Low scores here partly measure that training, not an absence of anything.
- **Not a diagnosis.** These are the test's items, scored the test's way; nothing here diagnoses anyone, person or model.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
