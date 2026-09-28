# reasoning_anchoring

family: reasoning · new questions: 33

## 1. Question
After a wheel of fortune lands on a low or a high number, do Jev's estimates of unrelated quantities drift toward the wheel, as people's famously do?

Tversky and Kahneman's wheel is the purest anchoring test: everyone knows the number is random, and it still moves people's estimates (median 25 after 10, 45 after 65, for the share of African countries in the UN). A model that reads the whole prompt might be moved just as much, or not at all.

## 2. Sourcing
New questions (sources/anchoring): the 1974 UN question after a wheel at 10 or 65 and with no wheel, and ten authored quantities with known answers (piano keys, Mozart's age at death, the share of the Earth covered by water...), each after a low anchor, a high anchor and none; 21 ordered bins.

Sources: `anchoring`

## 3. Collection
33 new questions, each asked as written and in three shuffled orders of the bins (averaged).

## 4. Scoring
Per quantity, the anchoring index (Jacowitz & Kahneman 1995): the difference between Jev's median after the high and the low anchor, divided by the difference between the anchors (0 = no effect, 1 = estimates follow the anchor fully). People's index on the UN question from the 1974 medians is (45 - 25) / (65 - 10) = 0.36. Also accuracy with no anchor.

## 5. Visualization
Dots per quantity: the no-anchor estimate, the low- and high-anchor estimates as ticks, and the truth.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Tversky & Kahneman 1974 (medians 25 and 45 on the UN question)

## Limits
Only the UN question has human data. Most authored quantities are well known, which should make them hard to move; that is the point of comparing with the no-anchor answer.

Results: `data/analysis/experiments/reasoning_anchoring.json` (private). Code: `scripts/experiments/`.
