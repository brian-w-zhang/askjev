# self_closed_questions

family: self

## 1. Question
On 80,000 yes/no questions people actually posted online (Stack Exchange, Quora, Yahoo Answers, chatbot logs), does Jev lean yes or no, and does the way a question starts decide it?

These questions have no answer key, so Jev's lean is a default, not knowledge. If the first word of a question predicts its answer, that's a habit worth knowing before trusting its yes or no.

## 2. Sourcing
Existing closed questions from four public Q&A sources, asked as yes/no. Enough: 79,700 questions; first words with 300+ questions.

Sources: `stackexchange_closed`, `quora_closed`, `yahoo_closed`, `wildchat_closed`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share where P(yes) > 0.5, overall, by source and by the question's first word, with 90% bootstrap intervals; the share within 10 points of 50/50.

## 5. Visualization
Dots per first word (Can, Have, Has, ... Will, Was), yes-share with intervals, line at 50%.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.839, top verdict `portrait`.

## Compared with
Nothing outside the model: no answer key exists for these questions

## Limits
A question's first word travels with its subject (Will... is about the future, Can... often about what's possible), so this shows a pattern, not its cause.

Results: `data/analysis/experiments/self_closed_questions.json` (private). Code: `scripts/experiments/`.
