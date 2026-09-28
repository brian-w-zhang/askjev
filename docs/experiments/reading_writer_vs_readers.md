# reading_writer_vs_readers

family: reading · new questions: 598

## 1. Question
When someone describes an event from their life, does Jev name the emotion they actually felt, or the one other readers guess, and how often do those differ?

Most emotion datasets label a text by what readers see in it. crowd-enVent also has the writer's own answer, so it can tell reading the page apart from reading the person; a model trained on text might be a very good reader and still miss the writer.

## 2. Sourcing
New questions (sources/crowd_envent): 'Someone wrote <story> about an event in their own life. Which emotion did the writer feel?' with the study's 13 options (anger ... trust, and no particular emotion), for 598 of the 1,200 texts that 5 readers also judged, about 46 per writer emotion; the emotion words are hidden as they were for the readers.

Sources: `crowd_envent`

## 3. Collection
598 new questions, each asked as written, for 'most people', and with the options in three shuffled orders (averaged).

## 4. Scoring
Share where Jev's top emotion is the writer's, and where it is the readers' majority; the same for the readers' majority and for an average single reader against the writer; on texts where the readers' majority and the writer differ, whom Jev sides with; hit rate per writer emotion, 90% bootstrap intervals.

## 5. Visualization
Paired bars per writer emotion: how often the readers' majority names it, and how often Jev does.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.804, top verdict `portrait`.

## Compared with
the writers' own emotion, and 5 readers per text (crowd-enVent, Troiano et al. 2023)

## Limits
Writers were Prolific workers in the UK and US writing about their own lives in 2021; readers saw the text with the emotion words hidden, as Jev does. Five readers per text, so a reader majority can be 3 of 5.

Results: `data/analysis/experiments/reading_writer_vs_readers.json` (private). Code: `scripts/experiments/`.
