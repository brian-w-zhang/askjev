# reading_politeness

family: reading · new questions: 500

## 1. Question
Reading requests Wikipedia editors wrote to each other, does Jev hear the same politeness as crowd raters, and where does its ear differ?

Tone is most of what people react to in a message. The Stanford Politeness Corpus is the standard record of what makes a request sound polite (please, hedges, gratitude) or rude (direct questions, 'you'); a model that writes and rewrites messages all day should hear it like people do.

## 2. Sourcing
New questions (sources/politeness): 'One Wikipedia editor wrote <request> to another editor on their talk page. How polite is it?' on five described levels, for 500 of the 4,353 rated requests, 100 from each fifth of the corpus's politeness score; 5 MTurk raters per request on the study's 1-25 scale, binned into the same five levels.

Sources: `politeness`

## 3. Collection
500 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Rank correlation between Jev's expected level (base and reversed averaged) and the raters' mean score, with a 90% bootstrap interval, next to how well one rater agrees with the other four (the ceiling); Jev's spread and mean against the raters'; the requests it hears most differently.

## 5. Visualization
A scatter: raters' mean score (x) vs Jev's level (y), with the largest disagreements labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.038, top verdict `portrait`.

## Compared with
5 MTurk raters per request (Danescu-Niculescu-Mizil et al. 2013)

## Limits
Raters were US MTurk workers in 2012; requests come from Wikipedia editors' talk pages, a particular register. Jev's level descriptions were written for this project, anchored on the study's ends.

Results: `data/analysis/experiments/reading_politeness.json` (private). Code: `scripts/experiments/`.
