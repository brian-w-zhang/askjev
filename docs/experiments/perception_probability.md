# perception_probability

family: perception · new questions: 17

## 1. Question
When someone says 'highly likely', 'we doubt' or 'about even', what probability does Jev read into it, and does it read the phrases the way people do?

Probability words are how forecasts, doctors and intelligence reports talk. A model that reads them differently from people will mistranslate every hedge in both directions.

## 2. Sourcing
New questions (sources/perception_words): the zonination survey's own wording, 'What probability would you assign to the phrase "<phrase>"?', for its 17 phrases, answered as 21 ordered bins (0%, 5%, ..., 100%). Each of the 46 respondents' answers is put in the same bins.

Sources: `perception_words`

## 3. Collection
17 new questions, each asked as written, for 'most people', and with the bins in three shuffled orders (the shuffles are averaged).

## 4. Scoring
Per phrase, the median of Jev's distribution vs the respondents' median; rank correlation of the medians; the median absolute gap in points; the spread (10th to 90th percentile) of each; similarity of the two distributions (1 - Jensen-Shannon distance).

## 5. Visualization
A ridge chart like the zonination original: one row per phrase, people's distribution as a ridge and Jev's as a second ridge, ordered by people's median.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
46 Reddit respondents (zonination 2015)

## Limits
46 people answered the original survey on Reddit's r/samplesize in 2015: a small, online, English-speaking sample. Each person gave one number; Jev gives a probability over the bins, and its median is compared with theirs.

Results: `data/analysis/experiments/perception_probability.json` (private). Code: `scripts/experiments/`.
