# reasoning_base_rates

family: reasoning · new questions: 6

## 1. Question
Told how common something is and how reliable a witness or test is, does Jev combine the two the way Bayes' rule does, or answer with the witness's reliability, as most people do?

Base-rate neglect is the classic error behind false-positive panics: people told a 90%-accurate test is positive think the chance is 90%, whatever the base rate. The taxi cab problem's median answer was 80% where the right one is 41%.

## 2. Sourcing
New questions (sources/reasoning_traps, family base_rate): the taxi cab problem as published (Tversky & Kahneman 1982) and five isomorphs (buses, factory parts, a clinic test, a screening, and a control where the base rate is 50% so reliability is the answer), answered in 21 bins (0% to 100%).

Sources: `reasoning_traps`

## 3. Collection
6 new questions, each in three shuffled orders (averaged), within the traps batch.

## 4. Scoring
Per item, Jev's median against the Bayesian answer and the lure (the reliability alone); people's published median for the taxi cab.

## 5. Visualization
Dots per item: Jev's median (magenta), the Bayesian answer (tick) and the lure (grey), on 0-100%.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.512, top verdict `portrait`.

## Compared with
Bayes' rule; people's median answer on the taxi cab (80%, Tversky & Kahneman 1982)

## Limits
Six items; bins are 5 points wide, so answers within 5 points of Bayes count as right.

Results: `data/analysis/experiments/reasoning_base_rates.json` (private). Code: `scripts/experiments/`.
