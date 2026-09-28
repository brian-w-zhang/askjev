# polls_cuisines

family: polls

## 1. Question
Ranking 40 world cuisines from head-to-heads, how does Jev's own ranking compare with Americans' (FiveThirtyEight's Food World Cup), and how well does it guess theirs?

The gap between Jev's taste and its model of American taste is visible here: it can know that Americans love Italian food and still rank something else first itself.

## 2. Sourcing
Existing FiveThirtyEight/SurveyMonkey Food World Cup pairs (about 790 head-to-heads, each with the share of about 1,000 US adults preferring each cuisine). Enough.

Sources: `food_538`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Bradley-Terry strengths from the head-to-heads, for Jev's answers, Jev's guess of most people and the US respondents; rank correlations between the three; the cuisines Jev ranks furthest from Americans.

## 5. Visualization
Three-column slope chart of cuisine ranks: Jev, Jev's guess of people, Americans.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.386, top verdict `portrait`.

## Compared with
US adults in the 2014 FiveThirtyEight Food World Cup survey

## Limits
Americans in 2014; many respondents hadn't tried every cuisine.

Results: `data/analysis/experiments/polls_cuisines.json` (private). Code: `scripts/experiments/`.
