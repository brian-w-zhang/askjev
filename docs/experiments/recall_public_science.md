# recall_public_science

family: recall · new questions: 26

## 1. Question
On the science quiz the US has put to adults since 1988 ('antibiotics kill viruses', 'lasers work by focusing sound waves'), does Jev know how many people answer correctly, and how that changed?

Science communication starts from what people already believe. The NSF items are the longest-running record of it, and some moved a lot (antibiotics: 25% right in 1988, 51% in 2016).

## 2. Sourcing
New questions (sources/science_literacy): 9 items from NSF Science & Engineering Indicators 2018, Appendix Table 7-9 (evolution and the big bang left out as religiously contested). Each asked as the survey asked it, and as 'what share of US adults answered correctly' in 2016 and in 1988, in 10-point bins.

Sources: `science_literacy`

## 3. Collection
26 new questions (9 items, 9 shares for 2016, 8 for 1988), each asked as written, for 'most people', and with options in shuffled orders where there are options (averaged).

## 4. Scoring
Jev's own answers vs the key; its estimated share correct (bin midpoints) vs the real share, per item and year; the change it expects from 1988 to 2016 vs the real change.

## 5. Visualization
A dumbbell per item: the real share correct in 1988 and 2016, with Jev's two estimates beside them.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.339, top verdict `portrait`.

## Compared with
US adults: NSF surveys 1988 (n=2,041) and the General Social Survey 2016 (n=1,390)

## Limits
Nine items; 'don't know' counts as incorrect in the real shares. The answer is shown in the share questions.

Results: `data/analysis/experiments/recall_public_science.json` (private). Code: `scripts/experiments/`.
