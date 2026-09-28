# world_ladder

family: world · new questions: 146

## 1. Question
For each of about 145 countries, does Jev know how people there rate their lives on the Gallup ladder (0 = worst possible life, 10 = best), and where is it most wrong?

The World Happiness Report is one of the most quoted rankings on earth, and it holds surprises (Costa Rica and Mexico near the top, rich East Asia in the middle). A model that simply maps wealth to happiness will get those wrong in a telling way.

## 2. Sourcing
New questions (sources/whr_ladder): one per country, the Gallup ladder question described in full, asking the country's 2022-2024 average, answered in half-step bins (below 3.0, 3.0-3.5, ..., 8.0 or above). Truth: the World Happiness Report 2025 averages via Our World in Data (CC BY 4.0). GDP per head and region are used in the analysis only.

Sources: `whr_ladder`

## 3. Collection
About 146 new questions, each asked as written and with the bins in three shuffled orders (averaged).

## 4. Scoring
Jev's expected score (bin midpoints) against the published average: rank correlation, mean absolute error, exact-bin rate; the countries it most over- and underrates; whether its errors follow wealth (rank correlation of the error with GDP per head) and region.

## 5. Visualization
A scatter: published average (x) vs Jev's estimate (y), with the diagonal and the biggest misses labeled.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
World Happiness Report 2025 (Gallup World Poll, 2022-2024)

## Limits
Country averages carry sampling error of about 0.1; bins are half a step wide. The question names the years, and Jev may know older reports better than this one.

Results: `data/analysis/experiments/world_ladder.json` (private). Code: `scripts/experiments/`.
