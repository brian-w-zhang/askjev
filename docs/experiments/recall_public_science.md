# recall_public_science

family: recall

## Why ask this
Explaining science starts from what people already believe. Since 1988 the US has put the same short quiz to a national sample of adults ("Antibiotics kill viruses as well as bacteria: true or false?"), and some answers have barely moved while others doubled. A model that explains science to millions of people should know roughly where the public stands, and which misconceptions are common.

## The people and the data
The questions and results come from the US National Science Board's Science and Engineering Indicators 2018 (Appendix Table 7-9): the share of US adults answering each item correctly, from an NSF survey in 1988 (2,041 people) and the General Social Survey in 2016 (1,390 people). Nine items are used; one (the father's gene) wasn't asked in 1988.

## What Jev was asked
Two kinds of questions. First the quiz itself, as the survey asked it:

> True or false: "Lasers work by focusing sound waves."

Then, for each item and year, what share of adults got it right, with the answer shown and ten ranges to choose from:

> In a 2016 national survey, US adults were asked whether this is true or false: "Lasers work by focusing sound
> waves." (The correct answer is: False.) What share of them answered correctly?
> *Answers: 0-10% · 10-20% · ... · 90-100%*

Each question was also asked with the answers in shuffled orders, and the answers averaged.

## How it was measured
Jev's own answers against the key. Then its estimated share (the middle of each range, weighted by its probability) against the real share, item by item and on average, and the change it expects from 1988 to 2016 against the real change.

## Caveats
- **Nine questions.** This is a small quiz. Each item is one estimate, so a single strange item moves the average a lot; read the rows, not just the mean.
- **The orbit item is a follow-up.** The "one year" question was only asked of people who first said the Earth goes around the Sun; everyone else counts as wrong, as the survey reports it. That's part of why its real share (51%) is low, and Jev may not have taken that into account.
- **"Don't know" counts as wrong.** The survey scores "don't know" as incorrect, so the real shares are what people could answer on the spot, not what they'd pick if forced to guess.
- **Two items left out.** The survey's questions on evolution and the big bang were left out because answers to them split along religious lines.
- **Jev sees the answer.** The estimate questions show Jev the correct answer, so they measure its sense of what the public knows, not its own knowledge (which it shows on the quiz itself, 9 out of 9).

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
