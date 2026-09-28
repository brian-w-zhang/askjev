# resemble_americans

family: resemble

## 1. Question
On General Social Survey items (trust, happiness, work, family), how close is Jev to American adults, year by year?

The GSS is the longest-running survey of American attitudes; the years Jev resembles most hint at which era of opinion it absorbed.

## 2. Sourcing
Existing questions from `gss`, each with real answer distributions per population. Enough for a ranking of populations; the answer shares show where Jev stands out.

Sources: `gss`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per question and population, 1 - Jensen-Shannon distance between Jev's distribution and the population's; mean per population with a 90% bootstrap interval over questions; plus the questions where Jev's top answer is furthest from the pooled populations.

## 5. Visualization
A ranked strip of populations by similarity, and the three questions where Jev differs most.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.338, top verdict `portrait`.

## Compared with
US adults in the General Social Survey, by year

## Limits
Most items are from one or two years, so years are compared on different items; read the overall level, not the year ranking, unless the same item spans years.

Results: `data/analysis/experiments/resemble_americans.json` (private). Code: `scripts/experiments/`.
