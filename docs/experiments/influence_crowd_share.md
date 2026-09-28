# influence_crowd_share

family: influence · new questions: 300

## 1. Question
Asked for the share of real voters who picked an option (in 5% steps), how close does Jev get, and does it squeeze its guesses toward 50%?

Knowing what most people pick is not the same as knowing how divided they are. Most of Jev's 'most people' answers only reveal the first; asking for the number tests the second.

## 2. Sourcing
New questions (sources/influence_variants): 'People were asked: "<question>" The options were ... What share of them chose "X"?' with 21 bins (0%, 5%, ..., 100%), for 150 Reddit polls (300+ votes) and 150 either.io would-you-rather questions (up to millions of votes), one option each at random.

Sources: `influence_variants`

## 3. Collection
300 new questions, each asked with the bins in shuffled orders (averaged).

## 4. Scoring
Jev's median share vs the real share: mean absolute error, rank correlation, and the slope of Jev's guess on the real share (a slope under 1 means it squeezes toward the middle). Baselines: always guessing an even split, and Jev's own 'most people' probability for the option.

## 5. Visualization
A scatter: real share (x) vs Jev's median guess (y), with the diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.405, top verdict `portrait`.

## Compared with
real vote shares (Reddit polls, either.io)

## Limits
Poll voters are self-selected; the share is theirs, not the public's.

Results: `data/analysis/experiments/influence_crowd_share.json` (private). Code: `scripts/experiments/`.
