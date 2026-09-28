# perception_round_trip

family: perception · new questions: 21

## 1. Question
Given a probability (0%, 5%, ..., 100%), which phrase does Jev choose for it, and do the phrases survive the round trip from word to number and back?

Reading 'likely' as 70% is half the job; the other half is saying 'likely' when the chance is 70%. A model that reads well but writes with only a few favorite phrases will flatten every forecast it writes.

## 2. Sourcing
New questions (sources/perception_words): 'An event has a <p>% chance of happening. Which phrase describes that chance best?' for each 5% step, with the 17 survey phrases as options. No human data exists for this direction.

Sources: `perception_words`

## 3. Collection
21 new questions, each asked with the phrases in three shuffled orders (averaged).

## 4. Scoring
Per probability, Jev's top phrase. Per phrase, the probabilities where it is Jev's top pick. The round trip: a phrase's median from the probability experiment, rounded to 5%, then the phrase Jev picks for that number; a phrase survives when it comes back.

## 5. Visualization
A strip from 0% to 100% colored by Jev's chosen phrase, with each phrase's forward median marked above.

## 6. Evaluation
Jev's verdict (evaluator v3): **keep**, head-to-head strength 1.144, top verdict `portrait`.

## Compared with
Jev's own forward readings (perception_probability); no human data in this direction

## Limits
Several phrases mean nearly the same thing ('likely', 'probable', 'probably'), so a phrase can lose the round trip to a near-synonym; the result lists which.

Results: `data/analysis/experiments/perception_round_trip.json` (private). Code: `scripts/experiments/`.
