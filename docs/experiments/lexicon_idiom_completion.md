# lexicon_idiom_completion

family: lexicon · new questions: 200

## 1. Question
Given an idiom without its last word ('Be a bad apple in the ___'), does Jev give the idiom's own word, and does it follow people when they mostly give a different one?

People's completions show which idioms are alive: many people finish 'a bad apple in the...' with 'bunch'. A model trained on text may know the dictionary form better than people, or follow the drift.

## 2. Sourcing
New questions (sources/idiom_norms): 'Finish this idiom with one word: "Be a bad apple in the ___"' for 200 idioms from Bulkes & Tanner 2017 (870 American English idioms, about 100 US adults each), a Choice over the idiom's word, up to five other completions people gave at least twice, and 'another word'; people's completions are the human distribution.

Sources: `idiom_norms`

## 3. Collection
Up to 200 new questions, each asked as written, for 'most people', and with the options shuffled (averaged).

## 4. Scoring
Share where Jev's top pick is the idiom's word, vs the share of people who gave it; on idioms where people's most common answer was a different word, which of the two Jev picks; agreement with people by how familiar the idiom is (terciles of the study's familiarity ratings).

## 5. Visualization
Bars by familiarity tercile: share of people giving the idiom's word vs Jev picking it.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.991, top verdict `portrait`.

## Compared with
US adults (Bulkes & Tanner 2017)

## Limits
Jev picks from the completions people gave rather than writing its own word, which makes the idiom's word easier to find.

Results: `data/analysis/experiments/lexicon_idiom_completion.json` (private). Code: `scripts/experiments/`.
