# self_shower_thoughts

family: self

## 1. Question
Asked whimsical yes/no questions ('Does 9 feel left out because it's always almost 10?'), does Jev answer the joke or the literal question?

Literal reading is a limit TypeSafe documents (docs/01-jev.md §6, item 1). This measures it on questions whose only sensible answer is playful, and shows where the line falls.

## 2. Sourcing
The shower-thoughts bank written for this project (World > Society): 576 yes/no questions that personify objects or pose silly hypotheticals. Enough for a rate; small for subtopics.

Sources: `g5_w12_shower_thoughts`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share where P(yes) > 0.5; share torn (within 10 points of 50/50); the most and least playful answers.

## 5. Visualization
A histogram of P(yes) across the 576 questions, with a few questions labeled at each end.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.002, top verdict `portrait`.

## Compared with
Nothing outside the model

## Limits
Known limit (literal reading, §6). The questions were written for this project; 'playing along' and 'yes' are the same thing only for questions phrased so a playful answer is yes.

Results: `data/analysis/experiments/self_shower_thoughts.json` (private). Code: `scripts/experiments/`.
