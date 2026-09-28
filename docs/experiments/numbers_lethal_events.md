# numbers_lethal_events

family: numbers · new questions: 81

## 1. Question
How many Americans a year die of botulism, tornadoes, diabetes or stroke? Does Jev show the famous 1978 pattern of overestimating rare, dramatic deaths and underestimating common, quiet ones?

Lichtenstein and colleagues' 1978 chart is the textbook picture of the availability bias: people's estimates are squashed toward the middle, so rare dramatic deaths are overestimated and common diseases underestimated. A model trained on the same news-heavy text might inherit the squash, or read the statistics instead.

## 2. Sourcing
New questions (sources/lethal_events): for each of the study's 41 causes, 'In the United States in the mid-1970s, about how many people died each year from <cause>?', in 13 log bins (about half an order of magnitude each), once with the study's reference (about 50,000 motor-vehicle deaths a year) and once without. Truth: the 1970s vital statistics the study used; people: the study's geometric mean estimates (Pachur's 2024 compilation, OSF u4d7g).

Sources: `lethal_events`

## 3. Collection
81 new questions (41 causes x 2 versions, less motor-vehicle accidents in the version where they are the reference), each asked as written and with the bins in three shuffled orders (averaged).

## 4. Scoring
Jev's estimate = the geometric middle of its median bin. On a log scale: rank correlation of Jev's and people's estimates with the truth; the slope of estimate on truth (1 = unbiased spread, below 1 = squashed toward the middle); the mean log ratio (estimate / truth) for the causes Pachur codes as dramatic vs the rest. Main numbers use the version with the reference, as people had.

## 5. Visualization
The 1978 log-log chart: true deaths (x) vs estimates (y), people's points and Jev's, with the diagonal.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.05, top verdict `portrait`.

## Compared with
US adults in 1978 (geometric means; Lichtenstein et al. 1978) and the 1970s death counts

## Limits
People's side is a published mean per cause, not a distribution. Jev answers about the 1970s knowing (presumably) later statistics too; its errors are compared on the 1970s truth. Bins cap precision at about a factor of three.

Results: `data/analysis/experiments/numbers_lethal_events.json` (private). Code: `scripts/experiments/`.
