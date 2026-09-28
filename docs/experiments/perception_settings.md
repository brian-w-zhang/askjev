# perception_settings

family: perception · new questions: 51

## 1. Question
Does Jev read the same probability phrase differently in a weather forecast, a doctor's warning about side effects, and an intelligence report?

For people, the same word shifts with the stakes and the base rate of the event (Weber & Hilton 1990). A model that reads 'likely' identically everywhere is simpler, but not how people talk.

## 2. Sourcing
New questions (sources/perception_words): each of the 17 phrases in three settings, e.g. 'A doctor describes the chance that a new medication causes a side effect with the phrase "likely". What probability does that suggest?', same 21 bins. No human data for the settings.

Sources: `perception_words`

## 3. Collection
51 new questions, each asked with the bins in three shuffled orders (averaged).

## 4. Scoring
Per phrase and setting, Jev's median minus its median for the bare phrase; mean shift per setting with a 90% bootstrap interval over phrases; the phrases that move most.

## 5. Visualization
A dot plot: one row per phrase, the bare reading and the three settings as colored dots.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.292, top verdict `portrait`.

## Compared with
Jev's own reading of the bare phrase (perception_probability)

## Limits
Jev only; the shifts are not compared with people here.

Results: `data/analysis/experiments/perception_settings.json` (private). Code: `scripts/experiments/`.
