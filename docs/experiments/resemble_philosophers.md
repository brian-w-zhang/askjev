# resemble_philosophers

family: resemble

## 1. Question
On the big questions of philosophy (free will, God, zombies, the trolley problem), does Jev side with the profession?

The PhilPapers survey records what ~1,800 professional philosophers believe; a model trained on their writing might echo the consensus, or pick sides the field rejects.

## 2. Sourcing
Existing PhilPapers 2020 survey questions (source `philpapers_survey`), each with the target faculty's answer distribution. Enough: 88 shown questions.

Sources: `philpapers_survey`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each question, with 'other' removed on both sides (it pools every unlisted view), whether Jev's top answer is the philosophers' most common named one, and the similarity of the two distributions (1 - Jensen-Shannon distance); the questions where Jev is most confident against the majority are listed.

## 5. Visualization
A strip per question, philosophers' split as a stacked bar with Jev's pick marked; a summary of how often Jev sides with the majority.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
PhilPapers 2020 survey, target faculty (~1,800 professional philosophers)

## Limits
Philosophers could pick 'other' and combinations; Jev picks among the named options.

Results: `data/analysis/experiments/resemble_philosophers.json` (private). Code: `scripts/experiments/`.
