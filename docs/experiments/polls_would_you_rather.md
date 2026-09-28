# polls_would_you_rather

family: polls

## 1. Question
On 750 would-you-rather questions voted on by millions (either.io), does Jev pick what most people pick, and where does it split from them hardest?

Would-you-rather is pure preference with huge samples; the biggest disagreements are Jev's quirks in plain view.

## 2. Sourcing
Existing either.io questions with vote shares (typically hundreds of thousands to millions of votes). Enough.

Sources: `wyr`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share where Jev's own choice and its guess of most people match the majority; the questions with the largest gap between Jev's probability and the vote share, among those where voters were clear (60%+).

## 5. Visualization
Scatter of vote share vs Jev's probability for option A, with the five biggest disagreements labeled.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
either.io voters

## Limits
Self-selected voters on a game site.

Results: `data/analysis/experiments/polls_would_you_rather.json` (private). Code: `scripts/experiments/`.
