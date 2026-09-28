# reading_event_appraisals

family: reading

## Why ask this
Psychologists who study emotion (appraisal theory) argue that feelings come from how people judge events: was it pleasant? did it come out of nowhere? whose fault was it? In that view, blaming someone else and blaming yourself lead to different feelings. Whether a model infers those judgments like the person who lived through the event, or like an outside reader, says what it's really modeling when it reads about people.

## The people and the data
The crowd-enVent corpus (Troiano, Oberländer and Klinger, 2023) asked people on the survey platform Prolific to describe an event from their own life and rate it on many appraisal questions, from "not at all" (1) to "extremely" (5). Five other people later read each text, with its emotion words hidden, and rated it on the same questions. This experiment uses 150 texts and four of the questions: how pleasant the event was, how sudden, how responsible the writer was, and how responsible someone else was.

## What Jev was asked
Each text and question on its own, with five described answers:

> Someone wrote *(the story below)* about an event in their own life. How responsible was someone else for the event?
> *"I found out a puppy was available for adoption."*
> *Nobody else was responsible · Someone else was slightly responsible · Someone else was moderately responsible ·
> Someone else was very responsible · Someone else was entirely responsible*

Each question was also asked with the answers in reverse order, and the two averaged.

## How it was measured
For each of the four questions, how well Jev's ratings follow the writer's own ratings across texts (a rank correlation: 1 means the same order), next to how well the readers' average does. Then Jev's average gap from the writer, in levels on the 0-4 scale, to see which way it leans.

## Caveats
- **The project's wording of the answers.** The study used a 1 to 5 scale from "not at all" to "extremely". Jev got the same five steps in words ("Someone else was slightly responsible" ...), a paraphrase rather than the study's exact form.
- **Who wrote and who read.** Writers and readers were paid Prolific workers whose first language is English, from six English-speaking countries. Readers saw the text with the emotion words hidden, as Jev did.
- **Short texts, big judgments.** Many accounts are a single sentence ("I found out a puppy was available for adoption."). Judging who was responsible from that is guesswork for any reader; the writer knows the backstory.
- **Hidden texts.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
