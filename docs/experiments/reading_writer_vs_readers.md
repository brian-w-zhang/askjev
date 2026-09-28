# reading_writer_vs_readers

family: reading

## Why ask this
Most emotion datasets label a text by what readers see in it. But what a reader sees and what the writer felt can differ: we project feelings onto other people's stories all the time. A dataset that also records the writer's own answer can tell reading the page apart from reading the person, and a model trained on text might be a very good reader of pages and still miss the person.

## The people and the data
The crowd-enVent corpus (Troiano, Oberländer and Klinger, 2023) asked people on the survey platform Prolific to recall an event from their own life in which they felt a given emotion, describe it, and rate it. That gave 6,600 descriptions from 2,379 writers. A later group of readers then saw 1,200 of the texts, with the emotion words hidden, and guessed what the writer felt, five readers per text.

## What Jev was asked
Each text on its own, with the study's 13 answers:

> Someone wrote *(the story below)* about an event in their own life. Which emotion did the writer feel?
> *"i got the strawberries out of the fridge and they had gone off, exploded and gone furry."*
> *Answers: joy · fear · anger · guilt · pride · shame · trust · relief · boredom · disgust · sadness · surprise · no
> particular emotion*

Each question was also asked with the answers in three shuffled orders, and the answers averaged.

## How we measured it
How often Jev's top answer is the writer's emotion, compared with how often the readers' majority names it and how often a single reader does. Where the readers' majority and the writer disagree, whose side Jev takes. And the hit rate for each emotion the writers felt.

## Caveats
- **"The writer's emotion" was assigned.** Each writer was asked to recall an event in which they felt a given emotion, so the "right answer" is the emotion they were prompted with. A writer asked for a "no particular emotion" story may still have written something that reads as mildly sad or annoyed.
- **Who wrote and who read.** Writers and readers were paid Prolific workers whose first language is English, from the US, UK, Canada, Australia, New Zealand and Ireland. Readers saw each text with the emotion words hidden, as Jev did.
- **Five readers is a small crowd.** A "majority" can be three of five, so the readers' answer per text is noisy. Comparing Jev with one average reader as well as with the majority helps, but neither is a large crowd.
- **Hidden texts.** The filter flags sensitive subjects, so the texts that remain may lean away from the most upsetting events.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
