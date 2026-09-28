# polls_default_person

family: polls

## 1. Question
Asked how often most people go without food, water, medicine or cash, or how often they use the internet, what does Jev say, and how does that compare with what 50,000 people across 39 African countries report?

Every 'most people' guess rests on an imagined default person. Afrobarometer's lived-poverty questions show whether Jev's default is someone whose basic needs are always met, which is not the case for a large share of the world.

## 2. Sourcing
Existing Afrobarometer Round 9 items (lived poverty, safety, media use), each with the pooled answers of about 50,000 adults in 39 countries. Political and trust items are left out. Small: about 15 items, but each has a very large sample.

Sources: `afrobarometer`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For the deprivation items, the share answering 'never' for Jev's guess of most people vs the Afrobarometer respondents; for media items, the share answering 'never' and 'every day'.

## 5. Visualization
Paired bars, one row per need: share who never went without, respondents vs Jev's 'most people'.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Afrobarometer Round 9 respondents, 39 African countries pooled

## Limits
Jev was asked about 'most people', not about Africans; the comparison shows its default, not its knowledge of Africa. Afrobarometer pools countries without population weights.

Results: `data/analysis/experiments/polls_default_person.json` (private). Code: `scripts/experiments/`.
