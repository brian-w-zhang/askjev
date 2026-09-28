# judge_toxicity_line

family: judge

## 1. Question
Asked whether a comment is a personal attack, hate speech, or merely toxic, and whether a prompt to an AI is toxic, does Jev flag more or less than the people who labeled the same text?

Moderation is a common job for a classifier model. Its line matters more than its average accuracy: flagging blunt disagreement silences people, and waving prompts through lets abuse in.

## 2. Sourcing
Existing Noul questions from Wikipedia Talk Labels (personal attacks), Measuring Hate Speech, Civil Comments (each with the share of raters saying yes), and ToxicChat (prompts to a chatbot with a toxic/not label). Enough: about 5,800 items. Items screened as harmful are not shown, so the most extreme text is under-represented in every set.

Sources: `wiki_attacks`, `measuring_hate_speech`, `civil_comments`, `toxicchat`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per dataset, the share Jev flags (probability above one half) vs the share the raters' majority flags, with a 90% bootstrap interval on the difference; for rater sets, how often Jev flags text that no rater flagged.

## 5. Visualization
Paired dots per dataset: raters' flag rate and Jev's, so the direction of each gap is visible at once.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.788, top verdict `portrait`.

## Compared with
The datasets' own raters (majority vote) and ToxicChat's labels

## Limits
Each dataset asks a different question, worded for Jev from the dataset's definition; rater pools differ. The Civil Comments sample is the part with rater shares, which is richer in toxic comments than the platform.

Results: `data/analysis/experiments/judge_toxicity_line.json` (private). Code: `scripts/experiments/`.
