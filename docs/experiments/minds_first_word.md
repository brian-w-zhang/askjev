# minds_first_word

family: minds · new questions: 400

## 1. Question
Hearing 'bread', most people think 'butter'. Given a word and the most common responses people gave, does Jev pick people's first association, and is it as predictable as they are?

Free association is a window on how concepts are wired. People agree strongly on some cues and not at all on others; a model that always goes for the obvious answer shows a mind with less spread than a crowd's.

## 2. Sourcing
New questions (sources/word_associations): 'What is the first word that comes to mind when you hear the word "<cue>"?' for 400 cues from the USF free association norms (Nelson et al. 2004; about 150 students per cue), options the cue's seven most common responses plus 'some other word'. Cues are sampled evenly across how predictable the top response is.

Sources: `word_associations`

## 3. Collection
400 new questions, each asked as written, for 'most people', and with the options in three shuffled orders (averaged).

## 4. Scoring
Share of cues where Jev's top pick is people's most common response, by quarter of predictability; Jev's probability on people's top response vs its actual share (does Jev exaggerate the obvious?); how often Jev picks 'some other word' vs how often people's answer fell outside the seven.

## 5. Visualization
Binned by how predictable the cue is (people's top share): people's top share, Jev's probability on that response, and how often Jev picks it.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.107, top verdict `portrait`.

## Compared with
University of South Florida students (Nelson et al. 2004)

## Limits
Jev chooses from people's own top seven responses instead of producing a word, so it can't show associations nobody gave; the norms are from US students in the 1970s-1990s.

Results: `data/analysis/experiments/minds_first_word.json` (private). Code: `scripts/experiments/`.
