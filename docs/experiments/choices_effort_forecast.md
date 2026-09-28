# choices_effort_forecast

family: choices · new questions: 15

## 1. Question
Told how hard online workers typed with no bonus, 1 cent and 10 cents per 100 points, can Jev forecast how hard they worked under 15 other incentives (charity, deadlines, losses, lotteries, praise) better than the 208 economists and psychologists who forecast the same study?

DellaVigna and Pope asked experts to predict their experiment before revealing it: the experts were good at the order but underrated how well tiny piece rates work. Predicting what moves people is exactly the kind of advice a model gets asked for.

## 2. Sourcing
New questions (sources/effort_forecasts): the 15 treatments of DellaVigna & Pope 2018 (about 550 MTurk workers each), each with the paper's mean score and the experts' mean forecast (Table 4). Jev gets the three benchmark results the experts got and answers in 50-point bins.

Sources: `effort_forecasts`

## 3. Collection
15 new questions, each asked as written and with the bins in shuffled orders (averaged).

## 4. Scoring
Jev's forecast = the expected score over its bins (bin midpoints). Against the actual means: mean absolute error and rank correlation, the same for the experts' mean forecast; the treatments where each misses most.

## 5. Visualization
A scatter: actual mean score (x) vs forecast (y), Jev and the experts, with the diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.305, top verdict `portrait`.

## Compared with
The actual scores (9,861 MTurk workers) and 208 experts' mean forecasts

## Limits
15 treatments; the experts' number is their average, which is usually better than a single expert (the paper's wisdom-of-crowds finding). Jev may have read the paper.

Results: `data/analysis/experiments/choices_effort_forecast.json` (private). Code: `scripts/experiments/`.
