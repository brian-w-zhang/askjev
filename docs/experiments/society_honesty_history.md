# society_honesty_history

family: society · new questions: 65

## 1. Question
Asked what share of Americans rated each profession's honesty high in Gallup's polls of 2000, 2005, 2010, 2015 and 2020, how close is Jev, and does it know which professions rose or fell?

Trust moves: bankers and stockbrokers lost standing after 2008, nurses have led for decades. Knowing the level is general knowledge; knowing the change means the model has a sense of time for public opinion.

## 2. Sourcing
New questions (sources/gallup_honesty): 'In Gallup's poll of <month year>, what share of Americans rated the honesty and ethical standards of <profession> as "very high" or "high"?', 21 bins (0-100% by 5), for each of the 16 professions and each target year with a poll within a year; the answer is the published trend figure.

Sources: `gallup_honesty`

## 3. Collection
65 new questions, each asked as written and with the bins in three shuffled orders (averaged).

## 4. Scoring
Jev's median share vs the published share: mean absolute error in points, and within 5 points, by year; for professions asked in both 2005 and 2010, and in 2010 and 2020, whether Jev's change has the same sign as the real change, and the rank correlation of the changes.

## 5. Visualization
Slopes per profession: the published share across the years (ink) and Jev's (magenta).

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.546, top verdict `portrait`.

## Compared with
Gallup's published trend figures (US adults, 2000-2020)

## Limits
Gallup asks US adults by phone and online; 'no opinion' answers are dropped. Politics and religion are left out: members of Congress, journalists, police officers, clergy and labor union leaders. The five answers are Gallup's own degree words.

Results: `data/analysis/experiments/society_honesty_history.json` (private). Code: `scripts/experiments/`.
