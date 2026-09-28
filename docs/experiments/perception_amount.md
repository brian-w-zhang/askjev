# perception_amount

family: perception · new questions: 9

## 1. Question
How many does Jev think 'a couple', 'a few', 'several', 'many', 'dozens', 'scores of' and 'hundreds of' are, compared with people?

Amount words are vaguer than probability words, and some have old literal meanings ('a score' is 20) that most people no longer use. Which way a model reads them shows whether it goes by the dictionary or by usage.

## 2. Sourcing
New questions (sources/perception_words): 'What number would you assign to the phrase "<phrase>"?' for 9 of the survey's 10 phrases ('fractions of' is left out: the bins hold counts), with 15 ordered bins from 1 to more than 1,000. Respondents' numbers are put in the same bins.

Sources: `perception_words`

## 3. Collection
9 new questions, asked as written, for 'most people', and in three shuffled orders (averaged).

## 4. Scoring
Per phrase, the bin holding Jev's median vs the bin holding people's median; rank correlation of the medians; the phrases where they differ.

## 5. Visualization
A ridge chart on a log axis: one row per phrase, people's and Jev's distributions over the bins.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.929, top verdict `portrait`.

## Compared with
46 Reddit respondents (zonination 2015)

## Limits
46 people answered the original survey on Reddit's r/samplesize in 2015: a small, online, English-speaking sample. Each person gave one number; Jev gives a probability over the bins, and its median is compared with theirs.

Results: `data/analysis/experiments/perception_amount.json` (private). Code: `scripts/experiments/`.
